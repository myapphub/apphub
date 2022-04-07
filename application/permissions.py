from enum import Enum
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from application.models import UniversalApp, UniversalAppUser
from organization.models import Organization, OrganizationUser
from util.visibility import VisibilityType
from util.role import Role
from util.choice import ChoiceField


class Namespace:

    class Kind(Enum):
        User = 'User'
        Organization = 'Organization'

    def __init__(self, kind, path):
        self._kind = kind
        self._path = path

    @staticmethod
    def user(path):
        return Namespace(Namespace.Kind.User, path)

    @staticmethod
    def organization(path):
        return Namespace(Namespace.Kind.Organization, path)

    @property
    def kind(self):
        return self._kind

    @property
    def path(self):
        return self._path

    def is_user(self):
        return self.kind == Namespace.Kind.User

    def is_organization(self):
        return self.kind == Namespace.Kind.Organization

    def response(self):
        return {
            'kind': self.kind.name,
            'path': self.path
        }

class UserRoleKind:
    class Kind(Enum):
        Organization = 'Organization'
        Application = 'Application'

    def __init__(self, kind, role):
        self._kind = kind
        self._role = role

    @staticmethod
    def application(role):
        return UserRoleKind(UserRoleKind.Kind.Application, role)

    @staticmethod
    def organization(role):
        return UserRoleKind(UserRoleKind.Kind.Organization, role)

    @property
    def kind(self):
        return self._kind

    @property
    def role(self):
        return self._role

    def is_application(self):
        return self.kind == UserRoleKind.Kind.Application

    def is_organization(self):
        return self.kind == UserRoleKind.Kind.Organization

    def response(self):
        return {
            'kind': self.kind.name,
            'role': ChoiceField(choices=Role.choices).to_representation(self.role)
        }

def check_user_app_view_permission(user, path, ownername):
    if user.is_authenticated:
        try:
            user_app = UniversalAppUser.objects.get(user=user, app__path=path, app__owner__username=ownername)
            return user_app.app, UserRoleKind.application(user_app.role)
        except UniversalAppUser.DoesNotExist:
            pass
    try:
        if user.is_authenticated:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
        else:
            allow_visibility = [VisibilityType.Public]
        try:
            app = UniversalApp.objects.get(path=path, owner__username=ownername, visibility__in=allow_visibility)
            return app, None
        except UniversalApp.DoesNotExist:
            raise Http404
    except Organization.DoesNotExist:
        raise Http404

def check_org_app_view_permission(user, path, org_path):
    if user.is_authenticated:
        try:
            user_app = UniversalAppUser.objects.get(app__org__path=org_path, app__path=path, user=user)
            return user_app.app, UserRoleKind.application(user_app.role)
        except UniversalAppUser.DoesNotExist:
            pass
        user_role_kind = None
        try:
            user_org = OrganizationUser.objects.get(org__path=org_path, user=user)
            user_role_kind = UserRoleKind.organization(user_org.role)
            try:
                app = UniversalApp.objects.get(org__path=org_path, path=path)
                return app, user_role_kind
            except UniversalApp.DoesNotExist:
                raise Http404
        except OrganizationUser.DoesNotExist:
            pass
    
    try:
        if user.is_authenticated:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
        else:
            allow_visibility = [VisibilityType.Public]
        app = UniversalApp.objects.get(org__path=org_path, path=path, visibility__in=allow_visibility)
        return app, None
    except UniversalApp.DoesNotExist:
        raise Http404


def check_app_view_permission(user, path, namespace):
    if namespace.is_user():
        return check_user_app_view_permission(user, path, namespace.path)
    if namespace.is_organization():
        return check_org_app_view_permission(user, path, namespace.path)

def check_user_app_manager_permission(user, path, ownername):
    try:
        user_app = UniversalAppUser.objects.get(app__path=path, app__owner__username=ownername, user=user)
        if user_app.role != Role.Owner and user_app.role != Role.Manager:
            raise PermissionDenied
        return user_app.app, UserRoleKind.application(user_app.role)
    except UniversalAppUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            UniversalApp.objects.get(path=path, owner__username=ownername, visibility__in=allow_visibility)
            raise PermissionDenied
        except UniversalApp.DoesNotExist:
            raise Http404

def check_org_app_manager_permission(user, path, org_path):
    app, role = check_org_app_view_permission(user, path, org_path)
    if role and role.role != Role.Manager and role.role != Role.Owner:
        raise PermissionDenied
    if role is None:
        raise PermissionDenied
    return app, role

def check_app_manager_permission(user, path, namespace):
    if namespace.is_user():
        return check_user_app_manager_permission(user, path, namespace.path)
    if namespace.is_organization():
        return check_org_app_manager_permission(user, path, namespace.path)
