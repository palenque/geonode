from tastypie.api import Api

from .api import TagResource, TopicCategoryResource, ProfileResource, \
    GroupResource, AppResource
from .resourcebase_api import LayerResource, MapResource, DocumentResource, \
    ResourceBaseResource, FeaturedResourceBaseResource, MonitorResource, \
    AttributeResource

api = Api(api_name='api')

api.register(LayerResource())
api.register(AttributeResource())
api.register(MonitorResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(ProfileResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(TopicCategoryResource())
api.register(GroupResource())
api.register(AppResource())
api.register(FeaturedResourceBaseResource())
