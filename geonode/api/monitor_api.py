import json

from tastypie.resources import Resource
from tastypie.exceptions import BadRequest

from geonode.layers.models import Layer
from geonode.monitors.views import monitor_upload, monitor_metadata

from .authorization import AttributeAuthorization
from .resourcebase_api import MultipartResource, CommonModelApi, CommonMetaApi



class MonitorResource(MultipartResource, CommonModelApi):

    """Monitor API"""

    class Meta(CommonMetaApi):
        allowed_methods = ['get', 'post']
        queryset = Layer.objects.filter(layer_type='monitor').distinct().order_by('-date')
        resource_name = 'monitors'
        excludes = ['csw_anytext', 'metadata_xml']

    def _create_metadata_request(self):
        pass

    def obj_create(self, bundle, request=None, **kwargs):
        """

        Ejemplo simple upload:

        curl 
        --dump-header - 
        -F base_file=@lvVK4NtGvJ.shp 
        -F shx_file=@lvVK4NtGvJ.shx 
        -F dbf_file=@lvVK4NtGvJ.dbf 
        -F prj_file=@lvVK4NtGvJ.prj 
        -F charset=UTF-8
        -F layer_title='monitor test'
        -F abstract='monitor test'
        -F 'permissions={"users":{},"groups":{}}' 
        -F 'attributes=[{"attribute_label":"Masa Seco", "field": "MASA_SECO"}]'
        -F 'attributes=[
            {"attribute": "MASA_1", "field": "MASA_HUMEDO", "magnitude": "kg"}, 
            {"attribute":"MASA_2", "field": "MASA_SECO", "magnitude": "kg"}]'
        'http://localhost:8000/api/monitors/?username=admin&api_key=xxx'


        Ejemplo ppciones de permisos:
        
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }
        """

        from geonode.monitors.views import _rename_fields, _precalculate_yield

        # creates layer
        try:
            result = json.loads(monitor_upload(bundle.request).content)
        except Exception, e:
            raise BadRequest('Error uploading monitor')

        if result['success']:
            layer = Layer.objects.get(id=result['layer_id'])
        else:
            raise BadRequest(result['errors'])


        attrs = json.loads(bundle.data['attributes'])
        if not attrs:
            raise BadRequest('Attributes mapping required')

        try:
            mapping = {a['attribute']: {'field': a['field'], 'magnitude': a['magnitude']} for a in attrs}

            # FIXME: validar campos requeridos

            for attr in layer.attribute_set.filter(attribute__in=mapping.keys()):
                attr.field = mapping[attr.attribute]['field']
                attr.magnitude = mapping[attr.attribute]['magnitude']
                attr.save()

            _rename_fields(layer)
            _precalculate_yield(layer)

        except Exception, e:
            layer.delete()
            raise BadRequest('foo')

        return layer

