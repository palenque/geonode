#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
#
#    This software is derived from EAV-Django originally written and
#    copyrighted by Andrey Mikhaylenko <http://pypi.python.org/pypi/eav-django>
#
#    This is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with EAV-Django.  If not, see <http://gnu.org/licenses/>.
'''
#####
forms
#####

The forms used for admin integration

Classes
-------
'''
from copy import deepcopy

from django.forms import BooleanField, CharField, DateTimeField, FloatField, \
                         IntegerField, ModelForm, ChoiceField, ValidationError, ModelChoiceField
from django.contrib.admin.widgets import AdminSplitDateTime
from django.utils.translation import ugettext_lazy as _


class BaseDynamicEntityForm(ModelForm):
    '''
    ModelForm for entity with support for EAV attributes. Form fields are
    created on the fly depending on Schema defined for given entity instance.
    If no schema is defined (i.e. the entity instance has not been saved yet),
    only static fields are used. However, on form validation the schema will be
    retrieved and EAV fields dynamically added to the form, so when the
    validation is actually done, all EAV fields are present in it (unless
    Rubric is not defined).
    '''

    FIELD_CLASSES = {
        'text': CharField,
        'float': FloatField,
        'int': IntegerField,
        'date': DateTimeField,
        'bool': BooleanField,
        'enum': ChoiceField,
        # 'enum': ModelChoiceField
    }

    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.object_type = config_cls.object_type
        self.attribute_relation = config_cls.attribute_relation
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()

    def _build_dynamic_fields(self):
        # reset form fields
        self.fields = deepcopy(self.base_fields)

        attributes = self.entity.get_all_attributes().filter(
            **{self.attribute_relation + '__in': getattr(self.instance, self.object_type).metadatatype_set.all()}
        )

        for attribute in attributes:
            value = getattr(self.entity, attribute.slug)

            defaults = {
                'label': attribute.name.capitalize(),
                'required': attribute.required,
                'help_text': attribute.help_text,
                'validators': attribute.get_validators(),
            }

            datatype = attribute.datatype
            if datatype == attribute.TYPE_ENUM:
                enums = attribute.get_choices().values_list('value', 'value')

                choices = [('', '-----')] + list(enums)

                defaults.update({'choices': choices})
                # defaults.update({'queryset': attribute.get_choices()})
                if value:
                    # defaults.update({'initial': value.pk})
                    defaults.update({'initial': value.value})


            elif datatype == attribute.TYPE_DATE:
                defaults.update({'widget': AdminSplitDateTime})
            elif datatype == attribute.TYPE_OBJECT:
                continue

            MappedField = self.FIELD_CLASSES[datatype]
            self.fields[attribute.slug] = MappedField(**defaults)

            # fill initial data (if attribute was already defined)
            if value and not datatype == attribute.TYPE_ENUM: #enum done above
                self.initial[attribute.slug] = value

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance`` and related EAV attributes.

        Returns ``instance``.
        """
        if self.errors:
            raise ValueError(_(u"The %s could not be saved because the data"
                             u"didn't validate.") % \
                             self.instance._meta.object_name)

        # create entity instance, don't save yet
        instance = super(BaseDynamicEntityForm, self).save(commit=False)

        # assign attributes
        for attribute in self.entity.get_all_attributes():
            value = self.cleaned_data.get(attribute.slug)
            if attribute.datatype == attribute.TYPE_ENUM:
                if value:
                    # value = attribute.enum_group.enums.get(pk=value)
                    value = attribute.enum_group.enums.get(value=value)
                else:
                    value = None

            setattr(self.entity, attribute.slug, value)

        # save entity and its attributes
        if commit:
            instance.save()

        return instance
