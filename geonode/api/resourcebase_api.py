import re, json
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings

from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils import trailing_slash

from guardian.shortcuts import get_objects_for_user

from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404

from tastypie.utils.mime import build_content_type
from tastypie.http import HttpNoContent, HttpBadRequest
from tastypie.exceptions import Unauthorized

if settings.HAYSTACK_SEARCH:
    from haystack.query import SearchQuerySet  # noqa

from geonode.people.models import Profile
from geonode.apps.models import App
from geonode.layers.models import Layer, Attribute, LayerType
from geonode.layers.views import layer_upload
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase, TopicCategory, ResourceBaseLink
from .authorization import GeoNodeAuthorization

from .api import TagResource, ProfileResource, TopicCategoryResource, \
    FILTER_TYPES, AppResource

LAYER_SUBTYPES = {
    'vector': 'dataStore',
    'raster': 'coverageStore',
    'remote': 'remoteStore',
}
FILTER_TYPES.update(LAYER_SUBTYPES)


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


class CommonMetaApi:
    authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
    authorization = GeoNodeAuthorization()
    allowed_methods = ['get']
    filtering = {'title': ALL,
                 'keywords': ALL_WITH_RELATIONS,
                 'category': ALL_WITH_RELATIONS,
                 'owner': ALL_WITH_RELATIONS,
                 'creator': ALL_WITH_RELATIONS,
                 'app': ALL_WITH_RELATIONS,
                 'date': ALL,
                 }
    ordering = ['date', 'title', 'popular_count']
    max_limit = None


class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    category = fields.ToOneField(
        TopicCategoryResource,
        'category',
        null=True,
        full=True)
    owner = fields.ToOneField(ProfileResource, 'owner', full=True)
    creator = fields.ToOneField(ProfileResource, 'creator', full=True, null=True)
    app = fields.ToOneField(AppResource, 'app', full=True, null=True)

    def build_filters(self, filters={}):
        orm_filters = super(CommonModelApi, self).build_filters(filters)
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

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        # impossible.

        base_bundle = self.build_bundle(request=request)
        objects = self.obj_get_list(
            bundle=base_bundle,
            **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(
            request.GET,
            sorted_objects,
            resource_uri=self.get_resource_uri(),
            limit=self._meta.limit,
            max_limit=self._meta.max_limit,
            collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        to_be_serialized = self.alter_list_data_to_serialize(
            request,
            to_be_serialized)
        return self.create_response(request, to_be_serialized)

    def create_response(
            self,
            request,
            data,
            response_class=HttpResponse,
            **response_kwargs):
        """
        Extracts the common "which-format/serialize/return-response" cycle.

        Mostly a useful shortcut/hook.
        """
        VALUES = [
            # fields in the db
            'creator',
            'app',

            'id',
            'uuid',
            'title',
            'abstract',
            'csw_wkt_geometry',
            'csw_type',
            'distribution_description',
            'distribution_url',
            'owner_id',
            'share_count',
            'popular_count',
            'date',
            'srid',
            'category',
            'supplemental_information',
            'thumbnail_url',
            'detail_url',
            'rating',
            'metadata_edited',
            'palenque_type_id',
        ]
        if isinstance(
                data,
                dict) and 'objects' in data and not isinstance(
                data['objects'],
                list):
            objects = data['objects']
            data['objects'] = list(data['objects'].values(*VALUES))
            # TODO: Improve
            for obj in data['objects']:
                if obj['palenque_type_id'] is not None:
                   obj['layer_type'] = LayerType.objects.get(id=obj['palenque_type_id']).name
                obj.pop('palenque_type_id')
                if obj['category'] is not None: 
                    obj['category_description'] = TopicCategory.objects.get(id=obj['category']).gn_description

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(
            content=serialized,
            content_type=build_content_type(desired_format),
            **response_kwargs)

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


class FeaturedResourceBaseResource(CommonModelApi):

    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.filter(featured=True).order_by('-date')
        resource_name = 'featured'

class ResourceLinkForwardResource(ModelResource):

    link_type = fields.CharField(attribute='link_type')
    target_uri = fields.ToOneField('geonode.api.resourcebase_api.LayerResource','target')

    class Meta:
        queryset = ResourceBaseLink.objects.all()

    def dehydrate(self, bundle):
        bundle.data.pop('resource_uri')
        bundle.data.pop('id')
        bundle.data['target_id'] = bundle.obj.target.id
        return bundle

class ResourceLinkBackwardResource(ModelResource):

    link_type = fields.CharField(attribute='link_type')
    target = fields.ToOneField('geonode.api.resourcebase_api.LayerResource','source')

    class Meta:
        queryset = ResourceBaseLink.objects.all()

    def dehydrate(self, bundle):
        bundle.data.pop('resource_uri')
        bundle.data.pop('id')
        bundle.data['target_id'] = bundle.obj.source.id
        return bundle


class LayerResource(MultipartResource, CommonModelApi):

    """Layer API"""

    resourcelinks_forward = fields.ToManyField(ResourceLinkForwardResource, 'resourcelinks_forward', full=True, null=True)
    resourcelinks_backward = fields.ToManyField(ResourceLinkBackwardResource, 'resourcelinks_backward', full=True, null=True)

    class Meta(CommonMetaApi):
        queryset = Layer.objects.all().distinct().order_by('-date')
        resource_name = 'layers'
        excludes = ['csw_anytext', 'metadata_xml']
        allowed_methods = ['get', 'post']
        filtering = {'title': ALL,
                 'keywords': ALL_WITH_RELATIONS,
                 'category': ALL_WITH_RELATIONS,
                 'owner': ALL_WITH_RELATIONS,
                 'creator': ALL_WITH_RELATIONS,
                 'app': ALL_WITH_RELATIONS,
                 'layer_type': ALL,
                 'date': ALL,
                 }

    def build_filters(self, filters={}):
        """adds filtering by group functionality"""

        orm_filters = super(LayerResource, self).build_filters(filters)

        filters = dict((k.replace('layer_type','palenque_type__name'),v) for k,v in filters.items())
        return orm_filters


    def obj_create(self, bundle, request=None, **kwargs):
        """
        Ejemplo simple upload:

        curl 
        --dump-header - 
        -F base_file=@lvVK4NtGvJ.shp 
        -F charset=UTF-8
        -F layer_title='monitor test'
        -F abstract='monitor test'
        -F 'permissions={"users":{},"groups":{}}' 
        -F 'attributes=[
            {"attribute": "MASA_1", "field": "MASA_HUMEDO", "magnitude": "kg"}, 
            {"attribute":"MASA_2", "field": "MASA_SECO", "magnitude": "kg"}]'
        'http://localhost:8000/api/layers/?username=admin&api_key=xxx'


        Ejemplo ppciones de permisos:
        {
            "users":{"AnonymousUser":["view_resourcebase"], "tinkamako":["change_resourcebase"] }, 
            "groups":{"foo":["change_resourcebase_permissions"] } 
        }
        """

        # creates layer
        try:
            result = json.loads(layer_upload(bundle.request).content)
        except Exception, e:
            return HttpBadRequest('Error uploading monitor')

        if result['success']:
            layer = Layer.objects.get(id=result['layer_id'])
        else:
            return HttpBadRequest(result['errors'])


        # attrs = json.loads(bundle.data['attributes'])
        # if not attrs:
        #     raise BadRequest('Attributes mapping required')

        # try:
        #     mapping = {a['attribute']: {'field': a['field'], 'magnitude': a['magnitude']} for a in attrs}

        #     # FIXME: validar campos requeridos

        #     for attr in layer.attribute_set.filter(attribute__in=mapping.keys()):
        #         attr.field = mapping[attr.attribute]['field']
        #         attr.magnitude = mapping[attr.attribute]['magnitude']
        #         attr.save()

        #     _rename_fields(layer)
        #     _precalculate_yield(layer)

        # except Exception, e:
        #     layer.delete()
        #     raise BadRequest('Error trying to map fields')

        return layer


class MapResource(CommonModelApi):

    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.distinct().order_by('-date')
        resource_name = 'maps'


class DocumentResource(CommonModelApi):

    """Maps API"""

    class Meta(CommonMetaApi):
        filtering = {
            'title': ALL,
            'keywords': ALL_WITH_RELATIONS,
            'category': ALL_WITH_RELATIONS,
            'owner': ALL_WITH_RELATIONS,
            'date': ALL,
            'doc_type': ALL,
            }
        queryset = Document.objects.distinct().order_by('-date')
        resource_name = 'documents'
