# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import uuid
import logging

from datetime import datetime

from django.db import transaction
from django.db import models, connections
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from geonode.base.models import TopicCategory
from geonode.base.models import ResourceBase, ResourceBaseManager
from geonode.base.models import resourcebase_post_save, resourcebase_pre_save
from geonode.people.utils import get_valid_user
from geonode.layers.units import *
from geonode.security.models import PermissionLevelMixin

from guardian.shortcuts import assign_perm, remove_perm, get_anonymous_user, get_groups_with_perms
import eav
from agon_ratings.models import OverallRating
from eav.models import Attribute as EAVAttribute


logger = logging.getLogger("geonode.layers.models")

shp_exts = ['.shp', ]
csv_exts = ['.csv']
kml_exts = ['.kml']
vec_exts = shp_exts + csv_exts + kml_exts

cov_exts = ['.tif', '.tiff', '.geotiff', '.geotif']



class LayerType(models.Model):
    'Layer type'

    name = models.CharField(_('name'), max_length=255, unique=True)
    label = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(
        _('description'), max_length=255, blank=True, null=True
    )
    fill_metadata = models.BooleanField(
        blank=True, default=False,
        help_text=_('defines if metadata must be filled out after uploading')
    )
    is_default = models.BooleanField(
        blank=True, default=False,
        help_text=_('defines if it is the default layer type')
    )
    show_category = models.BooleanField(
        blank=True, default=True,
        help_text=_('show category in metadata')
    )
    calculated_title = models.CharField(max_length=255, blank=True, null=True)
    calculated_abstract = models.CharField(max_length = 1024, blank=True, null=True)
    default_style = models.ForeignKey('Style', null=True, blank=True)


    def _set_default_style(self, layer):
        if self.default_style is None: return

        # Save to GeoServer
        cat = gs_catalog
        gs_layer = cat.get_layer(layer.name)
        gs_layer.default_style = self.default_style.name
        styles = [self.default_style.name]
        gs_layer.styles = styles
        cat.save(gs_layer)

        # Save to Django
        layer = set_styles(layer, cat)
        #layer.save()

    def update_attributes(self, layer):
        'Updates table fields and attributes to mach layer type attributes.'

        if layer.layer_type.is_default:
            return

        if layer.is_vector():
            with transaction.atomic(using="datastore"):
                self._validate_required_attributes(layer)
                self._rename_fields(layer)
                self._normalize_units(layer)
                self._precalculate_fields(layer)
                self._precalculate_metadata_fields(layer)
        else:
            self._validate_required_attributes(layer)

        self._set_default_style(layer)


    def _validate_required_attributes(self, layer):

        for attr_type in self.required_attributes():
            if not layer.attribute_set.filter(field=str(attr_type.id)):
                raise Exception('Attribute Type "%s" required' % attr_type.name)

    def _normalize_units(self, layer):
        'Converts units.'

        cursor = connections['datastore'].cursor()

        for attr in layer.attribute_set.exclude(attribute='the_geom'):
            
            if not attr.field:
                continue
            
            attr_type = AttributeType.objects.get(id=attr.field)
            
            if attr_type.is_precalculated:
                continue
            
            try:
                cursor.execute(
                    '''UPDATE %s SET "%s" = "%s" * %s;''' % (
                        layer.name, 
                        attr.attribute, 
                        attr.attribute,
                        str(units(attr.magnitude).to(attr_type.magnitude).magnitude)
                    )
                )
            except Exception as e:
                logging.exception('Error normalizing magnitudes')
                raise Exception(
                    'Error normalizing magnitude for field %s to %s. ' % (
                        attr.attribute, 
                        str(units(attr.magnitude).to(attr_type.magnitude).magnitude)
                    ) + \
                    'Please check magnitudes.'
                )

            attr.magnitude = attr_type.magnitude
            attr.save()

    def _precalculate_fields(self, layer):
        'Precalculates fields.'

        cursor = connections['datastore'].cursor()

        for attr in self.attribute_type_set.filter(is_precalculated=True):
            try:
                cursor.execute(
                    '''UPDATE %s SET "%s" = %s;''' % (
                        layer.name, attr.name, attr.sql_expression
                    )
                )
            except Exception as e:
                logging.exception('Error trying to precalculate field "%s".' % attr.name)
                raise Exception(
                    'Error trying to precalculate field "%s" (%s).' % (
                        attr.name, attr.sql_expression
                    ) + \
                    'Please check field types, associations and values.'
                )

    def _precalculate_metadata_fields(self, layer):
        cursor = connections['datastore'].cursor()

        for attr in self.metadatatype_set.filter(is_precalculated=True):
            cursor.execute(
                '''SELECT %s FROM %s''' 
                    % (attr.sql_expression,layer.name)
            )      
            setattr(layer.eav,attr.attribute.slug, cursor.fetchone()[0])

    def _rename_fields(self, layer):
        'Renames fiels in the layer table.'
        cursor = connections['datastore'].cursor()

        # borra campos y atributos no conservados
        for attr in layer.attribute_set.exclude(attribute='the_geom'):
            if not attr.preserved:
                try:
                    cursor.execute(
                        'ALTER TABLE %s DROP COLUMN "%s";' % (
                            layer.name, attr.attribute
                        )
                    )
                except Exception as e:
                    logging.exception('Error droping field "%s".' % attr.attribute)
                    raise Exception(
                        'Error droping field "%s". ' % attr.attribute + \
                        'Please check field associations.'
                    )
                attr.delete()

        # renombra demas atributos y campos
        for attr in layer.attribute_set.exclude(attribute='the_geom'):
            
            if not attr.field:
                continue
            
            attr_type = AttributeType.objects.get(id=attr.field)
            if not attr_type.is_precalculated and attr.attribute != attr_type.name:
                try:
                    cursor.execute(
                        'ALTER TABLE %s RENAME COLUMN "%s" to "%s";' % (
                            layer.name, attr.attribute, attr_type.name
                        )
                    )
                except Exception as e:
                    logging.exception(
                        'Error renaming field "%s" to "%s"' % (attr.attribute, attr_type.name)
                    )
                    raise Exception(
                        'Error renaming field "%s" to "%s". ' % (attr.attribute, attr_type.name) + \
                        'Please check field associations.'
                    )
                attr.attribute = attr_type.name
                attr.visible = True
                attr.save()

        # crea atributos y campos para campos precalculados
        for attr_type in self.attribute_type_set.filter(is_precalculated=True):
            try:
                cursor.execute(
                    '''ALTER TABLE %s ADD "%s" %s;''' % (
                        layer.name, attr_type.name, attr_type.attribute_type
                    )
                )
            except Exception as e:
                logging.exception('Error creating field "%s".' % attr_type.name)
                raise Exception(
                    'Error renaming field "%s". ' % attr_type.name + \
                    'Please check field associations.'
                )

            Attribute(
                layer=layer, 
                attribute=attr_type.name,
                attribute_label=attr_type.name,
                field=str(attr_type.id),
                attribute_type=attr_type.attribute_type,
                magnitude=attr_type.magnitude
            ).save()

        # convierte unidades de los campos precalculados
        for attr in layer.attribute_set.exclude(attribute='the_geom'):

            if not attr.field:
                continue

            attr_type = AttributeType.objects.get(id=attr.field)

            if attr_type.is_precalculated:
                try:
                    cursor.execute(
                        '''UPDATE %s SET "%s" = "%s" * %s;''' % (
                            layer.name, 
                            attr.attribute, 
                            attr.attribute,
                            str(units(attr.magnitude).to(attr_type.sql_magnitude).magnitude)
                        )
                    )
                except Exception as e:
                    logging.exception(
                        'Error converting magnitude for field "%s" to "%s".' % (
                            attr.attribute,
                            str(units(attr.magnitude).to(attr_type.sql_magnitude).magnitude)
                        )
                    )
                    raise Exception(
                        'Error converting magnitude for field "%s" to "%s". ' % (
                            attr.attribute,
                            str(units(attr.magnitude).to(attr_type.sql_magnitude).magnitude)
                        ) + 'Please check magnitudes.'
                    )


    def required_attributes(self):
        return self.attribute_type_set.filter(required=True).exclude(is_precalculated=True)

    def __unicode__(self):
        return self.label or self.name

# Fix para migracion de south 
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^eav\.fields\.EavDatatypeField"])
add_introspection_rules([], ["^eav\.fields\.EavSlugField"])

class MetadataType(models.Model):

    layer_type = models.ForeignKey(
        LayerType, blank=False, null=False, unique=False
    )

    attribute = models.ForeignKey(
        EAVAttribute, blank=False, null=False,
        related_name='layer_metadata_type_attribute',
    )

    is_precalculated = models.BooleanField(
        blank=True, default=False,
        help_text=_('defines if this will be a precalculated with the sql field')
    )

    sql_expression = models.CharField(max_length=255, blank=True, null=True)
    sql_magnitude = models.CharField(max_length=255, blank=True, null=True)


class AttributeType(models.Model):
    'Attributes related to a layer type'
    
    layer_type = models.ForeignKey(
        LayerType, blank=False, null=False, unique=False, related_name='attribute_type_set'
    )
    
    name = models.CharField(
        _('name'), help_text=_('name of attribute as it will be stored in the database'),
        max_length=255, blank=False, null=True, unique=False
    )    

    label = models.CharField(
        _('label'), help_text=_('label to show'),
        max_length=255, blank=False, null=True
    )    

    description = models.CharField(max_length=255, blank=True, null=True)    

    required = models.BooleanField(
        blank=True, default=False,
        help_text=_('defines if the attribute is required to save the whole attribute set')
    )

    is_precalculated = models.BooleanField(
        blank=True, default=False,
        help_text=_('defines if this will be a precalculated with the sql field')
    )

    sql_expression = models.CharField(max_length=255, blank=True, null=True)
    sql_magnitude = models.CharField(max_length=255, blank=True, null=True)

    attribute_type = models.CharField(
        _('attribute type'), help_text=_('the data type of the attribute (integer, string, geometry, etc)'),
        max_length=50, blank=True, null=False, default='xsd:string', unique=False
    )
    
    magnitude = models.CharField(
        _('magnitude'), help_text=_('unit'), max_length=255,
        blank=True, null=True, unique=False
    )


class Style(models.Model):

    """Model for storing styles.
    """
    name = models.CharField(_('style name'), max_length=255, unique=True)
    sld_title = models.CharField(max_length=255, null=True, blank=True)
    sld_body = models.TextField(_('sld text'), null=True, blank=True)
    sld_version = models.CharField(
        _('sld version'),
        max_length=12,
        null=True,
        blank=True)
    sld_url = models.CharField(_('sld url'), null=True, max_length=1000)
    workspace = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "%s" % self.name.encode('utf-8')


class LayerManager(ResourceBaseManager):

    def __init__(self):
        models.Manager.__init__(self)


class Layer(ResourceBase):

    """
    Layer (inherits ResourceBase fields)
    """

    # internal fields
    objects = LayerManager()
    workspace = models.CharField(max_length=128)
    store = models.CharField(max_length=128)
    storeType = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    typename = models.CharField(max_length=128, null=True, blank=True)
    layer_type = models.ForeignKey(LayerType, null=True, blank=True)
    metadata_edited = models.BooleanField(blank=True, default=False)

    concave_hull = models.TextField(null=True, blank=True)

    default_style = models.ForeignKey(
        Style,
        related_name='layer_default_style',
        null=True,
        blank=True)
    styles = models.ManyToManyField(Style, related_name='layer_styles')

    charset = models.CharField(max_length=255, default='UTF-8')

    upload_session = models.ForeignKey('UploadSession', blank=True, null=True)

    service = models.ForeignKey(
        'services.Service',
        null=True,
        blank=True,
        related_name='layer_set')

    def update_attributes(self):
        return self.layer_type.update_attributes(self)

    def is_vector(self):
        return self.storeType == 'dataStore'

    @property
    def display_type(self):
        return ({
            "dataStore": "Vector Data",
            "coverageStore": "Raster Data",
        }).get(self.storeType, "Data")

    @property
    def data_model(self):
        if hasattr(self, 'modeldescription_set'):
            lmd = self.modeldescription_set.all()
            if lmd.exists():
                return lmd.get().get_django_model()

        return None

    @property
    def data_objects(self):
        if self.data_model is not None:
            return self.data_model.objects.using('datastore')

        return None

    @property
    def service_type(self):
        if self.storeType == 'coverageStore':
            return "WCS"
        if self.storeType == 'dataStore':
            return "WFS"

    @property
    def ows_url(self):
        if self.storeType == "remoteStore":
            return self.service.base_url
        else:
            return settings.OGC_SERVER['default']['PUBLIC_LOCATION'] + "wms"

    @property
    def ptype(self):
        if self.storeType == "remoteStore":
            return self.service.ptype
        else:
            return "gxp_wmscsource"

    @property
    def service_typename(self):
        if self.storeType == "remoteStore":
            return "%s:%s" % (self.service.name, self.typename)
        else:
            return self.typename

    def get_base_file(self):
        """Get the shp or geotiff file for this layer.
        """
        # If there was no upload_session return None
        if self.upload_session is None:
            return None

        base_exts = [x.replace('.', '') for x in cov_exts + vec_exts]
        base_files = self.upload_session.layerfile_set.filter(
            name__in=base_exts)
        base_files_count = base_files.count()

        # If there are no files in the upload_session return None
        if base_files_count == 0:
            return None

        msg = 'There should only be one main file (.shp or .geotiff), found %s' % base_files_count
        assert base_files_count == 1, msg

        return base_files.get()

    def get_absolute_url(self):
        return reverse('layer_detail', args=(self.service_typename,))

    def attribute_config(self):
        # Get custom attribute sort order and labels if any
        cfg = {}
        visible_attributes = self.attribute_set.visible()
        if (visible_attributes.count() > 0):
            cfg["getFeatureInfo"] = {
                "fields": [l.attribute for l in visible_attributes],
                "propertyNames": dict([(l.attribute, l.attribute_label) for l in visible_attributes])
            }
        return cfg

    def __str__(self):
        if self.typename is not None:
            return "%s Layer" % self.service_typename.encode('utf-8')
        elif self.name is not None:
            return "%s Layer" % self.name
        else:
            return "Unamed Layer"

    class Meta:
        # custom permissions,
        # change and delete are standard in django
        permissions = (
            ('view_layer',
             'Can view'),
            ('change_layer_permissions',
             "Can change permissions"),
        )

    # Permission Level Constants
    # LEVEL_NONE inherited
    LEVEL_READ = 'layer_readonly'
    LEVEL_WRITE = 'layer_readwrite'
    LEVEL_ADMIN = 'layer_admin'

    def maps(self):
        from geonode.maps.models import MapLayer
        return MapLayer.objects.filter(name=self.typename)

    @property
    def class_name(self):
        return self.__class__.__name__

    def update_concave_hull(self):
        if self.is_vector():
            cursor = connections['datastore'].cursor()
            cursor.execute(
                '''SELECT st_asgeojson(st_concavehull(st_collect(the_geom),0.99)) 
                   FROM %s;''' % self.name)
            self.concave_hull = cursor.fetchone()[0]
            self.save()


class Layer_Styles(models.Model):
    layer = models.ForeignKey(Layer)
    style = models.ForeignKey(Style)


class UploadSession(models.Model):

    """Helper class to keep track of uploads.
    """
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)

    def successful(self):
        return self.processed and self.errors is None


class LayerFile(models.Model):

    """Helper class to store original files.
    """
    upload_session = models.ForeignKey(UploadSession)
    name = models.CharField(max_length=255)
    base = models.BooleanField(default=False)
    file = models.FileField(upload_to='layers', max_length=255)


class AttributeManager(models.Manager):

    """Helper class to access filtered attributes
    """

    def visible(self):
        return self.get_query_set().filter(
            visible=True).order_by('display_order')


class Attribute(models.Model, PermissionLevelMixin):

    """
        Auxiliary model for storing layer attributes.

       This helps reduce the need for runtime lookups
       to other servers, and lets users customize attribute titles,
       sort order, and visibility.
    """
    
    layer = models.ForeignKey(
        Layer,
        blank=False,
        null=False,
        unique=False,
        related_name='attribute_set')
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
    attribute_type = models.CharField(
        _('attribute type'),
        help_text=_('the data type of the attribute (integer, string, geometry, etc)'),
        max_length=50,
        blank=False,
        null=False,
        default='xsd:string',
        unique=False)
    visible = models.BooleanField(
        _('visible?'),
        help_text=_('specifies if the attribute should be displayed in identify results'),
        default=True)
    preserved = models.BooleanField(
        _('Preserve'),
        help_text=_('specifies if the attribute should be kept after mapping'),
        default=True)    
    display_order = models.IntegerField(
        _('display order'),
        help_text=_('specifies the order in which attribute should be displayed in identify results'),
        default=1)
    field = models.CharField(
        _('field mapping'),
        help_text=_('monitor field'),
        max_length=255,
        blank=True,
        null=True,
        unique=False)

    @property
    def attributetype(self):
        if not self.field:
            return None
        else:
            return AttributeType.objects.get(id=self.field)

    magnitude = models.CharField(
        _('magnitude'),
        help_text=_('unit'),
        max_length=255,
        blank=True,
        null=True,
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

    objects = AttributeManager()

    def __str__(self):
        if self.field:
            label = AttributeType.objects.get(id=self.field).label
        elif self.attribute_label:
            label = self.attribute_label
        else:
            label = self.attribute
        return "%s" % label.encode("utf-8")

    def unique_values_as_list(self):
        return self.unique_values.split(',')


def pre_save_layer(instance, sender, **kwargs):
    if kwargs.get('raw', False):
        instance.owner = instance.resourcebase_ptr.owner
        instance.uuid = instance.resourcebase_ptr.uuid
        instance.bbox_x0 = instance.resourcebase_ptr.bbox_x0
        instance.bbox_x1 = instance.resourcebase_ptr.bbox_x1
        instance.bbox_y0 = instance.resourcebase_ptr.bbox_y0
        instance.bbox_y1 = instance.resourcebase_ptr.bbox_y1

    if instance.abstract == '' or instance.abstract is None:
        instance.abstract = 'No abstract provided'
    if instance.title == '' or instance.title is None:
        instance.title = instance.name

    # Set a default user for accountstream to work correctly.
    if instance.owner is None:
        instance.owner = get_valid_user()

    if not instance.creator:
        instance.creator = instance.owner

    if instance.uuid == '':
        instance.uuid = str(uuid.uuid1())

    if instance.typename is None:
        # Set a sensible default for the typename
        instance.typename = 'geonode:%s' % instance.name

    base_file = instance.get_base_file()

    if base_file is not None:
        extension = '.%s' % base_file.name
        if extension in vec_exts:
            instance.storeType = 'dataStore'
        elif extension in cov_exts:
            instance.storeType = 'coverageStore'

    # Set sane defaults for None in bbox fields.
    if instance.bbox_x0 is None:
        instance.bbox_x0 = -180

    if instance.bbox_x1 is None:
        instance.bbox_x1 = 180

    if instance.bbox_y0 is None:
        instance.bbox_y0 = -90

    if instance.bbox_y1 is None:
        instance.bbox_y1 = 90

    bbox = [
        instance.bbox_x0,
        instance.bbox_x1,
        instance.bbox_y0,
        instance.bbox_y1]

    instance.set_bounds_from_bbox(bbox)


def pre_delete_layer(instance, sender, **kwargs):
    """
    Remove any associated style to the layer, if it is not used by other layers.
    Default style will be deleted in post_delete_layer
    """
    if instance.service:
        return
    logger.debug(
        "Going to delete the styles associated for [%s]",
        instance.typename.encode('utf-8'))
    ct = ContentType.objects.get_for_model(instance)
    OverallRating.objects.filter(
        content_type=ct,
        object_id=instance.id).delete()
    default_style = instance.default_style
    for style in instance.styles.all():
        if style.layer_styles.all().count() == 1:
            if style != default_style:
                style.delete()


def post_delete_layer(instance, sender, **kwargs):
    """
    Removed the layer from any associated map, if any.
    Remove the layer default style.
    """
    from geonode.maps.models import MapLayer
    logger.debug(
        "Going to delete associated maplayers for [%s]",
        instance.typename.encode('utf-8'))
    MapLayer.objects.filter(
        name=instance.typename,
        ows_url=instance.ows_url).delete()

    if instance.service:
        return
    logger.debug(
        "Going to delete the default style for [%s]",
        instance.typename.encode('utf-8'))

    if instance.default_style and Layer.objects.filter(
            default_style__id=instance.default_style.id).count() == 0:
        instance.default_style.delete()


def post_save_layer_type(instance, *args, **kwargs):
    'Updates or creates a category with the layer type name.'

    if instance.is_default:
        return

    try:
        category = TopicCategory.objects.get(identifier=instance.name)
        category.description = category.gn_description = instance.description
    except TopicCategory.DoesNotExist:
        category = TopicCategory(
            identifier=instance.name,
            description=instance.description,
            gn_description=instance.description
        )
    category.save()


def share(instance, created=False, update_fields=None, **kwargs):
    "Shares the tagged object with the app alter-ego"
    owner = instance.owner
    resource = instance.resourcebase_ptr

    for app_member in owner.appmember_set.all():
        app = app_member.app
        alter_ego = app.get_alter_ego()

        if not alter_ego:
            continue 

        if created:
            if instance.layer_type and instance.layer_type.name.lower() in app.keyword_list():
                if not alter_ego.has_perm('view_resourcebase', resource):
                    assign_perm('view_resourcebase', alter_ego, resource)      
        else:
            if instance.layer_type and instance.layer_type.name.lower() in app.keyword_list():
                if not alter_ego.has_perm('view_resourcebase', resource):
                    assign_perm('view_resourcebase', alter_ego, resource)
            #else:
            #    remove_perm('view_resourcebase', alter_ego, resource)


def unshare(instance, **kwargs):
    "Unshares the tagged object with the app alter-ego."

    owner = instance.owner
    resource = instance.resourcebase_ptr

    for app_member in owner.appmember_set.all():
        app = app_member.app
        alter_ego = app.get_alter_ego()

        if not alter_ego:
            continue 

        if (instance.layer_type 
            and instance.layer_type.name.lower() in app.keyword_list()
            and alter_ego.has_perm('view_resourcebase', resource)
        ):
            remove_perm('view_resourcebase', alter_ego, resource)


signals.pre_save.connect(pre_save_layer, sender=Layer)
signals.pre_save.connect(resourcebase_pre_save, sender=Layer)
signals.post_save.connect(resourcebase_post_save, sender=Layer)
signals.post_save.connect(post_save_layer_type, sender=LayerType)
signals.pre_delete.connect(pre_delete_layer, sender=Layer)
signals.post_delete.connect(post_delete_layer, sender=Layer)
signals.post_save.connect(share, sender=Layer)
#signals.post_delete.connect(unshare, sender=Layer)

from eav.registry import EavConfig
class EavConfigClass(EavConfig):
    manager_attr = 'eav_objects'
    object_type = 'layer_type'
    attribute_relation='layer_metadata_type_attribute'

eav.register(Layer, EavConfigClass)


#from geonode.geoserver.helpers import set_styles
from geonode.geoserver.signals import gs_catalog

def save_style(gs_style):
    style, created = Style.objects.get_or_create(name=gs_style.sld_name)
    style.sld_title = gs_style.sld_title
    style.sld_body = gs_style.sld_body
    style.sld_url = gs_style.body_href()
    style.save()
    return style

def set_styles(layer, gs_catalog):
    style_set = []
    gs_layer = gs_catalog.get_layer(layer.name)
    default_style = gs_layer.default_style
    layer.default_style = save_style(default_style)
    style_set.append(layer.default_style)

    alt_styles = gs_layer.styles

    for alt_style in alt_styles:
        style_set.append(save_style(alt_style))

    layer.styles = style_set
    return layer
