# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AbstractUser
from django.db.models import signals

from taggit.managers import TaggableManager

from geonode.base.enumerations import COUNTRIES
from geonode.groups.models import GroupProfile

from .utils import format_address
from .enumerations import PROFILE_VALUES

from avatar.models import Avatar

class Profile(AbstractUser):

    """Fully featured Geonode user"""

    organization = models.CharField(
        _('Organization Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('name of the responsible organization'))
    profile = models.CharField(_('Profile'), max_length=20, choices=PROFILE_VALUES, null=False, blank=False, default='user', help_text=_('type of user'))
    position = models.CharField(
        _('Position Name'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('role or position of the responsible person'))
    voice = models.CharField(_('Voice'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number by which individuals can speak to the responsible organization or individual'))
    fax = models.CharField(_('Facsimile'), max_length=255, blank=True, null=True, help_text=_(
        'telephone number of a facsimile machine for the responsible organization or individual'))
    delivery = models.CharField(
        _('Delivery Point'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('physical and email address at which the organization or individual may be contacted'))
    city = models.CharField(
        _('City'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('city of the location'))
    area = models.CharField(
        _('Administrative Area'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('state, province of the location'))
    zipcode = models.CharField(
        _('Postal Code'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('ZIP or other postal code'))
    country = models.CharField(
        choices=COUNTRIES,
        max_length=3,
        blank=True,
        null=True,
        help_text=_('country of the physical address'))
    keywords = TaggableManager(_('keywords'), blank=True, help_text=_(
        'commonly used word(s) or formalised word(s) or phrase(s) used to describe the subject \
            (space or comma-separated'))


    def save_avatar(self, logo):
        'Sets an avatar'

        self.avatar_set.all().delete()
        if logo:
            avatar = Avatar(
                user = self,
                primary = True,
            )
            image_file = logo
            avatar.avatar.save(image_file.name, image_file)
            avatar.save()

    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        elif self.organization:
            return self.organization
        else:
            return self.username

    @property
    def profile_icon_class(self):
        if self.profile == PROFILE.APP:
            return 'fa-cubes'
        elif self.profile == PROFILE.ORGANIZATION:
            return 'fa-bank'
        elif self.profile == PROFILE.DEVELOPER:
            return 'fa-lightbulb-o' 
        elif self.profile == PROFILE.CONTRACTOR:
            return 'fa-briefcase' 
        else:
            return 'fa-user'

    def get_absolute_url(self):
        return reverse('profile_detail', args=[self.username, ])

    def __unicode__(self):
        return u"%s" % (self.username)

    def class_name(value):
        return value.__class__.__name__

    USERNAME_FIELD = 'username'

    def group_list_public(self):
        return GroupProfile.objects.exclude(access="private").filter(groupmember__user=self)

    def group_list_all(self):
        return GroupProfile.objects.filter(groupmember__user=self)

    def apps_list_all(self):
        return [x.app for x in self.appmember_set.filter(role='member')]

    def own_apps_list_all(self):
        return [x.app for x in self.appmember_set.filter(role='manager')]

    def get_action_list_for_app(self, app):
        from actstream.models import Action
        from geonode.base.models import ResourceBase
        developer = app.get_managers()[0]
        alter_ego = app.get_alter_ego()
        objects = ResourceBase.objects.filter(owner=self).all()
        return Action.objects \
            .filter(actor_object_id__in=[developer.id,alter_ego.id]) \
            .filter(
                Q(target_object_id=self.id) | 
                Q(action_object_object_id__in=[x.id for x in objects])).all()

    #XXX: check
    @property
    def apps(self):
        return [x.app for x in self.appmember_set.all()]

    def keyword_list(self):
        """
        Returns a list of the Profile's keywords.
        """
        return [kw.name for kw in self.keywords.all()]

    @property
    def name_long(self):
        if self.first_name and self.last_name:
            return '%s %s (%s)' % (self.first_name, self.last_name, self.username)
        elif (not self.first_name) and self.last_name:
            return '%s (%s)' % (self.last_name, self.username)
        elif self.first_name and (not self.last_name):
            return '%s (%s)' % (self.first_name, self.username)
        else:
            return self.username

    @property
    def location(self):
        return format_address(self.delivery, self.zipcode, self.city, self.area, self.country)


def get_anonymous_user_instance(Profile):
    return Profile(username='AnonymousUser')


def profile_post_save(instance, sender, **kwargs):
    """Make sure the user belongs by default to the anonymous group.
    This will make sure that anonymous permissions will be granted to the new users."""
    from django.contrib.auth.models import Group
    anon_group, c = Group.objects.get_or_create(name='anonymous')
    instance.groups.add(anon_group)
    # keep in sync Profile email address with Account email address
    # if instance.email not in [u'', '', None] and not kwargs.get('raw', False):
    #     emailaddress, created = instance.emailaddress_set.get_or_create(user=instance, primary=True)
    #     if created or not emailaddress.email == instance.email:
    #         emailaddress.email = instance.email
    #         emailaddress.save()


signals.post_save.connect(profile_post_save, sender=Profile)

