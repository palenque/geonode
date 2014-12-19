import logging
import os
import uuid
import subprocess
from datetime import datetime

from django.db import models
from django.db.models import signals
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.contrib.contenttypes import generic
from django.contrib.staticfiles import finders
from django.utils.translation import ugettext_lazy as _

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase, Thumbnail, Link
from geonode.base.models import resourcebase_post_save, resourcebase_pre_save
from geonode.maps.signals import map_changed_signal
from geonode.maps.models import Map

import eav
from eav.models import Attribute as EAVAttribute

IMGTYPES = ['jpg', 'jpeg', 'tif', 'tiff', 'png', 'gif']

logger = logging.getLogger(__name__)


class TabularType(models.Model):
    'Layer type'

    name = models.CharField(_('name'), max_length=255, unique=True)
    label = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(
        _('description'), max_length=255, blank=True, null=True
    )


    def __unicode__(self):
        return self.label or self.name

class MetadataType(models.Model):

    tabular_type = models.ForeignKey(
        TabularType, blank=False, null=False, unique=False,
    )

    attribute = models.ForeignKey(
        EAVAttribute, blank=False, null=False,
        related_name='tabular_metadata_type_attribute',
    )


class Attribute(models.Model):

    """
        Auxiliary model for storing Tabular attributes.

       This helps reduce the need for runtime lookups
       to other servers, and lets users customize attribute titles,
       sort order, and visibility.
    """
    
    tabular = models.ForeignKey(
        'Tabular',
        blank=False,
        null=False,
        unique=False,
        related_name='tabular_attribute_set')
    attribute = models.CharField(
        _('attribute name'),
        help_text=_('name of attribute as stored in shapefile/spatial database'),
        max_length=255,
        blank=False,
        null=True,
        unique=False)
    description = models.CharField(
        _('attribute description'),
        help_text=_('description of attribute to be used in metadata'),
        max_length=255,
        blank=True,
        null=True)
    attribute_label = models.CharField(
        _('attribute label'),
        help_text=_('title of attribute as displayed in GeoNode'),
        max_length=255,
        blank=False,
        null=True,
        unique=False)
    visible = models.BooleanField(
        _('visible?'),
        help_text=_('specifies if the attribute should be displayed in identify results'),
        default=True)
    display_order = models.IntegerField(
        _('display order'),
        help_text=_('specifies the order in which attribute should be displayed in identify results'),
        default=1)
    magnitude = models.CharField(
        _('magnitude'),
        #choices=MAGNITUDES,
        help_text=_('unit'),
        max_length=255,
        blank=True,
        null=True,
        unique=False)
    attribute_type = models.CharField(
        _('attribute type'),
        help_text=_('the data type of the attribute (integer, string, geometry, etc)'),
        max_length=50,
        blank=False,
        null=False,
        default='xsd:string',
        unique=False)


    # statistical derivations
    count = models.IntegerField(
        _('count'),
        help_text=_('count value for this field'),
        default=1)
    min = models.CharField(
        _('min'),
        help_text=_('minimum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    max = models.CharField(
        _('max'),
        help_text=_('maximum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    average = models.CharField(
        _('average'),
        help_text=_('average value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    median = models.CharField(
        _('median'),
        help_text=_('median value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    stddev = models.CharField(
        _('standard deviation'),
        help_text=_('standard deviation for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    sum = models.CharField(
        _('sum'),
        help_text=_('sum value for this field'),
        max_length=255,
        blank=False,
        null=True,
        unique=False,
        default='NA')
    unique_values = models.TextField(
        _('unique values for this field'),
        null=True,
        blank=True,
        default='NA')
    last_stats_updated = models.DateTimeField(
        _('last modified'),
        default=datetime.now,
        help_text=_('date when attribute statistics were last updated'))  # passing the method itself, not


    def __unicode__(self):
        if self.attribute_label:
            return self.attribute_label
        return self.attribute

    def unique_values_as_list(self):
        return self.unique_values.split(',')


class Tabular(ResourceBase):

    """
    A document is any kind of information that can be attached to a map such as pdf, images, videos, xls...
    """

    tabular_type = models.ForeignKey(TabularType, null=True, blank=True)
    delimiter = models.CharField(max_length=128, blank=True, null=True)
    quote = models.CharField(max_length=128, blank=True, null=True)
    charset = models.CharField(max_length=128, blank=True, null=True)

    # Relation to the resource model
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    resource = generic.GenericForeignKey('content_type', 'object_id')

    doc_file = models.FileField(upload_to='tabular',
                                null=True,
                                blank=True,
                                verbose_name=_('File'))

    extension = models.CharField(max_length=128, blank=True, null=True)

    doc_type = models.CharField(max_length=128, blank=True, null=True)

    doc_url = models.URLField(
        blank=True,
        null=True,
        help_text=_('The URL of the document if it is external.'),
        verbose_name=_('URL'))

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tabular_detail', args=(self.id,))

    @property
    def name_long(self):
        if not self.title:
            return str(self.id)
        else:
            return '%s (%s)' % (self.title, self.id)

    def _render_thumbnail(self):
        from cStringIO import StringIO

        size = 200, 150

        try:
            from PIL import Image, ImageOps
        except ImportError, e:
            logger.error(
                '%s: Pillow not installed, cannot generate thumbnails.' %
                e)
            return None

        try:
            # if wand is installed, than use it for pdf thumbnailing
            from wand import image
        except:
            wand_available = False
        else:
            wand_available = True

        if wand_available and self.extension and self.extension.lower(
        ) == 'pdf' and self.doc_file:
            logger.debug(
                'Generating a thumbnail for document: {0}'.format(
                    self.title))
            with image.Image(filename=self.doc_file.path) as img:
                img.sample(*size)
                return img.make_blob('png')
        elif self.extension and self.extension.lower() in IMGTYPES and self.doc_file:

            img = Image.open(self.doc_file.path)
            img = ImageOps.fit(img, size, Image.ANTIALIAS)
        else:
            filename = finders.find('documents/{0}-placeholder.png'.format(self.extension), False) or \
                finders.find('documents/generic-placeholder.png', False)

            if not filename:
                return None

            img = Image.open(filename)

        imgfile = StringIO()
        img.save(imgfile, format='PNG')
        return imgfile.getvalue()

    @property
    def class_name(self):
        return self.__class__.__name__

    class Meta(ResourceBase.Meta):
        pass


def get_related_documents(resource):
    if isinstance(resource, Layer) or isinstance(resource, Map):
        ct = ContentType.objects.get_for_model(resource)
        return Tabular.objects.filter(content_type=ct, object_id=resource.pk)
    else:
        return None


def pre_save_document(instance, sender, **kwargs):
    base_name, extension, doc_type = None, None, None

    if instance.doc_file:
        base_name, extension = os.path.splitext(instance.doc_file.name)
        instance.extension = extension[1:]
        doc_type_map = settings.DOCUMENT_TYPE_MAP
        if doc_type_map is None:
            doc_type = 'other'
        else:
            if instance.extension in doc_type_map:
                doc_type = doc_type_map[''+instance.extension]
            else:
                doc_type = 'other'
        instance.doc_type = doc_type

    elif instance.doc_url:
        if len(instance.doc_url) > 4 and instance.doc_url[-4] == '.':
            instance.extension = instance.doc_url[-3:]

    if not instance.uuid:
        instance.uuid = str(uuid.uuid1())
    instance.csw_type = 'tabular'

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'

    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    if instance.resource:
        instance.csw_wkt_geometry = instance.resource.geographic_bounding_box.split(
            ';')[-1]
        instance.bbox_x0 = instance.resource.bbox_x0
        instance.bbox_x1 = instance.resource.bbox_x1
        instance.bbox_y0 = instance.resource.bbox_y0
        instance.bbox_y1 = instance.resource.bbox_y1
    else:
        instance.bbox_x0 = -180
        instance.bbox_x1 = 180
        instance.bbox_y0 = -90
        instance.bbox_y1 = 90


def create_thumbnail(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.has_thumbnail():
        instance.thumbnail_set.get().thumb_file.delete()
    else:
        instance.thumbnail_set.add(Thumbnail())

    image = instance._render_thumbnail()

    instance.thumbnail_set.get().thumb_file.save(
        'doc-%s-thumb.png' %
        instance.id,
        ContentFile(image))
    instance.thumbnail_set.get().thumb_spec = 'Rendered'
    instance.thumbnail_set.get().save()
    Link.objects.get_or_create(
        resource=instance.get_self_resource(),
        url=instance.thumbnail_set.get().thumb_file.url,
        defaults=dict(
            name=('Thumbnail'),
            extension='png',
            mime='image/png',
            link_type='image',))


def update_documents_extent(sender, **kwargs):
    model = 'map' if isinstance(sender, Map) else 'layer'
    ctype = ContentType.objects.get(model=model)
    for document in Tabular.objects.filter(content_type=ctype, object_id=sender.id):
        document.save()


def create_table(sender, instance, created, **kwargs):
    if not created:
        return

    from csvkit import table
    from csvkit.utilities.csvsql import CSVSQL

    # TODO: mejorar manejo de errores: validar si existe la tabla, nombre de tabla
    # separador, quote, errores de importacion, etc.
    
    table_name = 'tabular_%d' % instance.id
    
    csv_table = table.Table.from_csv(
        file(instance.doc_file.path),
        name=table_name,
        snifflimit=None,
        blanks_as_nulls=True,
        infer_types=True,
        no_header_row=False,
    )

    # save attributes
    for i, header in enumerate(csv_table.headers()):
        Attribute(
            tabular=instance,
            attribute=header,
            attribute_label=header,
            display_order=i+1,
            attribute_type=str(csv_table[i].type)
        ).save()

    # Out[3]: Namespace(blanks=False, connection_string=None, db_schema=None, delimiter=None, dialect=None, doublequote=False, encoding='utf-8', escapechar=None, input_paths=['-'], insert=False, maxfieldsize=None, no_constraints=False, no_create=False, no_header_row=False, no_inference=False, query=None, quotechar=None, quoting=None, skipinitialspace=False, snifflimit=None, table_names=None, tabs=False, verbose=False, zero_based=False)

    # csvsql = CSVSQL()
    # csvsql.args.blanks = True
    # csvsql.args.insert = True
    # csvsql.main()

    subprocess.call([
        'csvsql', 
        '--db', 
        'postgresql://%s:%s@%s:%s/%s' % (
            settings.DATABASES['datastore']['USER'],
            settings.DATABASES['datastore']['PASSWORD'],
            settings.DATABASES['datastore']['HOST'],
            settings.DATABASES['datastore']['PORT'],
            settings.DATABASES['datastore']['NAME'],
        ),
        '--table',
        table_name,
        '--insert', 
        instance.doc_file.path
    ])


signals.pre_save.connect(pre_save_document, sender=Tabular)
signals.post_save.connect(create_thumbnail, sender=Tabular)
signals.post_save.connect(create_table, sender=Tabular)
signals.pre_save.connect(resourcebase_pre_save, sender=Tabular)
signals.post_save.connect(resourcebase_post_save, sender=Tabular)
map_changed_signal.connect(update_documents_extent)


from eav.registry import EavConfig
class EavConfigClass(EavConfig):
    manager_attr = 'eav_objects'
    object_type = 'tabular_type'
    attribute_relation='tabular_metadata_type_attribute'

eav.register(Tabular, EavConfigClass)