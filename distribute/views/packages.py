from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.core.signing import BadSignature, TimestampSigner
from django.http import Http404
from django.shortcuts import render
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.models import Application
from application.permissions import (Namespace, UploadPackagePermission,
                                     check_app_download_permission,
                                     check_app_manager_permission,
                                     check_app_view_permission, get_app)
from distribute.models import Package, Release
from distribute.serializers import PackageSerializer, PackageUpdateSerializer
from util.choice import ChoiceField
from util.pagination import get_pagination_params


class UserAppPackageList(APIView):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly | UploadPackagePermission
    ]

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
            query = Package.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Package.objects.filter(app__universal_app=app)
        count = query.count()
        packages = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]

        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(packages, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)


class OrganizationAppPackageList(UserAppPackageList):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def plist_url_name(self):
        return "user-app-package-plist"

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, package_id):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)

    def put(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        serializer = PackageUpdateSerializer(package, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()
        context = {
            "plist_url_name": self.plist_url_name(),
            "namespace": namespace,
            "path": path,
        }
        return Response(PackageSerializer(instance, context=context).data)

    def delete(self, request, namespace, path, package_id):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        package = self.get_object(app, package_id)
        try:
            Release.objects.get(package=package)
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        except Release.DoesNotExist:
            pass
        package.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationAppPackageDetail(UserAppPackageDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def plist_url_name(self):
        return "org-app-package-plist"


class UserAppPackagePlist(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    template_name = "install.plist"

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, sign_name, sign_value, package_id):
        name = namespace + path + str(package_id)
        sign = sign_name + ":" + sign_value
        signer = TimestampSigner()
        try:
            value = signer.unsign(
                name + ":" + sign, max_age=timedelta(seconds=60 * 60 * 24)
            )
        except BadSignature:
            raise PermissionDenied

        if value != name:
            raise PermissionDenied

        app = get_app(path, self.get_namespace(namespace))
        package = self.get_object(app, package_id)

        data = {
            "ipa": package.package_file.url,
            "icon": package.icon_file.url,
            "identifier": package.bundle_identifier,
            "version": package.short_version,
            "name": package.name,
        }
        return render(request, self.template_name, data, content_type="application/xml")


class OrganizationAppPackagePlist(UserAppPackagePlist):
    def get_namespace(self, path):
        return Namespace.organization(path)


class SlugAppPackageList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, slug):
        app = check_app_download_permission(request.user, slug)
        page, per_page = get_pagination_params(request)
        os = request.GET.get("os", None)

        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path

        if os:
            query = Package.objects.filter(
                app__universal_app=app,
                app__os=ChoiceField(
                    choices=Application.OperatingSystem.choices
                ).to_internal_value(os),
            )
        else:
            query = Package.objects.filter(app__universal_app=app)
        count = query.count()
        packages = query.order_by("-create_time")[
            (page - 1) * per_page : page * per_page
        ]
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(packages, many=True, context=context)
        headers = {"X-Total-Count": count}
        return Response(serializer.data, headers=headers)


class SlugAppPackageLatest(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, slug):
        app = check_app_download_permission(request.user, slug)
        tryOS = request.GET.get("tryOS", None)
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path

        if tryOS and tryOS in app.enable_os_enum_list():
            package = (
                Package.objects.filter(
                    app__universal_app=app,
                    app__os=ChoiceField(
                        choices=Application.OperatingSystem.choices
                    ).to_internal_value(tryOS),
                )
                .order_by("-create_time")
                .first()
            )
        else:
            package = (
                Package.objects.filter(app__universal_app=app)
                .order_by("-create_time")
                .first()
            )
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)


class SlugAppPackageDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get_object(self, universal_app, package_id):
        try:
            return Package.objects.get(
                app__universal_app=universal_app, package_id=package_id
            )
        except Package.DoesNotExist:
            raise Http404

    def get(self, request, slug, package_id):
        app = check_app_download_permission(request.user, slug)
        namespace = ""
        if app.owner:
            namespace = app.owner.username
        elif app.org:
            namespace = app.org.path
        package = self.get_object(app, package_id)
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace,
            "path": app.path,
        }
        serializer = PackageSerializer(package, context=context)
        return Response(serializer.data)
