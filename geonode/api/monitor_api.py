
from tastypie.resources import Resource

from geonode.layers.models import Layer
from .resourcebase_api import MultipartResource, CommonModelApi, CommonMetaApi

class MonitorResource(MultipartResource, CommonModelApi):

    """Monitor API"""

    class Meta(CommonMetaApi):
        allowed_methods = ['get', 'post']
        queryset = Layer.objects.filter(layer_type='monitor').distinct().order_by('-date')
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
        -F charset=UTF-8 # opcional
        -F layer_title='monitor test'
        -F abstract='monitor test'
        -F 'permissions={"users":{},"groups":{}}' 
        'http://localhost:8000/api/monitors/?username=admin&api_key=xxx'


        Ejemplo ppciones de permisos:
        
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }
        """

        import json
        from geonode.monitors.views import monitor_upload
        from geonode.layers.models import Layer
        from tastypie.exceptions import BadRequest

        try:
            result = json.loads(monitor_upload(bundle.request).content)
        except Exception, e:
            raise BadRequest('Error uploading monitor')

        if result['success']:
            return Layer.objects.get(id=result['layer_id'])
        raise BadRequest(result['errors'])

