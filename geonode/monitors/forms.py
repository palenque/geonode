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

import os
import tempfile
import taggit
import pint

from django import forms
from django.utils import simplejson as json
from django.utils.translation import ugettext as _
from modeltranslation.forms import TranslationModelForm

from mptt.forms import TreeNodeMultipleChoiceField

from geonode.layers.models import Layer, Attribute
from geonode.layers.units import units
from geonode.people.models import Profile
from geonode.base.models import Region, TopicCategory

import autocomplete_light


class JSONField(forms.CharField):

    def clean(self, text):
        text = super(JSONField, self).clean(text)
        try:
            return json.loads(text)
        except ValueError:
            raise forms.ValidationError("this field must be valid JSON")


class MonitorForm(TranslationModelForm):
    date = forms.DateField(
        required=True,
        label=_("Harvest date"),
        widget=forms.DateInput(
            attrs={            
                "class": "datepicker",
                'data-date-format': "yyyy-mm-dd"}))
    
    temporal_extent_start = forms.DateField(
        required=False,
        label= _("Season Start"),
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
                'data-date-format': "yyyy-mm-dd"}))
    temporal_extent_end = forms.DateField(
        required=False,
        label= _("Season End"),
        widget=forms.DateInput(
            attrs={
                "class": "datepicker",
                'data-date-format': "yyyy-mm-dd"}))

    poc = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Point Of Contact",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    metadata_author = forms.ModelChoiceField(
        empty_label="Person outside GeoNode (fill form)",
        label="Metadata Author",
        required=False,
        queryset=Profile.objects.exclude(
            username='AnonymousUser'),
        widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    category = forms.ModelChoiceField(
        empty_label="----",
        label="Product",
        required=True,
        queryset=TopicCategory.objects.filter(identifier__startswith='yield/'))
        #widget=autocomplete_light.ChoiceWidget('ProfileAutocomplete'))

    keywords = taggit.forms.TagField(
        required=False,
        help_text=_("A space or comma-separated list of keywords"))

    # regions = TreeNodeMultipleChoiceField(
    #     required=False,
    #     queryset=Region.objects.all(),
    #     level_indicator=u'___')
    # regions.widget.attrs = {"size": 20}

    class Meta:
        model = Layer
        exclude = (
            #'metadata_edited',
            'owner',
            'creator',
            'app',

            'layer_type',
            'license',
            'language',
            'spatial_representation_type',
            'featured',
            'thumbnail_url',
            'detail_url',
            'rating',
            'purpose',
            'abstract',
            'edition',
            'maintenance_frequency',
            'regions',
            'restriction_code_type',
            #'date_type',
            'keywords',
            'charset',
            'upload_session',
            'data_quality_statement',
            'distribution_description',
            'distribution_url',
            'supplemental_information',
            'constraints_other',
            'service',
            #'date',
            'metadata_author',
            'layer_type',
            'contacts',
            'workspace',
            'store',
            'name',
            'uuid',
            'storeType',
            'typename',
            'bbox_x0',
            'bbox_x1',
            'bbox_y0',
            'bbox_y1',
            'srid',
            #'category',
            'csw_typename',
            'csw_schema',
            'csw_mdsource',
            'csw_type',
            'csw_wkt_geometry',
            'metadata_uploaded',
            'metadata_xml',
            'csw_anytext',
            'popular_count',
            'share_count',
            'thumbnail',
            'default_style',
            'styles')
        widgets = autocomplete_light.get_widgets_dict(Layer)

    def __init__(self, *args, **kwargs):
        super(MonitorForm, self).__init__(*args, **kwargs)
        self.fields['date_type'].widget = forms.HiddenInput()
        self.fields['metadata_edited'].widget = forms.HiddenInput()
        self.fields['title'].label = "Field"

        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update(
                    {
                        'class': 'has-popover',
                        'data-content': help_text,
                        'data-placement': 'right',
                        'data-container': 'body',
                        'data-html': 'true'})

    def clean_metadata_edited(self):
        self.cleaned_data['metadata_edited'] = True
        return True


class LayerUploadForm(forms.Form):
    base_file = forms.FileField()
    dbf_file = forms.FileField(required=False)
    shx_file = forms.FileField(required=False)
    prj_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    charset = forms.CharField(required=False)

    spatial_files = (
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file")

    def clean(self):
        cleaned = super(LayerUploadForm, self).clean()
        base_name, base_ext = os.path.splitext(cleaned["base_file"].name)
        if base_ext.lower() == '.zip':
            # for now, no verification, but this could be unified
            pass
        elif base_ext.lower() not in (".shp", ".tif", ".tiff", ".geotif", ".geotiff"):
            raise forms.ValidationError(
                "Only Shapefiles and GeoTiffs are supported. You uploaded a %s file" %
                base_ext)
        if base_ext.lower() == ".shp":
            dbf_file = cleaned["dbf_file"]
            shx_file = cleaned["shx_file"]
            if dbf_file is None or shx_file is None:
                raise forms.ValidationError(
                    "When uploading Shapefiles, .SHX and .DBF files are also required.")
            dbf_name, __ = os.path.splitext(dbf_file.name)
            shx_name, __ = os.path.splitext(shx_file.name)
            if dbf_name != base_name or shx_name != base_name:
                raise forms.ValidationError(
                    "It looks like you're uploading "
                    "components from different Shapefiles. Please "
                    "double-check your file selections.")
            if cleaned["prj_file"] is not None:
                prj_file = cleaned["prj_file"].name
                if os.path.splitext(prj_file)[0] != base_name:
                    raise forms.ValidationError(
                        "It looks like you're "
                        "uploading components from different Shapefiles. "
                        "Please double-check your file selections.")
            if cleaned["xml_file"] is not None:
                xml_file = cleaned["xml_file"].name
                if os.path.splitext(xml_file)[0] != base_name:
                    if xml_file.find('.shp') != -1:
                        # force rename of file so that file.shp.xml doesn't
                        # overwrite as file.shp
                        cleaned["xml_file"].name = '%s.xml' % base_name
        return cleaned

    def write_files(self):
        tempdir = tempfile.mkdtemp()
        for field in self.spatial_files:
            f = self.cleaned_data[field]
            if f is not None:
                path = os.path.join(tempdir, f.name)
                with open(path, 'wb') as writable:
                    for c in f.chunks():
                        writable.write(c)
        absolute_base_file = os.path.join(tempdir,
                                          self.cleaned_data["base_file"].name)
        return tempdir, absolute_base_file


class NewLayerUploadForm(LayerUploadForm):
    sld_file = forms.FileField(required=False)
    xml_file = forms.FileField(required=False)

    abstract = forms.CharField(required=False)
    layer_title = forms.CharField(required=False)
    permissions = JSONField()
    charset = forms.CharField(required=False)

    spatial_files = (
        "base_file",
        "dbf_file",
        "shx_file",
        "prj_file",
        "sld_file",
        "xml_file")


class LayerDescriptionForm(forms.Form):
    title = forms.CharField(300)
    abstract = forms.CharField(1000, widget=forms.Textarea, required=False)
    keywords = forms.CharField(500, required=False)


from .enumerations import MONITOR_FIELD_MAGNITUDES, MONITOR_FIELDS

class MonitorAttributeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(MonitorAttributeForm, self).__init__(*args, **kwargs)
        self.fields['attribute'].widget.attrs['readonly'] = True
        for field in ['attribute_label','description','display_order']:
            self.fields[field].widget = forms.HiddenInput()
        self.fields['magnitude'].widget.attrs['maxlength']= 10            
        self.fields['magnitude'].widget.attrs['size']= 10  
        choices = tuple([('','-----')] + list(MONITOR_FIELDS))
        self.fields['field'].widget = forms.Select(choices=choices)

    def clean_magnitude(self):
        if self.cleaned_data['field']:
            if self.cleaned_data['field'] in MONITOR_FIELD_MAGNITUDES:
                if not self.cleaned_data['magnitude']:
                    raise forms.ValidationError("Unit not specified. Default is '%s'" \
                        % MONITOR_FIELD_MAGNITUDES[self.cleaned_data['field']])
                else:
                    try:
                        (1 * units[self.cleaned_data['magnitude']]).to(MONITOR_FIELD_MAGNITUDES[self.cleaned_data['field']])
                    except pint.DimensionalityError:
                        raise forms.ValidationError("Unit not valid. Cannot convert '%s' to '%s'" \
                            % (self.cleaned_data['magnitude'],MONITOR_FIELD_MAGNITUDES[self.cleaned_data['field']].units))
                    except pint.UndefinedUnitError:
                        raise forms.ValidationError("Invalid unit: '%s'" \
                            % self.cleaned_data['magnitude'])
            else:
                if self.cleaned_data['magnitude']:
                    raise forms.ValidationError("This field has no unit.")
        return self.cleaned_data['magnitude']

    # def clean(self):
    #     'Validate magnitudes.'

    #     cleaned_data = super(MonitorAttributeForm, self).clean()
    #     if cleaned_data['field']:
    #         if cleaned_data['field'] in MONITOR_FIELD_MAGNITUDES:
    #             if not cleaned_data['magnitude']:
    #                 raise forms.ValidationError(cleaned_data['field'],"Unit not specified. Default is '%s'" \
    #                     % MONITOR_FIELD_MAGNITUDES[cleaned_data['field']])
    #             else:
    #                 try:
    #                     (1 * units[cleaned_data['magnitude']]).to(MONITOR_FIELD_MAGNITUDES[cleaned_data['field']])
    #                 except pint.DimensionalityError:
    #                     raise forms.ValidationError(cleaned_data['field'],"Unit not valid. Cannot convert '%s' to '%s'" \
    #                         % (cleaned_data['magnitude'],MONITOR_FIELD_MAGNITUDES[cleaned_data['field']].units))
    #         else:
    #             if cleaned_data['magnitude']:
    #                 raise forms.ValidationError(cleaned_data['field'],"This field has no unit." \
    #                     % (MONITOR_FIELD_MAGNITUDES[cleaned_data['field']].units))

    #         # mg = dict(MONITOR_FIELD_MAGNITUDES)
    #         # if (mg.has_key(cleaned_data['field']) and 
    #         #     cleaned_data['magnitude'] not in dict(mg[cleaned_data['field']]).keys()):
    #         #     raise forms.ValidationError("Magnitude not valid: %s" % cleaned_data['field'])
    #         cleaned_data['attribute_label'] = cleaned_data['field'].lower()
    #     return cleaned_data

    class Meta:
        model = Attribute
        exclude = (
            'attribute_type',
            'count',
            'min',
            'max',
            'average',
            'median',
            'stddev',
            'sum',
            'unique_values',
            'last_stats_updated',
            'objects')


class LayerStyleUploadForm(forms.Form):
    layerid = forms.IntegerField()
    name = forms.CharField(required=False)
    update = forms.BooleanField(required=False)
    sld = forms.FileField()
