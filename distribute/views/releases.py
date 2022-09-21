from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.models import Application
from application.permissions import (Namespace, check_app_manager_permission,
                                     check_app_view_permission)
from distribute.models import Release
from distribute.serializers import ReleaseCreateSerializer, ReleaseSerializer
from util.choice import ChoiceField
from util.pagination import get_pagination_params


class UserAppReleaseList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        os = request.GET.get("os", None)
        page, per_page = get_pagination_params(request)

        if os:
            query = Release.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Release.objects.filter(app__universal_app=app)
        count = query.count()
        releases = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = ReleaseSerializer(releases, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        serializer = ReleaseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        data = ReleaseSerializer(instance, context=context).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationAppReleaseList(UserAppReleaseList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppReleaseDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get_object(self, universal_app, release_id):
        try:
            return Release.objects.get(
                app__universal_app=universal_app, release_id=release_id
            )
        except Release.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, release_id):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = ReleaseSerializer(release, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        serializer = ReleaseCreateSerializer(release, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        return Response(ReleaseSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, release_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        release = self.get_object(app, release_id)
        if release.enabled:
            release.package.make_internal(app.install_slug)
        # todo: check release, upgrades use
        release.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationAppReleaseDetail(UserAppReleaseDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"
