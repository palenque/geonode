from tastypie.api import Api

from .api import TagResource, TopicCategoryResource, ProfileResource, \
    GroupResource, AppResource, LayerTypeResource, TabularTypeResource, \
    EavAttributeResource
from .resourcebase_api import LayerResource, MapResource, DocumentResource, \
    ResourceBaseResource, FeaturedResourceBaseResource, LinkResource, \
    InternalLinkResource, TabularResource, TabularAttributeResource

    
api = Api(api_name='api')

api.register(LayerResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(TabularResource())
api.register(TabularTypeResource())
api.register(TabularAttributeResource())
api.register(ProfileResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(TopicCategoryResource())
api.register(GroupResource())
api.register(AppResource())
api.register(FeaturedResourceBaseResource())
api.register(LayerTypeResource())
api.register(LinkResource())
api.register(InternalLinkResource())
api.register(EavAttributeResource())