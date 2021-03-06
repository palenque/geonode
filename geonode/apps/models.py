import datetime
import hashlib

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import models, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from actstream.models import Action

from taggit.managers import TaggableManager
from guardian.shortcuts import get_objects_for_group, remove_perm, assign_perm

class App(models.Model):
    # GROUP_CHOICES = [
    #     ("public", _("Public")),
    #     ("public-invite", _("Public (invite-only)")),
    #     ("private", _("Private")),
    # ]

    # access_help_text = _('Public: Any registered user can view and join a public group.<br>'
    #                      'Public (invite-only):Any registered user can view the group.  '
    #                      'Only invited users can join.<br>'
    #                      'Private: Registered users cannot see any details about the group, including membership.  '
    #                      'Only invited users can join.')
    #email_help_text = _('Email used to contact one or all app members, '
    #                    'such as a mailing list, shared email, or exchange group.')

    email_help_text = _('Public url for the application.')

    # group = models.OneToOneField(Group)
    title = models.CharField(_('Title'), max_length=50)
    slug = models.SlugField(_('Slug'), unique=True)
    logo = models.FileField(_('Logo'), upload_to="people_group", blank=False, null=False)
    description = models.TextField(_('Description'))    # markdown
    short_description = models.TextField(_('Short Description'), blank=True, null=True)
    thumbnail = models.FileField(_('Thumbnail'), upload_to="people_group", null=True, blank=True)
    category = models.ForeignKey('AppCategory', null=True, blank=True)
    widget_url = models.URLField(null=True, blank=True)

    # TODO: improve
    rating = models.IntegerField(_('Rating'), null=True, blank=True)


    email = models.URLField(
        _('email'),
        null=True,
        blank=True,
        help_text=email_help_text)
    keywords = TaggableManager(
        _('Resources'),
        help_text=_("A space or comma-separated list of resources required"),
        blank=True)
    # access = models.CharField(
    #     max_length=15,
    #     default="public'",
    #     choices=GROUP_CHOICES,
    #     help_text=access_help_text)
    last_modified = models.DateTimeField(auto_now=True)

    is_service = models.BooleanField()

    # def save(self, *args, **kwargs):
    #     group, created = Group.objects.get_or_create(name=self.slug)
    #     self.group = group
    #     super(App, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Group.objects.filter(name=self.slug).delete()
        super(App, self).delete(*args, **kwargs)

    @classmethod
    def groups_for_user(cls, user):
        """
        Returns the groups that user is a member of.  If the user is a superuser, all groups are returned.
        """
        if user.is_authenticated():
            if user.is_superuser:
                return cls.objects.all()
            return cls.objects.filter(groupmember__user=user)
        return []

    def __unicode__(self):
        return self.title

    def keyword_list(self):
        """
        Returns a list of the Group's keywords.
        """
        return [kw.name for kw in self.keywords.all()]

    def resources(self, resource_type=None):
        """
        Returns a generator of objects that this group has permissions on.

        :param resource_type: Filter's the queryset to objects with the same type.
        """

        queryset = get_objects_for_group(
            self.group, [
                'base.view_resourcebase', 'base.change_resourcebase'], any_perm=True)

        if resource_type:
            queryset = [
                item for item in queryset if hasattr(
                    item,
                    resource_type)]

        for resource in queryset:
            yield resource

    def member_queryset(self):
        return self.appmember_set.all()

    def get_managers(self):
        """
        Returns a queryset of the group's managers.
        """
        return get_user_model().objects.filter(
            id__in=self.member_queryset().filter(
                role='manager').values_list(
                "user",
                flat=True))

    def get_members(self):
        return get_user_model().objects.filter(
            id__in=self.member_queryset().filter(
                role='member').values_list(
                "user",
                flat=True))

    def get_alter_ego(self):
        """
        Returns a queryset of the group's managers.
        """
        try:
            return get_user_model().objects.get(
                id=self.member_queryset().get(role='alter_ego').user_id)
        except (App.DoesNotExist, AppMember.DoesNotExist) as e:
            return

    def user_is_member(self, user):
        if not user.is_authenticated():
            return False
        return user.id in self.member_queryset().values_list("user", flat=True)

    def user_is_role(self, user, role):
        if not user.is_authenticated():
            return False
        return self.member_queryset().filter(user=user, role=role).exists()

    def can_view(self, user):
        if self.access == "private":
            return user.is_authenticated() and self.user_is_member(user)
        else:
            return True

    def get_action_list(self):
        return Action.objects.filter(actor_object_id=self.get_alter_ego().id)

    def can_invite(self, user):
        if not user.is_authenticated():
            return False
        return self.user_is_role(user, "alter_ego")

    def resources_by_user(self, user):
        'Returns resource that an user shares with this app.'

        manager = self.get_managers()[0]
        for resource in user.resourcebase_set.filter(
            keywords__name__in=self.keyword_list()
        ).distinct():
            if manager.has_perm('view_resourcebase', resource):
                yield resource

    def set_free_resources(self, user):
        ''
        manager = self.get_managers()[0]
        for resource in self.resources_by_user(user):
            remove_perm('view_resourcebase', manager, resource)
        
        AppMember.objects.get(app=self, user=user).delete()

    def join(self, user, **kwargs):
        from geonode.layers.models import Layer
        from geonode.tabular.models import Tabular

        'Joins an user to this app as a member.'
        if user == user.get_anonymous():
            raise ValueError("The invited user cannot be anonymous")

        AppMember(app=self, user=user, **kwargs).save()

        # asocia todos los recursos del usuario que tienen 
        # los recursos que necesita la app

        manager = self.get_managers()[0]
        for resource in user.resourcebase_set.all():
            keywords = set(resource.keyword_list())

            try: keywords.add(resource.layer.layer_type.name)
            except Layer.DoesNotExist: pass

            try: keywords.add(resource.tabular.tabular_type.name)
            except Tabular.DoesNotExist: pass

            if len(keywords.intersection(self.keyword_list())) > 0:
                assign_perm('view_resourcebase', manager, resource)


        # user.groups.add(self.group)

    # def invite(self, user, from_user, role="member", send=True):
    #     params = dict(role=role, from_user=from_user)
    #     if isinstance(user, get_user_model()):
    #         params["user"] = user
    #         params["email"] = user.email
    #     else:
    #         params["email"] = user
    #     bits = [
    #         settings.SECRET_KEY,
    #         params["email"],
    #         str(datetime.datetime.now()),
    #         settings.SECRET_KEY
    #     ]
    #     params["token"] = hashlib.sha1("".join(bits)).hexdigest()

    #     # If an invitation already exists, re-use it.
    #     try:
    #         invitation = self.invitations.create(**params)
    #     except IntegrityError:
    #         invitation = self.invitations.get(
    #             group=self,
    #             email=params["email"])

    #     if send:
    #         invitation.send(from_user)
    #     return invitation

    @models.permalink
    def get_absolute_url(self):
        return ('app_detail', (), {'slug': self.slug})

    @property
    def class_name(self):
        return self.__class__.__name__


class AppMember(models.Model):

    app = models.ForeignKey(App)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    role = models.CharField(max_length=10, choices=[
        ("manager", _("Manager")),
        ("member", _("Member")),
        ("alter_ego", _("Alter ego"))
    ])
    joined = models.DateTimeField(default=datetime.datetime.now)

class AppCategory(models.Model):
    identifier = models.CharField(max_length=255)
    description = models.TextField(null=False, blank=False)
    is_service = models.BooleanField()

    def __unicode__(self):
        return self.description

# class GroupInvitation(models.Model):

#     group = models.ForeignKey(GroupProfile, related_name="invitations")
#     token = models.CharField(max_length=40)
#     email = models.EmailField()
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True,
#         related_name="pg_invitations_received")
#     from_user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name="pg_invitations_sent")
#     role = models.CharField(max_length=10, choices=[
#         ("manager", _("Manager")),
#         ("member", _("Member")),
#     ])
#     state = models.CharField(
#         max_length=10,
#         choices=(
#             ("sent", _("Sent")),
#             ("accepted", _("Accepted")),
#             ("declined", _("Declined")),
#         ),
#         default = "sent",
#     )
#     created = models.DateTimeField(default=datetime.datetime.now)

#     def __unicode__(self):
#         return "%s to %s" % (self.email, self.group.title)

#     class Meta:
#         unique_together = [("group", "email")]

#     # def send(self, from_user):
#     #     current_site = Site.objects.get_current()
#     #     domain = unicode(current_site.domain)
#         # ctx = {
#         #     "invite": self,
#         #     "group": self.group,
#         #     "from_user": from_user,
#         #     "domain": domain,
#         # }
#         # subject = render_to_string("groups/email/invite_user_subject.txt", ctx)
#         # message = render_to_string("groups/email/invite_user.txt", ctx)
#         # TODO Send a notification rather than a mail
#         # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email])

#     def accept(self, user):
#         if not user.is_authenticated() or user == user.get_anonymous():
#             raise ValueError("You must log in to accept invitations")
#         if not user.email == self.email:
#             raise ValueError(
#                 "You can't accept an invitation that wasn't for you")
#         self.group.join(user, role=self.role)
#         self.state = "accepted"
#         self.user = user
#         self.save()

#     def decline(self, user):
#         if not user.is_authenticated() or user == user.get_anonymous():
#             raise ValueError("You must log in to decline invitations")
#         if not user.email == self.email:
#             raise ValueError(
#                 "You can't decline an invitation that wasn't for you")
#         self.state = "declined"
#         self.save()


def group_pre_delete(instance, sender, **kwargs):
    """Make sure that the anonymous group is not deleted"""
    if instance.name == 'anonymous':
        raise Exception('Deletion of the anonymous group is\
         not permitted as will break the geonode permissions system')


def update_alter_ego_logo(instance, sender, **kwargs):
    if instance.get_alter_ego() is not None:
        instance.get_alter_ego().save_avatar(instance.logo)


signals.post_save.connect(update_alter_ego_logo, sender=App)
signals.pre_delete.connect(group_pre_delete, sender=Group)
