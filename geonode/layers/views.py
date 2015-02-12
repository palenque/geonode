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
import logging
import shutil

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.utils.html import escape
from django.template.defaultfilters import slugify
from django.forms.models import inlineformset_factory
from django.db.models import F
from django.forms.forms import NON_FIELD_ERRORS
from django.views.generic import TemplateView

from guardian.shortcuts import assign_perm

from geonode.services.models import Service
from geonode.layers.forms import LayerForm, LayerUploadForm, NewLayerUploadForm, LayerAttributeForm
from geonode.base.forms import CategoryForm
from geonode.layers.models import Layer, Attribute, LayerType, Style
from geonode.base.enumerations import CHARSETS
from geonode.base.models import TopicCategory

from geonode.contrib.dynamic.models import post_layer_mapping

from geonode.utils import default_map_config, llbbox_to_mercator
from geonode.utils import GXPLayer
from geonode.utils import GXPMap
from geonode.layers.utils import file_upload, guess_attribute_match
from geonode.utils import resolve_object
from geonode.people.forms import ProfileForm, PocForm
from geonode.security.views import _perms_info_json
#from geonode.security.models import ADMIN_PERMISSIONS
from geonode.documents.models import get_related_documents

from geonode.geoserver.helpers import set_styles
from geonode.geoserver.signals import gs_catalog


logger = logging.getLogger("geonode.layers.views")

DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
GENERIC_UPLOAD_ERROR = _("There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this layer")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this layer.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this layer")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this layer's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this layer")


# def _resolve_layer(request, typename, permission='base.view_resourcebase',
#                    msg=_PERMISSION_MSG_GENERIC, **kwargs):
#     """
#     Resolve the layer by the provided typename (which may include service name) and check the optional permission.
#     """
#     service_typename = typename.split(":", 1)
#     service = Service.objects.filter(name=service_typename[0])

#     if service.count() > 0 and service[0].method != "C":
#         return resolve_object(request,
#                               Layer,
#                               {'service': service[0],
#                                'typename': service_typename[1]},
#                               permission=permission,
#                               permission_msg=msg,
#                               **kwargs)
#     else:
#         return resolve_object(request,
#                               Layer,
#                               {'typename': typename,
#                                'service': None},
#                               permission=permission,
#                               permission_msg=msg,
#                               **kwargs)


def _resolve_layer(request, name, permission='base.view_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    return resolve_object(request,
                          Layer,
                          {'name': name},
                          permission=permission,
                          permission_msg=msg,
                          **kwargs)

# Basic Layer Views #


@login_required
def layer_upload(request, template='upload/layer_upload.html'):
    if request.method == 'GET':
        creator_candidates = [request.user]
        owner_candidates = [request.user]
        for app in request.user.own_apps_list_all():
            creator_candidates.append(app.get_alter_ego())
            owner_candidates.extend(app.get_members())
        
        ctx = {
            'charsets': CHARSETS,
            'layer_types': LayerType.objects.all(),
            'owner_candidates': owner_candidates,
            'creator_candidates': creator_candidates

        }
        return render_to_response(template,
                                  RequestContext(request, ctx))
    
    elif request.method == 'POST':
        form = NewLayerUploadForm(request.POST, request.FILES)
        tempdir = None
        errormsgs = []
        out = {'success': False}

        if form.is_valid():
            title = form.cleaned_data["layer_title"]

            # Replace dots in filename - GeoServer REST API upload bug
            # and avoid any other invalid characters.
            # Use the title if possible, otherwise default to the filename
            if title is not None and len(title) > 0:
                name_base = title
            else:
                name_base, __ = os.path.splitext(
                    form.cleaned_data["base_file"].name)

            name = slugify(name_base.replace(".", "_"))

            try:
                # Moved this inside the try/except block because it can raise
                # exceptions when unicode characters are present.
                # This should be followed up in upstream Django.
                tempdir, base_file = form.write_files()

                saved_layer = file_upload(
                    base_file,
                    name=name,
                    creator=request.user,
                    overwrite=False,
                    charset=form.cleaned_data["charset"],
                    abstract=form.cleaned_data["abstract"],
                    title=form.cleaned_data["layer_title"],
                    layer_type=form.cleaned_data["layer_type"],
                    owner=form.cleaned_data["owner"]
                )

                if not saved_layer.layer_type.is_default:
                    saved_layer.keywords.add(
                        *[saved_layer.layer_type.name]
                    )

            except Exception as e:
                logger.exception(e)
                out['success'] = False
                out['errors'] = str(e)
            else:
                out['success'] = True

                if saved_layer.layer_type.is_default:
                    out['url'] = reverse('layer_metadata', args=[saved_layer.name])

                elif saved_layer.storeType == 'coverageStore':
                    out['url'] = reverse('layer_metadata', args=[saved_layer.name])
                else:
                    out['url'] = reverse('layer_attribute_mapping', args=[saved_layer.name])

                permissions = form.cleaned_data["permissions"]
                if permissions is not None and len(permissions.keys()) > 0:
                    saved_layer.set_permissions(permissions)
                    # XXX:
                    # se guarda de nuevo porque se borran los permisos
                    # y se deben dar permisos a las aplicaciones de nuevo                    
                    saved_layer.save()
                # else:
                #     saved_layer.remove_all_permissions()
                #     for perm in ADMIN_PERMISSIONS:
                #         assign_perm(perm, saved_layer.owner, saved_layer.get_self_resource())
                #         if saved_layer.owner != saved_layer.creator:
                #             assign_perm(perm, saved_layer.creator, saved_layer.get_self_resource())

            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])

            out['errors'] = form.errors
            out['errormsgs'] = errormsgs

        if out['success']:
            status_code = 200
            # out['layer_type'] = form.cleaned_data["layer_type"]
            out['fill_metadata'] = saved_layer.layer_type.fill_metadata
            out['layer_id'] = saved_layer.id
        else:
            status_code = 500

        return HttpResponse(
            json.dumps(out),
            mimetype='application/json',
            status=status_code)

@login_required
def layer_detail(request, layername, template='layers/layer_detail.html'):
    from geonode.apps.models import App

    layer = _resolve_layer(
        request,
        layername,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    layer_bbox = layer.bbox
    # assert False, str(layer_bbox)
    bbox = list(layer_bbox[0:4])
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    config["srs"] = layer.srid
    config["title"] = layer.title 
    config["bbox"] = [float(coord) for coord in bbox] if layer.srid == "EPSG:4326" else llbbox_to_mercator(
        [float(coord) for coord in bbox])

    if layer.layer_type.is_default:
        typename = layer.typename
    else:
        typename = layer.layer_type.name

    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=typename,
            ows_url=layer.ows_url + 'XXXX',
            layer_params=json.dumps(config))

    # Update count for popularity ranking.
    Layer.objects.filter(
        id=layer.id).update(popular_count=F('popular_count') + 1)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    applications = [x.get_alter_ego().id for x in App.objects.filter(appmember__role='member',appmember__user=request.user).all()]

    meta_attributes = layer.eav.get_values()
    context_dict = {
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "meta_attributes": meta_attributes,
        "applications": applications
    }

    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        'leaflet')

    if layer.storeType == 'dataStore':
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_VECTOR)
    else:
        links = layer.link_set.download().filter(
            name__in=settings.DOWNLOAD_FORMATS_RASTER)

    context_dict["links"] = links

    return render_to_response(template, RequestContext(request, context_dict))


# def _validate_required_attributes(layer, attribute_form):
#     'Validates required attribute mapping'    

#     fields = [ attr['field'] for attr in attribute_form.cleaned_data if attr['field'] ]

#     is_valid = True

#     for rf, attr in [(str(a.id), a,) for a in layer.layer_type.required_attributes()]:
#         if rf in fields and fields.count(rf) > 1:
#             attribute_form._non_form_errors.append(attr.name + _(': field repeated'))
#             is_valid = False             
#         if rf not in fields:
#             attribute_form._non_form_errors.append(attr.name + _(': association required'))
#             is_valid = False

#     return is_valid


def layer_default_metadata(request, layername, template='layers/layer_metadata.html'):

    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_METADATA
    )

    topic_category = layer.category
    poc = layer.poc
    metadata_author = layer.metadata_author

    if request.method == "POST":
        layer_form = LayerForm(request.POST, instance=layer, prefix="resource")
        category_form = CategoryForm(
            request.POST,
            prefix="category_choice_field",
            initial=int(request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)
    else:
        layer_form = LayerForm(instance=layer, prefix="resource")
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None
        )

    if (
        request.method == "POST" and 
        layer_form.is_valid() and 
        category_form.is_valid()
    ):

        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']
        new_keywords = layer_form.cleaned_data['keywords']

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc
                )
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        new_category = TopicCategory.objects.get(
            id=category_form.cleaned_data['category_choice_field']
        )

        if new_poc is not None and new_author is not None:
            the_layer = layer_form.save()
            the_layer.poc = new_poc
            the_layer.metadata_author = new_author
            the_layer.keywords.clear()
            the_layer.keywords.add(*new_keywords)
            the_layer.category = new_category
            the_layer.metadata_edited = True
            the_layer.save()
            return HttpResponseRedirect(reverse('layer_detail', args=(layer.name,)))

    if poc is None:
        poc_form = ProfileForm(instance=poc, prefix="poc")
    else:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True

    if metadata_author is None:
        author_form = ProfileForm(instance=metadata_author, prefix="author")
    else:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
    }))


def set_default_style(layer, style):

    # Save to GeoServer
    cat = gs_catalog
    gs_layer = cat.get_layer(layer.name)
    gs_layer.default_style = style.name
    styles = [style.name]
    gs_layer.styles = styles
    cat.save(gs_layer)

    # Save to Django
    layer = set_styles(layer, cat)


def layer_attribute_mapping(request, layername, template='layers/layer_attribute_mapping.html'):

    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_METADATA
    )

    layer_attribute_set = inlineformset_factory(
        Layer,
        Attribute,
        extra=0,
        form=LayerAttributeForm,
    )

    if request.method == "POST":
        
        attribute_form = layer_attribute_set(
            request.POST,
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))

        if attribute_form.is_valid():
            attribute_form.save()

            if not layer.metadata_edited:
                layer.metadata_edited = True
                layer.save()
                next_url = reverse('layer_metadata', args=(layer.name,))
            else:
                next_url = reverse('layer_detail', args=(layer.name,))

            post_layer_mapping(attribute_form.instance, Layer)

            return HttpResponseRedirect(next_url)

        else:
            print attribute_form.errors
            return render_to_response(template, RequestContext(request, {
                "layer": layer,
                "attribute_form": attribute_form,
            }))
    else:
        attribute_form = layer_attribute_set(
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))

        if not layer.metadata_edited:
            guess_attribute_match(layer,attribute_form)

        return render_to_response(template, RequestContext(request, {
            "layer": layer,
            "attribute_form": attribute_form
        }))


# def layer_custom_metadata(request, layername, template='layers/layer_custom_metadata.html'):

#     from eav.forms import BaseDynamicEntityForm

#     layer = _resolve_layer(
#         request,
#         layername,
#         'base.change_resourcebase',
#         _PERMISSION_MSG_METADATA
#     )

#     layer_attribute_set = inlineformset_factory(
#         Layer,
#         Attribute,
#         extra=0,
#         form=LayerAttributeForm,
#     )

#     # form con metadata del tipo de capa
#     class LayerMetadataForm(BaseDynamicEntityForm):

#         def __init__(self, data=None, *args, **kwargs):
#             super(LayerMetadataForm, self).__init__(data, *args, **kwargs)
#             readonly_meta_fields = [x.attribute.slug for x in
#                 layer.layer_type.metadatatype_set.filter(
#                     is_precalculated=True)]                
#             meta_fields = [
#                 a.slug for a in layer.eav.get_all_attributes().filter(
#                     layer_metadata_type_attribute__in=layer.layer_type.metadatatype_set.all()
#                 )
#             ]
#             for f in self.fields.keys():
#                 if f not in meta_fields:
#                     del self.fields[f] 
#                 if f in readonly_meta_fields:
#                     self.fields[f].widget.attrs['readonly'] = True
        
#         class Meta:
#             model = Layer

#         def clean(self):
#             cleaned_data = super(LayerMetadataForm, self).clean()
#             if self.instance.layer_type.calculated_title:
#                 try:
#                     cleaned_data['title'] =  self.instance.layer_type.calculated_title % self.cleaned_data
#                 except: pass

#             if self.instance.layer_type.calculated_abstract:
#                 try:
#                     cleaned_data['abstract'] =  self.instance.layer_type.calculated_abstract % self.cleaned_data
#                 except: pass                
#             return cleaned_data

#     if request.method == "POST":
#         layer_form = LayerMetadataForm(request.POST, instance=layer, prefix="resource")
#         attribute_form = layer_attribute_set(
#             request.POST,
#             instance=layer,
#             prefix="layer_attribute_set",
#             queryset=Attribute.objects.order_by('display_order'))
#     else:
#         layer_form = LayerMetadataForm(instance=layer, prefix="resource")
#         attribute_form = layer_attribute_set(
#             instance=layer,
#             prefix="layer_attribute_set",
#             queryset=Attribute.objects.order_by('display_order'))
        
#         if not layer.metadata_edited:
#             guess_attribute_match(layer,attribute_form)

#     if (
#         request.method == "POST" and 
#         layer_form.is_valid() and 
#         (not layer.metadata_edited and attribute_form.is_valid() and _validate_required_attributes(layer, attribute_form)
#         or layer.metadata_edited)
#     ):

#         the_layer = layer_form.save()

#         if the_layer.layer_type.default_style is not None:
#             set_default_style(the_layer, the_layer.layer_type.default_style)
#             the_layer.save()

#         # XXX
#         the_layer.update_concave_hull()
#         # XXX

#         if not layer.metadata_edited:
#             try:
#                 with transaction.atomic(using='default'):
#                     attribute_form.save()
#                     layer.update_attributes()

#                 the_layer.metadata_edited = True
#                 the_layer.save()
#             except Exception as e:
#                 layer_form._errors[NON_FIELD_ERRORS] = layer_form.error_class([unicode(e)])

#         return HttpResponseRedirect(reverse('layer_detail', args=(layer.service_typename,)))

#     new_attribute_form = layer_attribute_set(
#         instance=layer,
#         prefix="layer_attribute_set",
#         queryset=Attribute.objects.order_by('display_order'))

#     return render_to_response(template, RequestContext(request, {
#         "layer": layer,
#         "layer_form": layer_form,
#         "attribute_form": attribute_form if not layer.metadata_edited else new_attribute_form,
#     }))

def layer_custom_metadata(request, layername, template='layers/layer_custom_metadata.html'):

    from eav.forms import BaseDynamicEntityForm

    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_METADATA
    )

    # form con metadata del tipo de capa
    class LayerMetadataForm(BaseDynamicEntityForm):

        def __init__(self, data=None, *args, **kwargs):
            super(LayerMetadataForm, self).__init__(data, *args, **kwargs)
            readonly_meta_fields = [x.attribute.slug for x in
                layer.layer_type.metadatatype_set.filter(
                    is_precalculated=True)]                
            meta_fields = [
                a.slug for a in layer.eav.get_all_attributes().filter(
                    layer_metadata_type_attribute__in=layer.layer_type.metadatatype_set.all()
                )
            ]
            for f in self.fields.keys():
                if f not in meta_fields:
                    del self.fields[f] 
                if f in readonly_meta_fields:
                    self.fields[f].widget.attrs['readonly'] = True
        
        class Meta:
            model = Layer

        def clean(self):
            cleaned_data = super(LayerMetadataForm, self).clean()
            if self.instance.layer_type.calculated_title:
                try:
                    cleaned_data['title'] =  self.instance.layer_type.calculated_title % self.cleaned_data
                except: pass

            if self.instance.layer_type.calculated_abstract:
                try:
                    cleaned_data['abstract'] =  self.instance.layer_type.calculated_abstract % self.cleaned_data
                except: pass                
            return cleaned_data

    if request.method == "POST":
        layer_form = LayerMetadataForm(request.POST, instance=layer, prefix="resource")
    else:
        layer_form = LayerMetadataForm(instance=layer, prefix="resource")

    if request.method == "POST" and layer_form.is_valid():

        the_layer = layer_form.save()
        the_layer.update_attributes()

        if the_layer.layer_type.default_style is not None:
            set_default_style(the_layer, the_layer.layer_type.default_style)
            
        the_layer.save()
        return HttpResponseRedirect(reverse('layer_detail', args=(layer.name,)))

    return render_to_response(template, RequestContext(request, {
        "layer": layer,
        "layer_form": layer_form,
    }))


@login_required
def layer_metadata(request, layername, template='layers/layer_metadata.html'):
    
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_METADATA
    )

    if layer.layer_type.is_default:
        return layer_default_metadata(request, layername)
    else:
        return layer_custom_metadata(request, layername)


@login_required
def layer_change_poc(request, ids, template='layers/layer_change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))
    if request.method == 'POST':
        form = PocForm(request.POST)
        if form.is_valid():
            for layer in layers:
                layer.poc = form.cleaned_data['contact']
                layer.save()
            # Process the data in form.cleaned_data
            # ...
            # Redirect after POST
            return HttpResponseRedirect('/admin/maps/layer')
    else:
        form = PocForm()  # An unbound form
    return render_to_response(
        template, RequestContext(
            request, {
                'layers': layers, 'form': form}))


@login_required
def layer_replace(request, layername, template='layers/layer_replace.html'):
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_MODIFY)

    if request.method == 'GET':
        ctx = {
            'charsets': CHARSETS,
            'layer': layer,
            'is_featuretype': layer.is_vector()
        }
        return render_to_response(template,
                                  RequestContext(request, ctx))
    elif request.method == 'POST':

        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None
        out = {}

        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                saved_layer = file_upload(
                    base_file,
                    name=layer.name,
                    creator=request.user,
                    overwrite=True,
                    charset=form.cleaned_data["charset"],
                )
            except Exception as e:
                out['success'] = False
                out['errors'] = str(e)
            else:
                out['success'] = True
                out['url'] = reverse(
                    'layer_detail', args=[
                        saved_layer.name])
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.append([escape(v) for v in e])

            out['errors'] = form.errors
            out['errormsgs'] = errormsgs

        if out['success']:
            status_code = 200
        else:
            status_code = 500
        return HttpResponse(
            json.dumps(out),
            mimetype='application/json',
            status=status_code)


@login_required
def layer_remove(request, layername, template='layers/layer_remove.html'):
    try:
        layer = _resolve_layer(request, layername, 'base.delete_resourcebase',
                               _PERMISSION_MSG_DELETE)

        if (request.method == 'GET'):
            return render_to_response(template, RequestContext(request, {
                "layer": layer
            }))
        if (request.method == 'POST'):
            layer.delete()
            return HttpResponseRedirect(reverse("layer_browse"))
        else:
            return HttpResponse("Not allowed", status=403)
    except PermissionDenied:
        return HttpResponse(
            'You are not allowed to delete this layer',
            mimetype="text/plain",
            status=401
        )

class LayerListView(TemplateView):
    def get_context_data(self, **kwargs):
        return {'categories': TopicCategory.objects.all()}

