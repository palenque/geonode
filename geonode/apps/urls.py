from django.conf.urls import patterns, url
from django.views.generic import TemplateView

# from .views import GroupDetailView, GroupActivityView
from .views import AppDetailView

urlpatterns = patterns('geonode.apps.views',
                       url(r'^$',
                           TemplateView.as_view(template_name='apps/app_list.html'),
                           name="app_list"),                      
                       url(r"^member/(?P<app_id>[-\d+]+)/(?P<username>[^/]*)/$",
                           "member_detail",
                           name="app_member_detail"),                       
                       url(r'^resource/share/(?P<app_id>[-\d]+)$',
                           'resource_share',
                           name="app_resource_share"),                       
                       url(r'^create/$',
                           'app_create',
                           name="app_create"),
                       url(r'^app/(?P<slug>[-\w]+)/$',
                           AppDetailView.as_view(),
                           name='app_detail'),
                       url(r'^app/(?P<slug>[-\w]+)/update/$',
                           'app_update',
                           name='app_update'),
                       # url(r'^app/(?P<slug>[-\w]+)/members/$',
                       #     'app_members',
                       #     name='app_members'),
                       # url(r'^group/(?P<slug>[-\w]+)/invite/$',
                       #     'group_invite',
                       #     name='group_invite'),
                       # url(r'^group/(?P<slug>[-\w]+)/members_add/$',
                       #     'group_members_add',
                       #     name='group_members_add'),
                       url(r'^app/(?P<slug>[-\w]+)/member_remove/(?P<username>.+)$',
                           'app_member_remove',
                           name='app_member_remove'),
                       url(r'^apps/(?P<slug>[-\w]+)/remove/$',
                           'app_remove',
                           name='app_remove'),
                       url(r'^app/(?P<slug>[-\w]+)/join/$',
                           'app_join',
                           name='app_join'),
                       # url(r'^group/[-\w]+/invite/(?P<token>[\w]{40})/$',
                       #     'group_invite_response',
                       #     name='group_invite_response'),
                       # url(r'^group/(?P<slug>[-\w]+)/activity/$',
                       #     GroupActivityView.as_view(),
                       #     name='group_activity'),
                       )
