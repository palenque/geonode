from django.conf.urls import url
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from avatar.templatetags.avatar_tags import avatar_url
from guardian.shortcuts import get_objects_for_user
import eav.models

from geonode.base.models import TopicCategory
from geonode.layers.models import Layer, LayerType
from geonode.tabular.models import TabularType
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.apps.models import App, AppCategory

from taggit.models import Tag

from tastypie import fields
from tastypie.resources import ModelResource, Resource
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash

FILTER_TYPES = {
    'layer': Layer,
    'map': Map,
    'document': Document
}

def remove_internationalization_fields(bundle):
    bundle.data = dict(filter(lambda (k,v):len(k)<3 or k[-3] != '_', bundle.data.items()))
    return bundle

class PostQueryFilteringMixin(object):
    def build_post_query_filters(self, filters):
        orm_filters = {}
        if hasattr(self.Meta, 'post_query_filtering'):
            for flt in self.Meta.post_query_filtering:
                if flt in filters:
                    orm_filters[flt] = filters.pop(flt)
        return orm_filters

    def process_post_query_filters(self, request, applicable_filters):
        request.post_query_filters = {}
        if hasattr(self.Meta, 'post_query_filtering'):
            for flt in self.Meta.post_query_filtering:
                if flt in applicable_filters:
                    request.post_query_filters[flt] = applicable_filters.pop(flt)

    def apply_post_query_filters(self, objects, bundle):
        if hasattr(self.Meta, 'post_query_filtering'):
            for name,vals in bundle.request.post_query_filters.items():
                objects = filter(self.Meta.post_query_filtering[name](vals), objects)
        return objects

class TypeFilteredResource(ModelResource):

    """ Common resource used to apply faceting to categories and keywords
    based on the type passed as query parameter in the form
    type:layer/map/document"""
    count = fields.IntegerField()

    type_filter = None

    def dehydrate(self, bundle):
        return remove_internationalization_fields(bundle)

    def dehydrate_count(self, bundle):
        raise Exception('dehydrate_count not implemented in the child class')

    def build_filters(self, filters={}):

        orm_filters = super(TypeFilteredResource, self).build_filters(filters)

        if 'type' in filters and filters['type'] in FILTER_TYPES.keys():
            self.type_filter = FILTER_TYPES[filters['type']]
        else:
            self.type_filter = None
        return orm_filters


class TagResource(TypeFilteredResource):

    """Tags api"""

    def dehydrate_count(self, bundle):
        count = 0
        if settings.SKIP_PERMS_FILTER:
            if self.type_filter:
                ctype = ContentType.objects.get_for_model(self.type_filter)
                count = bundle.obj.taggit_taggeditem_items.filter(
                    content_type=ctype).count()
            else:
                count = bundle.obj.taggit_taggeditem_items.count()
        else:
            resources = get_objects_for_user(
                bundle.request.user,
                'base.view_resourcebase').values_list(
                'id',
                flat=True)
            if self.type_filter:
                ctype = ContentType.objects.get_for_model(self.type_filter)
                count = bundle.obj.taggit_taggeditem_items.filter(content_type=ctype).filter(object_id__in=resources)\
                    .count()
            else:
                count = bundle.obj.taggit_taggeditem_items.filter(
                    object_id__in=resources).count()

        return count

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'keywords'
        allowed_methods = ['get']
        filtering = {
            'slug': ALL,
        }


class TopicCategoryResource(TypeFilteredResource):

    """Category api"""

    def dehydrate_count(self, bundle):
        if settings.SKIP_PERMS_FILTER:
            return bundle.obj.resourcebase_set.instance_of(self.type_filter).count() if \
                self.type_filter else bundle.obj.resourcebase_set.all().count()
        else:
            resources = bundle.obj.resourcebase_set.instance_of(self.type_filter) if \
                self.type_filter else bundle.obj.resourcebase_set.all()
            permitted = get_objects_for_user(
                bundle.request.user,
                'base.view_resourcebase').values_list(
                'id',
                flat=True)
            return resources.filter(id__in=permitted).count()

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get']
        filtering = {
            'identifier': ALL,
        }

class AppCategoryResource(TypeFilteredResource):

    class Meta:
        queryset = AppCategory.objects.all()
        resource_name = 'app_categories'
        allowed_methods = ['get']
        filtering = {
            'identifier': ALL,
        }

    def dehydrate_count(self, bundle):
        return bundle.obj.app_set.count()


class GroupResource(ModelResource):

    """Groups api"""

    detail_url = fields.CharField()
    member_count = fields.IntegerField()
    manager_count = fields.IntegerField()

    def dehydrate_member_count(self, bundle):
        return bundle.obj.member_queryset().count()

    def dehydrate_manager_count(self, bundle):
        return bundle.obj.get_managers().count()

    def dehydrate_detail_url(self, bundle):
        return reverse('group_detail', args=[bundle.obj.slug])

    class Meta:
        queryset = GroupProfile.objects.all()
        resource_name = 'groups'
        allowed_methods = ['get']
        filtering = {
            'name': ALL
        }
        ordering = ['title', 'last_modified']


class AppResource(ModelResource, PostQueryFilteringMixin):

    """App api"""

    class Meta:
        queryset = App.objects.all()
        resource_name = 'apps'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
            'category': ALL_WITH_RELATIONS,
            'developer': ALL,
        }
        ordering = ['title', 'last_modified']
        post_query_filtering = {
            'developer': lambda vals: lambda app: app.get_managers()[0].username in vals
        }

    detail_url = fields.CharField()
    member_count = fields.IntegerField()
    manager_count = fields.IntegerField()
    developer = fields.CharField()
    category = fields.ToOneField('geonode.api.api.AppCategoryResource', 'category', null=True)
    
    def dehydrate_member_count(self, bundle):
        return bundle.obj.member_queryset().filter(role='member').count()

    def dehydrate_manager_count(self, bundle):
        return bundle.obj.get_managers().count()

    def dehydrate_detail_url(self, bundle):
        return reverse('app_detail', args=[bundle.obj.slug])

    def dehydrate_developer(self, bundle):
        return bundle.obj.get_managers()[0].full_name
    
    def dehydrate_detail_url(self, bundle):
        return reverse('app_detail', args=[bundle.obj.slug])

    def build_filters(self, filters={}):
        """adds filtering by group functionality"""

        orm_filters = self.build_post_query_filters(filters)
        orm_filters.update(super(AppResource, self).build_filters(filters))

        if 'member' in filters:
            orm_filters['member'] = filters['member']

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """filter by group if applicable by group functionality"""

        self.process_post_query_filters(request, applicable_filters)
        member = applicable_filters.pop('member', None)
        developer = applicable_filters.pop('developer', None)

        semi_filtered = super(
            AppResource,
            self).apply_filters(
            request,
            applicable_filters)

        if member is not None:
            semi_filtered = semi_filtered.filter(
                appmember__user__username=member, 
                appmember__role='member'
            )

        if developer is not None:
            semi_filtered = semi_filtered.filter(
                appmember__user__username=developer, 
                appmember__role='manager'
            )

        return semi_filtered

    def obj_get_list(self, **kwargs):
        objects = super(AppResource, self).obj_get_list(**kwargs)
        bundle = kwargs['bundle']
        objects = self.apply_post_query_filters(objects, bundle)
        return objects


class ProfileResource(ModelResource):

    """Profile api"""
    avatar_100 = fields.CharField(null=True)
    profile_detail_url = fields.CharField()
    email = fields.CharField(default='')
    layers_count = fields.IntegerField(default=0)
    maps_count = fields.IntegerField(default=0)
    documents_count = fields.IntegerField(default=0)
    current_user = fields.BooleanField(default=False)
    activity_stream_url = fields.CharField(null=True)
    full_name = fields.CharField(null=True)

    def build_filters(self, filters={}):
        """adds filtering by group functionality"""
        
        orm_filters = super(ProfileResource, self).build_filters(filters)

        for flt in ['group','app']:
            if flt in filters:
                orm_filters[flt] = filters[flt]

        orm_filters['created_resource'] = dict(filter(lambda (k,v):k.startswith('created_resource'),filters.items()))

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """filter by group if applicable by group functionality"""

        group = applicable_filters.pop('group', None)
        app = applicable_filters.pop('app', None)
        created_resource = applicable_filters.pop('created_resource', {})

        semi_filtered = super(
            ProfileResource,
            self).apply_filters(
            request,
            applicable_filters)

        if group is not None:
            semi_filtered = semi_filtered.filter(
                groupmember__group__slug=group)
        
        if app is not None:
            semi_filtered = semi_filtered.filter(
                appmember__app__slug=app,
                appmember__role='member')

        if len(created_resource) > 0:
            semi_filtered = semi_filtered.filter(**created_resource).distinct()

        return semi_filtered

    def dehydrate_email(self, bundle):
        email = ''
        if bundle.request.user.is_authenticated():
            email = bundle.obj.email
        return email

    def dehydrate_full_name(self, bundle):
        return bundle.obj.full_name

    def dehydrate_layers_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Layer).distinct().count()

    def dehydrate_maps_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Map).distinct().count()

    def dehydrate_documents_count(self, bundle):
        return bundle.obj.resourcebase_set.instance_of(Document).distinct().count()

    def dehydrate_avatar_100(self, bundle):
        return avatar_url(bundle.obj, 100)

    def dehydrate_profile_detail_url(self, bundle):
        return bundle.obj.get_absolute_url()

    def dehydrate_current_user(self, bundle):
        return bundle.request.user.username == bundle.obj.username

    def dehydrate_activity_stream_url(self, bundle):
        return reverse(
            'actstream_actor',
            kwargs={
                'content_type_id': ContentType.objects.get_for_model(
                    bundle.obj).pk,
                'object_id': bundle.obj.pk})

    def prepend_urls(self):
        if settings.HAYSTACK_SEARCH:
            return [
                url(r"^(?P<resource_name>%s)/search%s$" % (
                    self._meta.resource_name, trailing_slash()
                    ),
                    self.wrap_view('get_search'), name="api_get_search"),
            ]
        else:
            return []

    class Meta:
        queryset = get_user_model().objects.exclude(username='AnonymousUser')
        resource_name = 'profiles'
        allowed_methods = ['get']
        ordering = ['username', 'date_joined']
        excludes = ['is_staff', 'password', 'is_superuser',
                    'is_active', 'last_login']

        filtering = {
            'username': ALL,
            'profile': ALL
        }

class LayerTypeResource(TypeFilteredResource):

    """Layer Type api"""

    def dehydrate_count(self, bundle):
        resources = bundle.obj.layer_set.all()
        permitted = get_objects_for_user(
            bundle.request.user,
            'base.view_resourcebase').values_list(
            'id',
            flat=True)
        return resources.filter(id__in=permitted).count()

    class Meta:
        queryset = LayerType.objects.all()
        resource_name = 'layer_types'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
        }

class TabularTypeResource(TypeFilteredResource):

    """Tabular Type api"""

    def dehydrate_count(self, bundle):
        resources = bundle.obj.tabular_set.all()
        permitted = get_objects_for_user(
            bundle.request.user,
            'base.view_resourcebase').values_list(
            'id',
            flat=True)
        return resources.filter(id__in=permitted).count()

    class Meta:
        queryset = TabularType.objects.all()
        resource_name = 'tabular_types'
        allowed_methods = ['get']
        filtering = {
            'name': ALL,
        }


class EavAttributeResource(ModelResource):

    values = fields.DictField()

    class Meta:
        queryset = eav.models.Attribute.objects.all()
        resource_name = 'eav_attributes'
        filtering = {
            'slug': ALL,
        }

    def dehydrate_values(self, bundle):
        attr = bundle.obj.slug
        resources = get_objects_for_user(
            bundle.request.user,
            'base.view_resourcebase')

        values = eav.models.Value.objects.filter(attribute=bundle.obj).values('value_text').distinct()
        for val in values:
            if val['value_text'] is not None: val['value_text'] = val['value_text'].encode('utf8')
            val['count'] = len([res for res in resources if 
                hasattr(res,'layer') and hasattr(res.layer.eav,attr) and getattr(res.layer.eav,attr) == val['value_text']])
        return list(values)

