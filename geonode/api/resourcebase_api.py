import re, json, logging
import datetime as dt
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
from django.db import transaction, connections

from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils import trailing_slash
from tastypie.exceptions import ImmediateHttpResponse

from guardian.shortcuts import get_objects_for_user, get_anonymous_user

from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404

from tastypie.utils.mime import build_content_type
from tastypie.http import HttpNoContent, HttpBadRequest
from tastypie.exceptions import Unauthorized
from tastypie.exceptions import BadRequest

if settings.HAYSTACK_SEARCH:
    from haystack.query import SearchQuerySet  # noqa

from geonode.layers.forms import LayerForm
from geonode.people.models import Profile
from geonode.apps.models import App
from geonode.layers.models import Layer, LayerType, AttributeType
from geonode.layers.views import layer_upload

from geonode.tabular.forms import DocumentReplaceForm
from geonode.tabular.forms import DocumentCreateForm
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.tabular.models import Tabular, TabularType
from geonode.tabular.models import Attribute as TabularAttribute
from geonode.base.models import ResourceBase, TopicCategory, Link, InternalLink
from .authorization import GeoNodeAuthorization, InternalLinkAuthorization

from .api import TagResource, ProfileResource, TopicCategoryResource, \
    FILTER_TYPES, AppResource, remove_internationalization_fields, \
    PostQueryFilteringMixin

from eav.forms import BaseDynamicEntityForm


LAYER_SUBTYPES = {
    'vector': 'dataStore',
    'raster': 'coverageStore',
    'remote': 'remoteStore',
}
FILTER_TYPES.update(LAYER_SUBTYPES)


def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

class MultipartResource(object):
    'Allows multipart request.'

    def deserialize(self, request, data, format=None):

        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')

        if format == 'application/x-www-form-urlencoded':
            return request.POST

        if format.startswith('multipart'):
            data = request.POST.copy()
            data.update(request.FILES)

            return data

        return super(MultipartResource, self).deserialize(request, data, format)



extra_actions = [
    {
        "name": 'transfer_owner',
        "http_method": "POST",
        "resource_type": "",
        "summary": "Transfer ownership to another user",
        "fields": {
            "new_owner": {
                "type": "integer",
                "required": True,
                "description": "new owner id"
            },
            "app_id": {
                "type": "integer",
                "required": True,
                "description": "app that generated the resource"
            }                
        }
    }
]


class CommonMetaApi:
    extra_actions = extra_actions
    authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
    authorization = GeoNodeAuthorization()
    allowed_methods = ['get']
    filtering = {'title': ALL,
                 'keywords': ALL_WITH_RELATIONS,
                 'category': ALL_WITH_RELATIONS,
                 'owner': ALL_WITH_RELATIONS,
                 'creator': ALL_WITH_RELATIONS,
                 'date': ALL,
                 'csw_type': ALL,
                 }
    ordering = ['date', 'title', 'popular_count']
    max_limit = None
    #paginator_class = Paginator

class CommonModelApi(ModelResource, PostQueryFilteringMixin):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    category = fields.ToOneField(
        TopicCategoryResource,
        'category',
        null=True,
        full=True)
    owner = fields.ToOneField(ProfileResource, 'owner', full=True)
    creator = fields.ToOneField(ProfileResource, 'creator', full=True, null=True)
    permission_class = fields.CharField(null=True)
    metadata = fields.DictField(null=True)

    def dehydrate(self, bundle):
        bundle = super(CommonModelApi, self).dehydrate(bundle)
        return remove_internationalization_fields(bundle)

    def dehydrate_metadata(self, bundle):
        if hasattr(bundle.obj,'eav'):
            return bundle.obj.eav.get_values_dict()
        else:
            return {}

    def dehydrate_permission_class(self, bundle):
        if type(bundle.obj.is_public) == bool:
            return bundle.obj
        else:
            return ""
        if bundle.obj.is_public():
            return "public"
        else:
            # TODO: shared missing
            return "owned"

    def apply_eav_filters(self, objects, bundle):
        for flt,vals in bundle.request.eav_filters.items():
            objects = filter(lambda obj: \
                hasattr(obj,'eav') and \
                hasattr(obj.eav,flt) and \
                getattr(obj.eav,flt) in vals, objects)
        return objects


    def build_filters(self, filters={}):
        orm_filters = {}

        if 'app' in filters:
            orm_filters['app'] = filters.pop('app')

        to_remove = set()
        for flt,vals in filters.lists():
            if flt.startswith('eav_'):
                to_remove.add(flt)                
                if flt.endswith('__in'): flt = flt[:-4]
                orm_filters[flt] = vals
        for flt in to_remove: filters.pop(flt)

        orm_filters.update(self.build_post_query_filters(filters))

        orm_filters.update(super(CommonModelApi, self).build_filters(filters))

        if 'type__in' in filters and filters[
                'type__in'] in FILTER_TYPES.keys():
            orm_filters.update({'type': filters.getlist('type__in')})
        if 'extent' in filters:
            orm_filters.update({'extent': filters['extent']})            
        # Nothing returned if +'s are used instead of spaces for text search,
        # so swap them out. Must be a better way of doing this?

        for filter in orm_filters:
            if filter in ['title__contains', 'q']:
                orm_filters[filter] = orm_filters[filter].replace("+", " ")
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        request.eav_filters = {}

        if 'app' in applicable_filters:
            app = applicable_filters.pop('app')[0]
            if not any(x for x in request.user.apps_list_all() if x.slug == app):
                # TODO: Error
                pass
            else:
                request.user = Profile.objects.get(username=app)

        to_remove = set()
        for flt in applicable_filters:
            if flt.startswith('eav_'):
                request.eav_filters[flt[4:]] = applicable_filters[flt]
                to_remove.add(flt)
        for flt in to_remove: applicable_filters.pop(flt)

        self.process_post_query_filters(request, applicable_filters)

        types = applicable_filters.pop('type', None)
        extent = applicable_filters.pop('extent', None)

        semi_filtered = super(
            CommonModelApi,
            self).apply_filters(
            request,
            applicable_filters)
        filtered = None
        if types:
            for the_type in types:
                if the_type in LAYER_SUBTYPES.keys():
                    if filtered:
                        filtered = filtered | semi_filtered.filter(
                            Layer___storeType=LAYER_SUBTYPES[the_type])
                    else:
                        filtered = semi_filtered.filter(
                            Layer___storeType=LAYER_SUBTYPES[the_type])
                else:
                    if filtered:
                        filtered = filtered | semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
                    else:
                        filtered = semi_filtered.instance_of(
                            FILTER_TYPES[the_type])
        else:
            filtered = semi_filtered

        if extent:
            filtered = self.filter_bbox(filtered, extent)

        return filtered


    def filter_bbox(self, queryset, bbox):
        """
        modify the queryset q to limit to data that intersects with the
        provided bbox

        bbox - 4 tuple of floats representing 'southwest_lng,southwest_lat,
        northeast_lng,northeast_lat'
        returns the modified query
        """
        bbox = bbox.split(
            ',')  # TODO: Why is this different when done through haystack?
        bbox = map(str, bbox)  # 2.6 compat - float to decimal conversion

        intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) |
                       Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))

        return queryset.filter(intersects)

    def build_haystack_filters(self, parameters):
        from haystack.inputs import Raw
        from haystack.query import SearchQuerySet, SQ  # noqa

        sqs = None

        # Retrieve Query Params

        # Text search
        query = parameters.get('q', None)

        # Types and subtypes to filter (map, layer, vector, etc)
        type_facets = parameters.getlist("type__in", [])

        # If coming from explore page, add type filter from resource_name
        resource_filter = self._meta.resource_name.rstrip("s")
        if resource_filter != "base" and resource_filter not in type_facets:
            type_facets.append(resource_filter)

        # Publication date range (start,end)
        date_range = parameters.get("date_range", ",").split(",")

        # Topic category filter
        category = parameters.getlist("category__identifier__in")

        # Keyword filter
        keywords = parameters.getlist("keywords__slug__in")

        # Sort order
        sort = parameters.get("order_by", "relevance")

        # Geospatial Elements
        bbox = parameters.get("extent", None)

        # Filter by Type and subtype
        if type_facets is not None:

            types = []
            subtypes = []

            for type in type_facets:
                if type in ["map", "layer", "document", "user"]:
                    # Type is one of our Major Types (not a sub type)
                    types.append(type)
                elif type in LAYER_SUBTYPES.keys():
                    subtypes.append(type)

            if len(subtypes) > 0:
                types.append("layer")
                sqs = SearchQuerySet().narrow("subtype:%s" %
                                              ','.join(map(str, subtypes)))

            if len(types) > 0:
                sqs = (SearchQuerySet() if sqs is None else sqs).narrow(
                    "type:%s" % ','.join(map(str, types)))

        # Filter by Query Params
        # haystack bug? if boosted fields aren't included in the
        # query, then the score won't be affected by the boost
        if query:
            if query.startswith('"') or query.startswith('\''):
                # Match exact phrase
                phrase = query.replace('"', '')
                sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                    SQ(title__exact=phrase) |
                    SQ(description__exact=phrase) |
                    SQ(content__exact=phrase)
                )
            else:
                words = [
                    w for w in re.split(
                        '\W',
                        query,
                        flags=re.UNICODE) if w]
                for i, search_word in enumerate(words):
                    if i == 0:
                        sqs = (SearchQuerySet() if sqs is None else sqs) \
                            .filter(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )
                    elif search_word in ["AND", "OR"]:
                        pass
                    elif words[i - 1] == "OR":  # previous word OR this word
                        sqs = sqs.filter_or(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )
                    else:  # previous word AND this word
                        sqs = sqs.filter(
                            SQ(title=Raw(search_word)) |
                            SQ(description=Raw(search_word)) |
                            SQ(content=Raw(search_word))
                        )

        # filter by category
        if category:
            sqs = (SearchQuerySet() if sqs is None else sqs).narrow(
                'category:%s' % ','.join(map(str, category)))

        # filter by keyword: use filter_or with keywords_exact
        # not using exact leads to fuzzy matching and too many results
        # using narrow with exact leads to zero results if multiple keywords
        # selected
        if keywords:
            for keyword in keywords:
                sqs = (
                    SearchQuerySet() if sqs is None else sqs).filter_or(
                    keywords_exact=keyword)

        # filter by date
        if date_range[0]:
            sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                SQ(date__gte=date_range[0])
            )

        if date_range[1]:
            sqs = (SearchQuerySet() if sqs is None else sqs).filter(
                SQ(date__lte=date_range[1])
            )

        # Filter by geographic bounding box
        if bbox:
            left, bottom, right, top = bbox.split(',')
            sqs = (
                SearchQuerySet() if sqs is None else sqs).exclude(
                SQ(
                    bbox_top__lte=bottom) | SQ(
                    bbox_bottom__gte=top) | SQ(
                    bbox_left__gte=right) | SQ(
                        bbox_right__lte=left))

        # Apply sort
        if sort.lower() == "-date":
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("-modified")
        elif sort.lower() == "date":
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("modified")
        elif sort.lower() == "title":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "title_sortable")
        elif sort.lower() == "-title":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "-title_sortable")
        elif sort.lower() == "-popular_count":
            sqs = (SearchQuerySet() if sqs is None else sqs).order_by(
                "-popular_count")
        else:
            sqs = (
                SearchQuerySet() if sqs is None else sqs).order_by("-modified")

        return sqs

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Get the list of objects that matches the filter
        sqs = self.build_haystack_filters(request.GET)
        if not settings.SKIP_PERMS_FILTER:
            # Get the list of objects the user has access to
            filter_set = set(
                get_objects_for_user(
                    request.user,
                    'base.view_resourcebase').values_list(
                    'id',
                    flat=True))

            # Do the query using the filterset and the query term. Facet the
            # results
            if len(filter_set) > 0:
                sqs = sqs.filter(oid__in=filter_set).facet('type').facet('subtype').facet('owner').facet('keywords')\
                    .facet('category')
            else:
                sqs = None
        else:
            sqs = sqs.facet('type').facet('subtype').facet(
                'owner').facet('keywords').facet('category')

        if sqs:
            # Build the Facet dict
            facets = {}
            for facet in sqs.facet_counts()['fields']:
                facets[facet] = {}
                for item in sqs.facet_counts()['fields'][facet]:
                    facets[facet][item[0]] = item[1]

            # Paginate the results
            paginator = Paginator(sqs, request.GET.get('limit'))

            try:
                page = paginator.page(
                    int(request.GET.get('offset')) /
                    int(request.GET.get('limit'), 0) + 1)
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")

            if page.has_previous():
                previous_page = page.previous_page_number()
            else:
                previous_page = 1
            if page.has_next():
                next_page = page.next_page_number()
            else:
                next_page = 1
            total_count = sqs.count()
            objects = page.object_list
        else:
            next_page = 0
            previous_page = 0
            total_count = 0
            facets = {}
            objects = []

        object_list = {
           "meta": {"limit": 100,  # noqa
                    "next": next_page,
                    "offset": int(getattr(request.GET, 'offset', 0)),
                    "previous": previous_page,
                    "total_count": total_count,
                    "facets": facets,
                    },
            'objects': map(lambda x: x.get_stored_fields(), objects),
        }
        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def obj_get_list(self, **kwargs):
        objects = super(CommonModelApi, self).obj_get_list(**kwargs)
        bundle = kwargs['bundle']
        objects = self.apply_eav_filters(objects, bundle)
        objects = self.apply_post_query_filters(objects, bundle)
        return objects
        
    # def get_list_xx(self, request, **kwargs):
    #     """
    #     Returns a serialized list of resources.

    #     Calls ``obj_get_list`` to provide the data, then handles that result
    #     set and serializes it.

    #     Should return a HttpResponse (200 OK).
    #     """
    #     # TODO: Uncached for now. Invalidation that works for everyone may be
    #     # impossible.

    #     base_bundle = self.build_bundle(request=request)
    #     objects = self.obj_get_list(
    #         bundle=base_bundle,
    #         **self.remove_api_resource_names(kwargs))

    #     sorted_objects = self.apply_sorting(objects, options=request.GET)

    #     paginator = self._meta.paginator_class(
    #         request.GET,
    #         sorted_objects,
    #         resource_uri=self.get_resource_uri(),
    #         limit=self._meta.limit,
    #         max_limit=self._meta.max_limit,
    #         collection_name=self._meta.collection_name)
    #     to_be_serialized = paginator.page()

    #     to_be_serialized = self.alter_list_data_to_serialize(
    #         request,
    #         to_be_serialized)
    #     return self.create_response(request, to_be_serialized)

    # def create_response_xxx(
    #         self,
    #         request,
    #         data,
    #         response_class=HttpResponse,
    #         **response_kwargs):
    #     """
    #     Extracts the common "which-format/serialize/return-response" cycle.

    #     Mostly a useful shortcut/hook.
    #     """
    #     VALUES = [
    #         # fields in the db
    #         'creator',

    #         'id',
    #         'uuid',
    #         'title',
    #         'abstract',
    #         'csw_wkt_geometry',
    #         'csw_type',
    #         'distribution_description',
    #         'distribution_url',
    #         'owner_id',
    #         'share_count',
    #         'popular_count',
    #         'date',
    #         'srid',
    #         'category',
    #         'supplemental_information',
    #         'thumbnail_url',
    #         'detail_url',
    #         'rating',
    #         # 'concave_hull',

    #         'bbox_x0',
    #         'bbox_y0',
    #         'bbox_x1',
    #         'bbox_y1',
            
    #         # 'metadata_edited',
    #         # 'layer_type'
    #     ]

    #     if isinstance(
    #             data,
    #             dict) and 'objects' in data and not isinstance(
    #             data['objects'],
    #             list):


    #         # TODO: Improve
    #         objects = list(data['objects'].values(*VALUES))
    #         for objdata,obj in zip(objects, data['objects']):
    #             if not isinstance(obj,Document) and not isinstance(obj,Tabular):
    #                 for attr in ['metadata_edited', 'layer_type', 'concave_hull']:
    #                     objdata[attr] = getattr(obj, attr)

    #                 objdata['layer_type'] = obj.layer_type.name
    #                 objdata['category_description'] = obj.category.gn_description if obj.category is not None else ''
    #                 objdata['creator_username'] = obj.creator.username

    #             if obj.is_public():
    #                 objdata['permission_class'] = "public"
    #             elif request.user == obj.owner:
    #                 objdata['permission_class'] = "owned"
    #             else:
    #                 objdata['permission_class'] = "shared"

    #         data['objects'] = objects
                
    #     # XXX FEO!!
    #     if 'permission_class' in request.GET:
    #         data['objects'] = filter(lambda obj: obj['permission_class'] == request.GET['permission_class'], data['objects'])

    #     if 'layer_type' in request.GET:
    #         data['objects'] = filter(lambda obj: obj['layer_type'] == request.GET['layer_type'], data['objects'])            

    #     if 'layer_type__in' in request.GET:
    #         data['objects'] = filter(lambda obj: obj['layer_type'] in request.GET['layer_type__in'].split(','), data['objects'])

    #     data['meta']['total_count'] = len(data['objects'])

    #     desired_format = self.determine_format(request)
    #     serialized = self.serialize(request, data, desired_format)
    #     return response_class(
    #         content=serialized,
    #         content_type=build_content_type(desired_format),
    #         **response_kwargs)


    def transfer_owner(self, request, resource_id, **kwargs):
        '''Transfers ownership of an resource.

        curl 
        --dump-header -  
        -H "Content-Type: application/json" 
        -X  PUT 
        --data '{"new_owner_id": 25, "app_id": 14}' 
        'http://localhost:8000/api/base/79/transfer_owner/?username=foo&api_key=c003062347b82a8cdd4014e9f8edb5c2aef63c7a'
        '''

        self.method_check(request, allowed=['put'])
        self.is_authenticated(request)
        self.throttle_check(request)

        try:
            data = json.loads(request.body)
            new_owner_id = int(data['new_owner_id'])
            app_id = int(data['app_id'])
            new_owner = Profile.objects.get(id=new_owner_id)
            app = App.objects.get(id=app_id)
            resource  = ResourceBase.objects.get(id=resource_id)
        except Exception as e:
            return HttpBadRequest()

        if not (app.user_is_role(request.user, "manager") and
            resource.owner == request.user):
            raise Unauthorized()

        resource.transfer_owner(new_owner, app)

        return HttpNoContent()


    def prepend_urls(self):
        urls = [
            url(
                r"^(?P<resource_name>%s)/(?P<resource_id>\d+)/transfer_owner%s$" % (
                    self._meta.resource_name, trailing_slash()
                ),
                self.wrap_view('transfer_owner'), 
                name="api_transfer_owner"
            )
        ]

        if settings.HAYSTACK_SEARCH:
            return urls + [
                url(r"^(?P<resource_name>%s)/search%s$" % (
                    self._meta.resource_name, trailing_slash()
                    ),
                    self.wrap_view('get_search'), name="api_get_search")
            ]
        else:
            return urls


class ResourceBaseResource(CommonModelApi):

    """ResourceBase api"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.polymorphic_queryset() \
            .distinct().order_by('-date')
        resource_name = 'base'
        excludes = ['csw_anytext', 'metadata_xml']
        authorization = GeoNodeAuthorization()
        post_query_filtering = {
            'is_public': lambda vals: lambda res: res.is_public() in map(str2bool,vals)
        }

class FeaturedResourceBaseResource(CommonModelApi):

    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.filter(featured=True).order_by('-date')
        resource_name = 'featured'



class LinkResource(ModelResource):
    class Meta:
        queryset = Link.objects.all()
        resource_name = 'links'
        filtering = {
            'link_type': ALL
        }


class LayerTypeResource(ModelResource):

    class Meta:
        resource_name = 'layer_types'
        queryset = LayerType.objects.all()
        fields = ['name', 'description', 'fill_metadata']
        filtering = {
            'name': ALL,
        }

class LayerResource(MultipartResource, CommonModelApi):

    """Layer API"""

    layer_type = fields.ForeignKey(LayerTypeResource, 'layer_type', full=True)
    links = fields.ToManyField(LinkResource, 'link_set', full=True)
    internal_links_forward = fields.ToManyField(
        'geonode.api.resourcebase_api.InternalLinkResource','internal_links_forward_set', null=True, full=True)

    internal_links_backward = fields.ToManyField(
        'geonode.api.resourcebase_api.InternalLinkResource','internal_links_backward_set', null=True, full=True)

    class Meta(CommonMetaApi):

        extra_actions = extra_actions + [
            {
                "name": 'table',
                "http_method": "GET",
                "resource_type": "",
                "summary": "Get layer data",
                "fields": {
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Limit"
                    },
                    "offset": {
                        "type": "integer",
                        "required": False,
                        "description": "Offset"
                    }                
                }
            },
            {
                "name": '',
                "http_method": "POST",
                "resource_type": "list",
                "summary": "Create a new layer",
                "fields": {
                    "base_file": {
                        "type": "file",
                        "required": True,
                        "description": ".shp file"
                    },                
                    "shx_file": {
                        "type": "file",
                        "required": True,
                        "description": ".shx file"
                    },                    
                    "dbf_file": {
                        "type": "file",
                        "required": True,
                        "description": ".dbf file"
                    },                    
                    "prj_file": {
                        "type": "file",
                        "required": True,
                        "description": ".prj file"
                    },     
                    "attributes": {
                        "type": "string",
                        "required": True,
                        "description": """Define if table has header. Omite if not has header."""
                    },                                                                           
                    "layer_type": {
                        "type": "string",
                        "required": False,
                        "description": "Layer type"
                    },                    
                    "layer_title": {
                        "type": "string",
                        "required": True,
                        "description": "Title"
                    },
                    "charset": {
                        "type": "string",
                        "required": False,
                        "description": "Charset. Ex: UTF8"
                    },
                    "metadata": {
                        "type": "string",
                        "required": True,
                        "description": """Metadata json. Ex: '{"campana": "xxx", "lote": "111", "producto": "Soja"}'"""
                    },                    
                    "permissions": {
                        "type": "string",
                        "required": False,
                        "description": """Permissions. Ex: '[
                        {"attribute": "MASA_1", "mapping": "MASA_HUMEDO", "magnitude": "kg"}, 
                        {"attribute":"MASA_2", "mapping": "MASA_SECO", "magnitude": "kg"}]'
                        """
                    },
                    "abstract": {
                        "type": "string",
                        "required": False,
                        "description": "Abstract"
                    },
                    "keywords": {
                        "type": "string",
                        "required": False,
                        "description": """Keywords json list. Ex: {"users":{},"groups":{}}"""
                    }
                }
            }
        ]        

        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = GeoNodeAuthorization()

        queryset = Layer.objects.all().distinct().order_by('-date')
        resource_name = 'layers'
        excludes = ['csw_anytext', 'metadata_xml', 'layer_type']
        allowed_methods = ['get','post', 'put']

        filtering = {'title': ALL,
                 'keywords': ALL_WITH_RELATIONS,
                 'category': ALL_WITH_RELATIONS,
                 'owner': ALL_WITH_RELATIONS,
                 'creator': ALL_WITH_RELATIONS,
                 'layer_type': ALL_WITH_RELATIONS,
                 'date': ALL,
                 }

        post_query_filtering = {
            'is_public': lambda vals: lambda res: res.is_public() in map(str2bool,vals)
        }

    def prepend_urls(self):
        urls = [
            url(
                r"^(?P<resource_name>%s)/(?P<resource_id>\d+)/table%s$" % (
                    self._meta.resource_name, trailing_slash()
                ),
                self.wrap_view('table'), 
                name="api_layer_table"
            )           
        ]

        return urls

    def table(self, request, resource_id, **kwargs):
        '''query the table.'''

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        layer = Layer.objects.get(id=resource_id)

        cursor = connections['datastore'].cursor()
        fields = [a.attribute for a in Layer.objects.get(id=resource_id).attribute_set.all() if a.attribute.lower() != 'the_geom']

        # FIXME: hacer seguro
        cursor.execute(
            'select %s from %s  order by "%s" limit %s offset %s;' % (
                ', '.join(['"%s"' % f for f in fields]),
                layer.name, 
                fields[0],
                request.GET.get('limit', '50'),
                request.GET.get('offset', '0')
            ) 
        )

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(fields, row)))

        to_be_serialized = self.alter_list_data_to_serialize(
            request,
            results
        )
        return self.create_response(request, to_be_serialized)

    def _set_default_metadata(self, bundle, layer, update=False):
        now = dt.datetime.now()

        bundle.request.POST['charset'] = bundle.request.POST.get(
            'charset', layer.charset if update else 'utf-8' 
        )
        bundle.request.POST['rating'] = bundle.request.POST.get(
            'rating', layer.rating if update else '0'
        )
        bundle.request.POST['language'] = bundle.request.POST.get(
            'language', layer.language if update else 'eng'
        )
        bundle.request.POST['title'] = bundle.request.POST.get(
            'title', layer.title if update else layer.title
        )
        bundle.request.POST['date_type'] = bundle.request.POST.get(
            'date_type', layer.date_type if update else 'publication'
        )
        bundle.request.POST['owner'] = bundle.request.POST.get(
            'owner', bundle.request.user)

        bundle.request.POST['supplemental_information'] = bundle.request.POST.get(
            'supplemental_information', layer.supplemental_information if update else 'no info.'
        )

        date_str = bundle.request.POST.get('date')
        if date_str:
            date = dt.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            date_part = date.strftime("%Y-%m-%d")
            time_part = date.strftime("%H:%M:%S")
        else:
            if update:
                date_part = layer.date.strftime("%Y-%m-%d")
                time_part = layer.date.strftime("%H:%M:%S")                
            else:
                date_part = now.strftime("%Y-%m-%d")
                time_part = now.strftime("%H:%M:%S")
        bundle.request.POST['date_0'] = date_part
        bundle.request.POST['date_1'] = time_part

        form = LayerForm(bundle.request.POST, instance=layer)
        if form.is_valid():
            form.save()
        else:
            raise BadRequest('Error metadata: %s' % json.dumps(form.errors))

    def _create_layer(self, bundle):
        try:
            layer_type = LayerType.objects.get(
                name=bundle.request.POST.get('layer_type', 'default')
            )
            bundle.request.POST['layer_type'] = layer_type.id
            result = json.loads(layer_upload(bundle.request).content)
        except Exception, e:
            raise BadRequest('Error uploading layer: %s' % unicode(e))

        if result['success']:
            return Layer.objects.get(id=result['layer_id'])
        else:
            raise BadRequest(result['errors'])

    def _set_attributes(self, bundle, layer):

        attrs = json.loads(bundle.data.get('attributes', '{}'))
        if not attrs:
            raise BadRequest('Attributes mapping required')

        mapping = {a['attribute']: {'mapping': a['mapping'], 'magnitude': a['magnitude']} for a in attrs}

        for attr in layer.attribute_set.filter(attribute__in=mapping.keys()):
            attr.field = str(
                AttributeType.objects.get(
                    layer_type=layer.layer_type, 
                    name=mapping[attr.attribute]['mapping']
                ).id
            )
            attr.magnitude = mapping[attr.attribute]['magnitude']
            attr.save()

        layer.update_attributes()
        layer.metadata_edited = True
        layer.save()

    def _set_metadata(self, bundle, layer):

        class LayerMetadataForm(BaseDynamicEntityForm):

            def __init__(self, data=None, *args, **kwargs):
                super(LayerMetadataForm, self).__init__(data, *args, **kwargs)
                meta_fields = [
                    a.slug for a in layer.eav.get_all_attributes().filter(
                        layer_metadata_type_attribute__in=layer.layer_type.metadatatype_set.all()
                    )
                ]
                for f in self.fields.keys():
                    if f not in meta_fields:
                        del self.fields[f] 
            
            class Meta:
                model = Layer

            def clean(self):
                cleaned_data = super(LayerMetadataForm, self).clean()
                calc_title = self.instance.layer_type.calculated_title
                if calc_title is not None:
                    try:
                        cleaned_data['title'] = calc_title % cleaned_data
                    except: pass

                calc_abstract = self.instance.layer_type.calculated_abstract
                if calc_abstract is not None:
                    try:
                        cleaned_data['abstract'] = calc_abstract % cleaned_data
                    except: pass 
                return cleaned_data
                

        if bundle.request.POST.get('metadata'):
            bundle.request.POST.update(json.loads(bundle.request.POST.get('metadata')))
            layer_form = LayerMetadataForm(bundle.request.POST, instance=layer)

            if layer_form.is_valid():
                layer_form.save()
            else:
                raise BadRequest('Error metadata: %s' % json.dumps(layer_form.errors))

    def dehydate(self, bundle):
        bundle = super(CommonModelApi, self).dehydrate(bundle)
        return remove_internationalization_fields(bundle)

    def obj_update(self, bundle, pk, **kwargs):
        '''Update metadata.

        curl 
        --dump-header - 
        -H "Content-Type: application/json" 
        -X PUT --data 'metadata={"campana": "xxx", "lote": "111", "producto": "Soja"}&purpose=foo'
        'http://localhost:8000/api/layers/4/?username=admin&api_key=xxx'
        '''

        bundle.request.POST._mutable = True
        layer = Layer.objects.get(id=pk)
        self._set_default_metadata(bundle, layer, update=True)
        if not layer.layer_type.is_default:
            self._set_metadata(bundle, layer)

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
        -F keywords='foo,bar'
        -F 'permissions={"users":{},"groups":{}}' 
        -F 'attributes=[
            {"attribute": "MASA_1", "mapping": "MASA_HUMEDO", "magnitude": "kg"}, 
            {"attribute":"MASA_2", "mapping": "MASA_SECO", "magnitude": "kg"}]'
        -F 'metadata={"campana": "xxx", "lote": "111", "producto": "Soja"}'
        'http://localhost:8000/api/layers/?username=admin&api_key=xxx'


        Ejemplo ppciones de permisos:
        
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }
        """
        layer = self._create_layer(bundle)
        self._set_default_metadata(bundle, layer)

        if layer.layer_type.is_default:
            return layer

        try:
            with transaction.atomic(using="default"):
                self._set_attributes(bundle, layer)
                self._set_metadata(bundle, layer)
        except Exception as e:
            logging.exception('Error trying to map fields: %s' % unicode(e))
            layer.delete()
            raise BadRequest('Error trying to map fields: %s' % unicode(e))

        return layer


class MapResource(CommonModelApi):

    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.distinct().order_by('-date')
        resource_name = 'maps'


class DocumentResource(CommonModelApi):

    class Meta(CommonMetaApi):
        filtering = {
            'title': ALL,
            'keywords': ALL_WITH_RELATIONS,
            'category': ALL_WITH_RELATIONS,
            'owner': ALL_WITH_RELATIONS,
            'date': ALL,
            'doc_type': ALL,
            'creator': ALL_WITH_RELATIONS
            }
        queryset = Document.objects.distinct().order_by('-date')
        resource_name = 'documents'
        post_query_filtering = {
            'is_public': lambda vals: lambda res: res.is_public() in map(str2bool,vals)
        }        

class TabularTypeResource(ModelResource):

    class Meta:
        resource_name = 'tabular_types'
        queryset = TabularType.objects.all()
        fields = ['name', 'description', 'fill_metadata']
        filtering = {
            'name': ALL,
        }


class TabularAttributeResource(ModelResource):

    tabular = fields.ToOneField('geonode.api.resourcebase_api.TabularResource', 'tabular')

    class Meta(CommonMetaApi):
        extra_actions = []
        resource_name = 'tabular_attributes'
        queryset = TabularAttribute.objects.all()
        fields = ['attribute', 'attribute_label', 'description']
        filtering = {
            'tabular': ALL_WITH_RELATIONS,
        }


class TabularResource(MultipartResource, CommonModelApi):

    """Tabular API"""

    tabular_type = fields.ForeignKey(TabularTypeResource, 'tabular_type', full=True, null=True)
    attributes = fields.ToManyField(TabularAttributeResource, 'tabular_attribute_set', full=True)

    # def build_schema(self): 
    #     schema = super(ModelResource, self).build_schema() 
    #     schema["fields"]["foo"] = {"blank": False, 
    #                                         "default": "No default provided.", 
    #                                         "help_text": "Integer data. Ex: 2673", 
    #                                         "nullable": False, 
    #                                         "readonly": False, 
    #                                         "type": "integer", 
    #                                         "unique": True 
    #                                         } 
    #     return schema

    class Meta(CommonMetaApi):
        extra_actions = extra_actions + [
            {
                "name": '',
                "http_method": "POST",
                "resource_type": "list",
                "summary": "Create a new table",
                "fields": {
                    "doc_file": {
                        "type": "file",
                        "required": True,
                        "description": "Table to append"
                    },                
                    "title": {
                        "type": "string",
                        "required": True,
                        "description": "Title"
                    },
                    "permissions": {
                        "type": "string",
                        "required": True,
                        "description": """Permissions. Ex: '{"users":{},"groups":{},"apps":{}}'"""
                    },
                    "charset": {
                        "type": "string",
                        "required": False,
                        "description": "Charset"
                    },
                    "tabular_type": {
                        "type": "string",
                        "required": False,
                        "description": "Table type"
                    },                    
                    "delimiter": {
                        "type": "string",
                        "required": False,
                        "description": "Column table delimiter"
                    },
                    "quotechar": {
                        "type": "string",
                        "required": False,
                        "description": "quoting"
                    },
                    "has_header": {
                        "type": "string",
                        "required": False,
                        "description": "Define if table has header. Omite if not has header."
                    }
                }
            },                
            {
                "name": 'append',
                "http_method": "POST",
                "resource_type": "",
                "summary": "Append data to this table",
                "fields": {
                    "doc_file": {
                        "type": "file",
                        "required": True,
                        "description": "Table to append"
                    }
                }
            },        
            {
                "name": "sql",
                "http_method": "GET",
                "resource_type": "",
                "summary": "Search in a SQL way",
                "fields": {
                    "q": {
                        "type": "string",
                        "required": False,
                        "description": "SQL query"
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "description": "Limit"
                    },
                    "offset": {
                        "type": "integer",
                        "required": False,
                        "description": "Offset"
                    }
                }
            }
        ]
        filtering = {
            'title': ALL,
            'keywords': ALL_WITH_RELATIONS,
            'category': ALL_WITH_RELATIONS,
            'owner': ALL_WITH_RELATIONS,
            'date': ALL,
            'doc_type': ALL,
            'creator': ALL_WITH_RELATIONS,
            'tabular_type': ALL_WITH_RELATIONS,
            }
        queryset = Tabular.objects.distinct().order_by('-date')
        resource_name = 'tabular'
        allowed_methods = ['get','post']
        post_query_filtering = {
            'is_public': lambda vals: lambda res: res.is_public() in map(str2bool,vals)
        }

    def prepend_urls(self):
        urls = [
            url(
                r"^(?P<resource_name>%s)/(?P<resource_id>\d+)/sql%s$" % (
                    self._meta.resource_name, trailing_slash()
                ),
                self.wrap_view('sql'), 
                name="api_tabular_sql"
            ),
            url(
                r"^(?P<resource_name>%s)/(?P<resource_id>\d+)/append%s$" % (
                    self._meta.resource_name, trailing_slash()
                ),
                self.wrap_view('append'), 
                name="api_tabular_append"
            )            
        ]

        return urls


    def append(self, request, resource_id, **kwargs):
        '''
        Append a table to an existing table

        curl 
        --dump-header - 
        -F doc_file=@Allianz-Visbroker.xls   
        'http://localhost:8000/api/tabular/100/append/?username=admin&api_key=1e7ee138294d929505aa0057ac243daaf374ee38'

        '''

        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        form = DocumentReplaceForm(
            request.POST,
            request.FILES,
            instance=Tabular.objects.get(id=resource_id)
        )
        if form.is_valid():
            obj = form.save()
            obj.append()
            return HttpNoContent()
        else:
            logging.exception('Error trying load table: %s' % unicode(form.errors))
            raise BadRequest('Error trying load table: %s' % unicode(form.errors))

    def sql(self, request, resource_id, **kwargs):
        '''query the table.

        curl 
        --dump-header -  
        -H "Content-Type: application/json" 
        -X  PUT 
        --data '{"new_owner_id": 25, "app_id": 14}' 
        'http://localhost:8000/api/base/79/transfer_owner/?username=foo&api_key=c003062347b82a8cdd4014e9f8edb5c2aef63c7a'
        '''

        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        cursor = connections['datastore'].cursor()
        fields = [a.attribute for a in Tabular.objects.get(id=resource_id).tabular_attribute_set.all()]

        # FIXME: hacer seguro
        cursor.execute(
            'select %s from tabular_%s where %s order by "%s" limit %s offset %s;' % (
                ', '.join(['"%s"' % f for f in fields]),
                resource_id, 
                request.GET.get('q', '1=1'),
                fields[0],
                request.GET.get('limit', '50'),
                request.GET.get('offset', '0')
            ) 
        )

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(fields, row)))

        to_be_serialized = self.alter_list_data_to_serialize(
            request,
            results
        )
        return self.create_response(request, to_be_serialized)

    def obj_create(self, bundle, request=None, **kwargs):
        """
        <QueryDict: {u'resource': [u''], u'title': [u'C:\\fakepath\\Allianz-Visbroker.xls'], 
        u'charset': [u''], u'delimiter': [u''], u'tabular_type': [u''], u'quotechar': [u''], 
        u'csrfmiddlewaretoken': [u'2EozhP87wSPOFFSAF475O86O77oe1Ozn'], u'doc_url': [u''], 
        u'has_header': [u'on'], u'permissions': [u'{"users":{},"groups":{}}']}>
        
        <MultiValueDict: {u'doc_file': [<InMemoryUploadedFile: Allianz-Visbroker.xls (application/vnd.ms-excel)>]}>


        Ejemplo simple upload:

        curl 
        --dump-header - 
        -F doc_file=@Allianz-Visbroker.xls 
        -F title='xxx' 
        -F charset='' 
        -F delimiter='' 
        -F quotechar='' 
        -F has_header='true' 
        -F tabular_type='' 
        -F permissions='{"users":{},"groups":{},"apps":{}}'   
        'http://localhost:8000/api/tabular/?username=admin&api_key=1e7ee138294d929505aa0057ac243daaf374ee38'

        Ejemplo opciones de permisos:
        
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }



        """

        form = DocumentCreateForm(bundle.request.POST, bundle.request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = bundle.request.user
            obj.save()
            obj.set_permissions(form.cleaned_data['permissions'])
            # XXX:
            # se guarda de nuevo porque se borran los permisos
            # y se deben dar permisos a las aplicaciones de nuevo
            obj.save()
            return obj
        
        logging.exception('Error trying load table: %s' % unicode(form.errors))
        raise BadRequest('Error trying load table: %s' % unicode(form.errors))


class InternalLinkResource(ModelResource):
    class Meta:
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = InternalLinkAuthorization()
        queryset = InternalLink.objects.all()
        resource_name = 'internal_links'
        allowed_methods = ['get','post','delete']
        filtering = {
            'name': ALL,
        }
        fields = ['name','source','target']

    source = fields.ToOneField(ResourceBaseResource, 'source')
    target = fields.ToOneField(ResourceBaseResource, 'target')

