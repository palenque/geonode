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

from django.utils import simplejson as json
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from actstream.models import Action

from geonode.utils import resolve_object
from geonode.base.models import ResourceBase
 

def _perms_info(obj):
    info = obj.get_all_level_info()

    return info


def _perms_info_json(obj):
    info = _perms_info(obj)

    info['users'] = dict([(u.username, perms)
                          for u, perms in info['users'].items()])
    info['groups'] = dict([(g.name, perms)
                           for g, perms in info['groups'].items()])

    return json.dumps(info)


def resource_permissions(request, resource_id):
    try:
        resource = resolve_object(
            request, ResourceBase, {
                'id': resource_id}, 'base.change_resourcebase_permissions')
        resource_content_type = ContentType.objects.get_for_model(resource).id

    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this resource',
            status=401,
            mimetype='text/plain')

    if request.method == 'POST':
        permission_spec = json.loads(request.body)
        old_permission_spec = resource.get_all_level_info()

        for user in permission_spec['users']:
            user = get_user_model().objects.get(username=user)
            if user not in old_permission_spec['users']:
                action = Action(
                    actor=request.user, 
                    action_object_id=resource.id,
                    action_object_content_type_type=resource_content_type,
                    target=user,
                    verb='permission_granted')
                action.save()
            else:
                old_permission_spec['users'].pop(user)

        resource.set_permissions(permission_spec)

        for user in old_permission_spec['users']:
            action = Action(
                actor=request.user, 
                action_object_id=resource.id,
                action_object_content_type=resource_content_type,
                target=user,
                verb='permission_revoked')
            action.save()


        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = _perms_info_json(resource)
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')
