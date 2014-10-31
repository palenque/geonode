import json

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotAllowed
from django.http import HttpResponse
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView


from actstream.models import Action
from guardian.shortcuts import assign_perm, remove_perm


from geonode.base.models import ResourceBase
from geonode.apps.forms import AppForm, AppUpdateForm
from geonode.apps.models import App, AppMember
from geonode.people.models import Profile
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

@login_required
def app_create(request):
    if request.method == "POST":
        form = AppForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.save()
            form.save_m2m()
            app.join(request.user, role="manager")
            return HttpResponseRedirect(
                reverse("app_detail", args=[app.slug])
            )
    else:
        form = AppForm()

    return render_to_response("apps/app_create.html", {
        "form": form,
    }, context_instance=RequestContext(request))


@login_required
def app_update(request, slug):
    app = App.objects.get(slug=slug)
    if not app.user_is_role(request.user, role="manager"):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = AppUpdateForm(request.POST, request.FILES, instance=app)
        if form.is_valid():
            app = form.save(commit=False)
            app.save()
            form.save_m2m()
            return HttpResponseRedirect(
                reverse("app_detail", args=[app.slug]))
    else:
        form = AppForm(instance=app)

    return render_to_response("apps/app_update.html", {
        "form": form,
        "group": app,
    }, context_instance=RequestContext(request))


class AppDetailView(ListView):

    """
    Mixes a detail view (the app) with a ListView (the members).
    """

    model = get_user_model()
    template_name = "apps/app_detail.html"
    paginate_by = None
    app = None

    def get_queryset(self):
        return self.app.member_queryset()

    def get(self, request, *args, **kwargs):
        self.app = get_object_or_404(App, slug=kwargs.get('slug'))
        return super(AppDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        manager = self.app.get_managers()[0]
        profile = get_object_or_404(Profile, username=self.request.user.username)
        user_objects = profile.resourcebase_set.distinct()

        content_filter = 'all'

        if ('content' in self.request.GET):
            content = self.request.GET['content']
            if content != 'all':
                if (content == 'layers'):
                    content_filter = 'layers'
                    user_objects = user_objects.instance_of(Layer)
                if (content == 'monitors'):
                    content_filter = 'monitors'
                    user_objects = Layer.objects.filter(
                        layer_type='monitor',
                        owner=self.request.user
                    )
                if (content == 'maps'):
                    content_filter = 'maps'
                    user_objects = user_objects.instance_of(Map)
                if (content == 'documents'):
                    content_filter = 'documents'
                    user_objects = user_objects.instance_of(Document)

        sortby_field = 'date'
        if ('sortby' in self.request.GET):
            sortby_field = self.request.GET['sortby']
        if sortby_field == 'title':
            user_objects = user_objects.order_by('title')
        else:
            user_objects = user_objects.order_by('-date')

        context = super(AppDetailView, self).get_context_data(**kwargs)
        context['object'] = self.app
        context['app_manager'] = manager
        context['maps'] = self.app.resources(resource_type='map')
        context['layers'] = self.app.resources(resource_type='layer')
        context['is_member'] = self.app.user_is_member(self.request.user)
        context['is_manager'] = self.app.user_is_role(self.request.user, "manager")
        
        context['profile'] = profile
        context['sortby_field'] = sortby_field
        context['content_filter'] = content_filter
        context['object_list'] = user_objects.get_real_instances()
        context['permissions'] = [
            obj.id for obj in user_objects if manager.has_perm('base.view_resourcebase', obj)
        ]

        # context['can_view'] = self.app.can_view(self.request.user)
        return context


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

    app = get_object_or_404(App, id=app_id)
    manager = app.get_managers()[0]
    profile = get_object_or_404(Profile, username=username)
    # combined queryset from each model content type
    user_objects = profile.resourcebase_set.distinct()

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
            if (content == 'monitors'):
                content_filter = 'monitors'
                user_objects = Layer.objects.filter(
                    layer_type='monitor',
                    owner=self.request.user
                )                
            if (content == 'documents'):
                content_filter = 'documents'
                user_objects = user_objects.instance_of(Document)

    # TODO: cambiar query
    user_objects = profile.resourcebase_set.filter(
        id__in=[obj.id for obj in user_objects if manager.has_perm('base.view_resourcebase', obj)]
    )

    sortby_field = 'date'
    if ('sortby' in request.GET):
        sortby_field = request.GET['sortby']
    if sortby_field == 'title':
        user_objects = user_objects.order_by('title')
    else:
        user_objects = user_objects.order_by('-date')

    return render(request, "apps/app_member_detail.html", {
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
    resource = get_object_or_404(
        ResourceBase, id=request.POST.get('resource_id')
    )
    
    if app.user_is_role(request.user, role="member"):
    
        if shared == 'true':
            assign_perm('base.view_resourcebase', app.get_managers()[0], resource)
        else:
            remove_perm('base.view_resourcebase', app.get_managers()[0], resource)

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
def app_member_remove(request, slug, username):

    app = get_object_or_404(App, slug=slug)
    user = get_object_or_404(get_user_model(), username=username)

    if request.method == 'GET':
        return render_to_response(
            "apps/app_member_remove.html", RequestContext(request, {"group": app}))

    elif request.method == 'POST':

        if request.user == user:
            AppMember.objects.get(app=app, user=user).delete()
            return redirect("app_detail", slug=app.slug)
        return HttpResponseForbidden()


@require_POST
@login_required
def app_join(request, slug):

    app = get_object_or_404(App, slug=slug)

    # if group.access == "private":
    #     raise Http404()

    if app.user_is_member(request.user):
        return redirect("app_detail", slug=app.slug)
    else:
        app.join(request.user, role="member")
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
