import json

from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from geonode.layers.models import Layer, LayerType
from geonode.monitors.views import monitor_upload, monitor_metadata

from .resourcebase_api import MultipartResource, CommonModelApi, CommonMetaApi


class MonitorResource(MultipartResource, CommonModelApi):

    """Monitor API"""

    class Meta(CommonMetaApi):
        allowed_methods = ['get', 'post']
        queryset = Layer.objects.filter(layer_type__name='monitor').distinct().order_by('-date')
        resource_name = 'monitors'
        excludes = ['csw_anytext', 'metadata_xml']

    def obj_create(self, bundle, request=None, **kwargs):
        """

        Ejemplo simple upload:

        curl 
        --dump-header - 
        -F base_file=@lvVK4NtGvJ.shp 
        -F shx_file=@lvVK4NtGvJ.shx 
        -F dbf_file=@lvVK4NtGvJ.dbf 
        -F prj_file=@lvVK4NtGvJ.prj 
        -F layer_type=monitor
        -F charset=UTF-8
        -F layer_title='monitor test'
        -F abstract='monitor test'
        -F 'permissions={"users":{},"groups":{}}' 
        -F 'attributes=[
            {"attribute": "MASA_1", "mapping": "MASA_HUMEDO", "magnitude": "kg"}, 
            {"attribute":"MASA_2", "mapping": "MASA_SECO", "magnitude": "kg"}]'
        'http://localhost:8000/api/monitors/?username=admin&api_key=xxx'


        Ejemplo ppciones de permisos:
        
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }
        """

        attrs = json.loads(bundle.data['attributes'])
        if not attrs:
            raise BadRequest('Attributes mapping required')

        # creates a layer
        try:
            result = json.loads(monitor_upload(bundle.request).content)
            result['layer_type'] = LayerType.objects.get(name=result.get('layer_type'))
        except Exception, e:
            raise BadRequest('Error uploading monitor')

        if result['success']:
            layer = Layer.objects.get(id=result['layer_id'])
        else:
            raise BadRequest(result['errors'])
        
        return layer
        # map attributes
        try:
            mapping = {a['attribute']: {'field': a['mapping'], 'magnitude': a['magnitude']} for a in attrs}

            with transaction.commit_manually(using="default"):

                # FIXME: validar campos requeridos
                for attr in layer.attribute_set.filter(attribute__in=mapping.keys()):
                    attr.field = mapping[attr.attribute]['mapping']
                    attr.magnitude = mapping[attr.attribute]['magnitude']
                    attr.save()

                try:
                    layer.update_attributes(commit=False)
                except:
                    layer_form._errors[NON_FIELD_ERRORS] = layer_form.error_class([
                        _(u'Some attributes could be updated. Please review association and types.')
                    ])
                else:
                    layer.update_attributes()
                    updated_attributes = True

        except Exception, e:
            layer.delete()
            raise BadRequest('Error trying to map fields')

        return layer

