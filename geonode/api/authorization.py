from tastypie.authorization import DjangoAuthorization
from tastypie.exceptions import Unauthorized

from guardian.shortcuts import get_objects_for_user


class GeoNodeAuthorization(DjangoAuthorization):

    """Object level API authorization based on GeoNode granular
    permission system"""

    def read_list(self, object_list, bundle):
        permitted_ids = get_objects_for_user(
            bundle.request.user,
            'base.view_resourcebase').values_list(
            'id',
            flat=True)

        return object_list.filter(id__in=permitted_ids)

    def read_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'view_resourcebase',
            bundle.obj.get_self_resource())

    def create_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def create_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'add_resourcebase',
            bundle.obj.get_self_resource())

    def update_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def update_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'change_resourcebase',
            bundle.obj.get_self_resource())

    def delete_list(self, object_list, bundle):
        # TODO implement if needed
        raise Unauthorized()

    def delete_detail(self, object_list, bundle):
        return bundle.request.user.has_perm(
            'delete_resourcebase',
            bundle.obj.get_self_resource())


class AttributeAuthorization(DjangoAuthorization):
    'Allows modification just for owners, accessed by layer attribute.'


    def read_list(self, object_list, bundle):
        return object_list.filter(layer__owner=bundle.request.user)

    def read_detail(self, object_list, bundle):
        return True

    def create_list(self, object_list, bundle):
        raise Unauthorized("No individual create.")

    def create_detail(self, object_list, bundle):
        raise Unauthorized("No individual create.")

    def update_list(self, object_list, bundle):
        allowed = []
        for obj in object_list:
            if obj.layer.owner == bundle.request.user:
                allowed.append(obj)
        return allowed

    def update_detail(self, object_list, bundle):
        return bundle.obj.layer.owner == bundle.request.user

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")        
