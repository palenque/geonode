import json
import markdown

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotAllowed
from django.http import HttpResponse
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView,TemplateView
from django.utils.translation import ugettext_lazy as _

from actstream.models import Action
from guardian.shortcuts import assign_perm, remove_perm


from geonode.base.models import ResourceBase
from geonode.apps.forms import AppForm, AppUpdateForm
from geonode.apps.models import App, AppMember, AppLayerTypePermission
from geonode.people.models import Profile
from geonode.layers.models import Layer, LayerType
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.tabular.models import Tabular, TabularType

@login_required
def app_create(request, is_service=False):
    if request.method == "POST":
        form = AppForm(request.POST, request.FILES, is_service=is_service)
        if form.is_valid():
            app = form.save(commit=False)
            app.save()
            form.save_m2m()
            app.join(request.user, role="manager")
            
            app_user = Profile(username=app.slug[:25], profile='application', organization=app.title)
            app_user.save()
            app.join(app_user, role="alter_ego")

            return HttpResponseRedirect(
                reverse("app_detail", args=[app.slug])
            )
    else:
        form = AppForm(is_service=is_service)

    return render_to_response("apps/app_create.html", {
        "form": form,
    }, context_instance=RequestContext(request,{'is_service':is_service}))


@login_required
def app_update(request, slug):
    app = App.objects.get(slug=slug)
    if not app.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()

    context = {
        "group": app 
    }

    if request.method == "POST":
        form = AppUpdateForm(request.POST, request.FILES, instance=app)
        layer_types = {}
        public_layers = []
        for k,v in request.POST.items():
            if k.startswith('layer_type_permissions'):
                layer_types[int(k.split('_')[-1])] = v
            if k.startswith('public_layer'):
                public_layers.append(int(k.split('_')[-1]))

        if form.is_valid():
            app = form.save()
            AppLayerTypePermission.objects.filter(app=app).delete()
            for layer_type_id,perm in layer_types.items():
                if len(perm) == 0: continue
                app.applayertypepermission_set.add(AppLayerTypePermission(
                    app=app,
                    layer_type_id=layer_type_id,
                    permission=perm))

            app.public_layer_permissions.clear()
            for layer_id in public_layers:
                app.public_layer_permissions.add(Layer.objects.get(id=layer_id))

            return HttpResponseRedirect(
                reverse("app_detail", args=[app.slug]))
    else:
        layer_type_permissions = dict((x.layer_type,x.permission) for x in app.applayertypepermission_set.all())
        layer_type_permissions.update(dict((lt,None) for lt in LayerType.objects.all() 
            if lt not in layer_type_permissions and not lt.is_default))
        context['layer_type_permissions'] = layer_type_permissions
        pl = app.public_layer_permissions.all()
        context['public_layers'] = dict((l, l in pl) 
            for l in Layer.objects.filter(is_public=True).all())
        form = AppForm(instance=app)

    context['form'] = form
    return render_to_response("apps/app_update.html", context,
        context_instance=RequestContext(request))


@login_required
def app_detail(request, slug):
    app = get_object_or_404(App, slug=slug)
    manager = app.get_managers()[0]
    alter_ego = app.get_alter_ego()
    profile = get_object_or_404(Profile, username=request.user.username)
    user_objects = profile.owned_resource.distinct()

    action_list = Action.objects.filter(actor_object_id=alter_ego.id)[:15]

    keywords = app.keyword_list
    keyword_labels = set()
    keyword_labels.update(x.label for x in LayerType.objects.filter(name__in=keywords).all())
    keyword_labels.update(x.label for x in TabularType.objects.filter(name__in=keywords).all())

    context = {}
    context['object'] = app
    context['app_manager'] = manager
    context['app_alter_ego'] = alter_ego
    context['maps'] = app.resources(resource_type='map')
    context['layers'] = app.resources(resource_type='layer')
    context['is_member'] = app.user_is_member(request.user)
    context['is_manager'] = app.user_is_role(request.user, "manager")
    context['description'] = markdown.markdown(app.description)
    context['action_list'] = action_list
    context['keywords'] = keyword_labels
    context['thing'] = _('service') if app.is_service else _('app')
    context['profile'] = profile
    context['object_list'] = user_objects.get_real_instances()
    context['permissions'] = [
        obj.id for obj in user_objects if alter_ego.has_perm('view_resourcebase', obj)
    ]
    return render_to_response("apps/app_detail.html", RequestContext(request, context))

# class AppDetailView(ListView):

#     """
#     Mixes a detail view (the app) with a ListView (the members).
#     """

#     model = get_user_model()
#     template_name = "apps/app_detail.html"
#     paginate_by = None
#     app = None

#     def get_queryset(self):
#         return self.app.member_queryset()

#     def get(self, request, *args, **kwargs):
#         self.app = get_object_or_404(App, slug=kwargs.get('slug'))
#         return super(AppDetailView, self).get(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):

#         manager = self.app.get_managers()[0]
#         alter_ego = self.app.get_alter_ego()
#         profile = get_object_or_404(Profile, username=self.request.user.username)
#         user_objects = profile.owned_resource.distinct()

#         # content_filter = 'all'

#         # if ('content' in self.request.GET):
#         #     content = self.request.GET['content']
#         #     if content != 'all':
#         #         if (content == 'layers'):
#         #             content_filter = 'layers'
#         #             user_objects = user_objects.instance_of(Layer)
#         #         if (content == 'maps'):
#         #             content_filter = 'maps'
#         #             user_objects = user_objects.instance_of(Map)
#         #         if (content == 'documents'):
#         #             content_filter = 'documents'
#         #             user_objects = user_objects.instance_of(Document)
#         #         if (content == 'tabular'):
#         #             content_filter = 'tabular'
#         #             user_objects = user_objects.instance_of(Tabular)

#         # sortby_field = 'date'
#         # if ('sortby' in self.request.GET):
#         #     sortby_field = self.request.GET['sortby']
#         # if sortby_field == 'title':
#         #     user_objects = user_objects.order_by('title')
#         # else:
#         #     user_objects = user_objects.order_by('-date')

#         action_list = Action.objects.filter(target_object_id__in=[x.id for x in user_objects])[:15]

#         context = super(AppDetailView, self).get_context_data(**kwargs)
#         context['object'] = self.app
#         context['app_manager'] = manager
#         context['app_alter_ego'] = alter_ego
#         context['maps'] = self.app.resources(resource_type='map')
#         context['layers'] = self.app.resources(resource_type='layer')
#         context['is_member'] = self.app.user_is_member(self.request.user)
#         context['is_manager'] = self.app.user_is_role(self.request.user, "manager")
#         context['description'] = markdown.markdown(self.app.description)
#         context['action_list'] = action_list

#         context['profile'] = profile
#         # context['sortby_field'] = sortby_field
#         # context['content_filter'] = content_filter
#         context['object_list'] = user_objects.get_real_instances()
#         context['permissions'] = [
#             obj.id for obj in user_objects if alter_ego.has_perm('view_resourcebase', obj)
#         ]

#         # context['can_view'] = self.app.can_view(self.request.user)
#         return context


# def app_members(request, slug):
#     app = get_object_or_404(App, slug=slug)
#     ctx = {}

#     if not app.can_view(request.user):
#         raise Http404()

#     # if app.access in [
#     #         "public-invite",
#     #         "private"] and group.user_is_role(
#     #         request.user,
#     #         "manager"):
#     #     ctx["invite_form"] = GroupInviteForm()

#     if app.user_is_role(request.user, "manager"):
#         ctx["member_form"] = GroupMemberForm()

#     ctx.update({
#         "object": app,
#         "members": app.member_queryset(),
#         "is_member": app.user_is_member(request.user),
#         "is_manager": app.user_is_role(request.user, "manager"),
#     })
#     ctx = RequestContext(request, ctx)
#     return render_to_response("apps/app_members.html", ctx)


# @require_POST
# @login_required
# def group_members_add(request, slug):
#     group = get_object_or_404(GroupProfile, slug=slug)

#     if not group.user_is_role(request.user, role="manager"):
#         return HttpResponseForbidden()

#     form = GroupMemberForm(request.POST)

#     if form.is_valid():
#         role = form.cleaned_data["role"]
#         for user in form.cleaned_data["user_identifiers"]:
#             # dont add them if already a member, just update the role
#             try:
#                 gm = GroupMember.objects.get(user=user, group=group)
#                 gm.role = role
#                 gm.save()
#             except:
#                 gm = GroupMember(user=user, group=group, role=role)
#                 gm.save()
#     return redirect("group_detail", slug=group.slug)


@login_required
def member_detail(request, app_id, username):
    # TODO: validar listado de usuario que tengan la app

    app = get_object_or_404(App, id=app_id)
    manager = app.get_managers()[0]
    profile = get_object_or_404(Profile, username=username)

    if not app.user_is_member(profile):
        raise Http404()

    # combined queryset from each model content type
    user_objects = profile.resourcebase_set.distinct()
    #user_objects = profile.member_set.all()

    content_filter = 'all'

    if ('content' in request.GET):
        content = request.GET['content']
        if content != 'all':
            if (content == 'layers'):
                content_filter = 'layers'
                user_objects = user_objects.instance_of(Layer)
            if (content == 'maps'):
                content_filter = 'maps'
                user_objects = user_objects.instance_of(Map)
            if (content == 'documents'):
                content_filter = 'documents'
                user_objects = user_objects.instance_of(Document)
            if (content == 'tabular'):
                content_filter = 'tabular'
                user_objects = user_objects.instance_of(Tabular)

    # TODO: cambiar query
    # user_objects = profile.resourcebase_set.filter(
    #     id__in=[obj.id for obj in user_objects if manager.has_perm('view_resourcebase', obj)]
    # ).distinct()

    # sortby_field = 'date'
    # if ('sortby' in request.GET):
    #     sortby_field = request.GET['sortby']
    # if sortby_field == 'title':
    #     user_objects = user_objects.order_by('title')
    # else:
    #     user_objects = user_objects.order_by('-date')

    return render(request, "apps/app_member_detail.html", {
        "app": app,
        "profile": profile,
        "sortby_field": sortby_field,
        "content_filter": content_filter,
        "object_list": user_objects.get_real_instances(),
    })


@require_POST
@login_required
def resource_share(request, app_id):
    app  = get_object_or_404(App, id=app_id)
    shared = request.POST.get('shared')
    #manager = app.get_managers()[0]
    alter_ego = app.get_alter_ego()
    resource = get_object_or_404(
        ResourceBase, id=request.POST.get('resource_id')
    )
    
    if app.user_is_role(request.user, role="member"):
        # and resource.get_real_instance().keywords.filter(name__in=app.keyword_list()))
        if shared == 'true':
            assign_perm('view_resourcebase', alter_ego, resource)
        else:
            remove_perm('view_resourcebase', alter_ego, resource)

        return HttpResponse(
            json.dumps(dict(status='ok')), 
            mimetype="application/javascript"
        )

    else:
        return HttpResponse(
            json.dumps(dict(status='error')), 
            mimetype="application/javascript"
        )


@login_required
def app_member_unlink(request, slug, username):

    app = get_object_or_404(App, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if request.method == 'GET':
        return render_to_response(
            "apps/app_member_unlink.html", RequestContext(request, {"app": app}))

    elif request.method == 'POST':

        if request.user == user and app.user_is_member(user):
            app.set_free_resources(user)
            return redirect("app_detail", slug=app.slug)
        return HttpResponseForbidden()


@login_required
def app_member_link(request, slug, username):

    app = get_object_or_404(App, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    read_permissions = []; create_permissions = []
    for perm in app.applayertypepermission_set.all():
        if perm.permission == 'read': read_permissions.append(perm.layer_type)
        elif perm.permission == 'create': create_permissions.append(perm.layer_type)

    # keywords = app.keyword_list
    # keyword_labels = set()
    # keyword_labels.update(x.label for x in LayerType.objects.filter(name__in=keywords).all())
    # keyword_labels.update(x.label for x in TabularType.objects.filter(name__in=keywords).all())

    if request.method == 'GET':
        return render_to_response(
            "apps/app_member_link.html", RequestContext(request, {
                "app": app, 
                "read_permissions": read_permissions,
                "create_permissions": create_permissions,
                # "keywords": keyword_labels,
                "thing": "service" if app.is_service else "app"

            }))

    elif request.method == 'POST':

        if app.user_is_member(user):
            return redirect("app_detail", slug=app.slug)
        else:
            app.join(user, role="member")
            return redirect("app_detail", slug=app.slug)

# @require_POST
# def group_invite(request, slug):
#     group = get_object_or_404(GroupProfile, slug=slug)

#     if not group.can_invite(request.user):
#         raise Http404()

#     form = GroupInviteForm(request.POST)

#     if form.is_valid():
#         for user in form.cleaned_data["invite_user_identifiers"].split("\n"):
#             group.invite(
#                 user,
#                 request.user,
#                 role=form.cleaned_data["invite_role"])

#     return redirect("group_members", slug=group.slug)


# @login_required
# def group_invite_response(request, token):
#     invite = get_object_or_404(GroupInvitation, token=token)
#     ctx = {"invite": invite}

#     if request.user != invite.user:
#         redirect("group_detail", slug=invite.group.slug)

#     if request.method == "POST":
#         if "accept" in request.POST:
#             invite.accept(request.user)

#         if "decline" in request.POST:
#             invite.decline()

#         return redirect("group_detail", slug=invite.group.slug)
#     else:
#         ctx = RequestContext(request, ctx)
#         return render_to_response("groups/group_invite_response.html", ctx)


@login_required
def app_remove(request, slug):
    # FIXME: permitir borrar app solo si no tiene usuarios asociados?
    # FIXME: quitar permisos del owner en recursos compartidos o transferir

    app = get_object_or_404(App, slug=slug)
    if request.method == 'GET':
        return render_to_response(
            "apps/app_remove.html", RequestContext(request, {"group": app}))
    if request.method == 'POST':

        if not app.user_is_role(request.user, role="manager"):
            return HttpResponseForbidden()

        app.delete()
        return HttpResponseRedirect(reverse("app_list"))
    else:
        return HttpResponseNotAllowed()


# class GroupActivityView(ListView):
#     """
#     Returns recent group activity.
#     """

#     template_name = 'groups/activity.html'
#     group = None

#     def get_queryset(self):
#         if not self.group:
#             return None
#         else:
#             members = ([(member.user.id) for member in self.group.member_queryset()])
#             return Action.objects.filter(public=True, actor_object_id__in=members, )[:15]

#     def get(self, request, *args, **kwargs):
#         self.group = None
#         group = get_object_or_404(GroupProfile, slug=kwargs.get('slug'))

#         if not group.can_view(request.user):
#             raise Http404()

#         self.group = group

#         return super(GroupActivityView, self).get(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super(GroupActivityView, self).get_context_data(**kwargs)
#         context['group'] = self.group
#         return context

class AppListView(TemplateView):
    def get_context_data(self, **kwargs):
        ans = super(AppListView,self).get_context_data(**kwargs)
        ans['is_service'] = self.request.path.startswith('/contractor_services/')
        return ans

