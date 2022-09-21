from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import Http404
from django.urls import reverse
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.models import AppAPIToken, Application
from application.permissions import (Namespace, UploadPackagePermission,
                                     check_app_upload_permission, get_app)
from distribute.models import FileUploadRecord, Package
from distribute.package_parser import parser
from distribute.serializers import (PackageSerializer,
                                    RequestUploadPackageSerializer,
                                    RequestUploadSymbolFileSerializer,
                                    UploadPackageSerializer,
                                    UploadSymbolFileSerializer)
from distribute.task import notify_new_package
from util.url import build_absolute_uri, get_file_extension


def create_package(
    operator_content_object,
    universal_app,
    file,
    commit_id="",
    description="",
    channel="",
    build_type="Debug",
):
    ext = get_file_extension(file.name)
    pkg = parser.parse(file.file, ext)
    if pkg is None:
        raise serializers.ValidationError({"message": "Can not parse the package."})
    if pkg.app_icon is not None:
        icon_file = ContentFile(pkg.app_icon)
        icon_file.name = "icon.png"
    else:
        icon_file = None
    app = None
    if pkg.os == Application.OperatingSystem.iOS:
        app = universal_app.iOS
    elif pkg.os == Application.OperatingSystem.Android:
        app = universal_app.android
    if app is None:
        raise serializers.ValidationError({"message": "OS not supported."})
    package_id = (
        Package.objects.filter(app__universal_app=universal_app).count() + 1
    )
    instance = Package.objects.create(
        operator_object_id=operator_content_object.id,
        operator_content_object=operator_content_object,
        build_type=build_type,
        channel=channel,
        app=app,
        name=pkg.display_name,
        package_file=file,
        icon_file=icon_file,
        version=pkg.version,
        short_version=pkg.short_version,
        bundle_identifier=pkg.bundle_identifier,
        package_id=package_id,
        min_os=pkg.minimum_os_version,
        commit_id=commit_id,
        description=description,
        extra=pkg.extra,
        size=file.size,
    )
    if not app.icon_file and icon_file is not None:
        app.icon_file = icon_file
        app.save()
    notify_new_package(instance.id)
    return instance


class TokenAppPackageUpload(APIView):
    permission_classes = [UploadPackagePermission]

    def get_namespace_by_app(self, app):
        if app.owner:
            return Namespace.user(app.owner.username)
        elif app.org:
            return Namespace.organization(app.org.path)
        else:
            return None

    def url_name(self, app):
        if app.owner:
            return "user-app-package"
        elif app.org:
            return "org-app-package"
        return ""

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"
        return ""

    def post(self, request):
        app = request.token.app
        return self.create_package(request, app, request.token)

    def create_package(self, request, app, uploader):
        serializer = UploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        file = serializer.validated_data["file"]
        commit_id = serializer.validated_data.get("commit_id", "")
        description = serializer.validated_data.get("description", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        channel = serializer.validated_data.get("channel", "")
        instance = create_package(
            uploader, app, file, commit_id, description, channel, build_type
        )

        namespace = self.get_namespace_by_app(app)
        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": namespace.path,
            "path": app.path,
        }
        serializer = PackageSerializer(instance, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(
            self.url_name(app),
            args=(namespace.path, app.path, instance.package_id),
        )
        response["Location"] = build_absolute_uri(location)
        return response


class UserAppPackageUpload(TokenAppPackageUpload):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def post(self, request, namespace, path):
        app = self.check_and_get_app(request, namespace, path)
        return self.create_package(request, app, request.user)


class OrganizationAppPackageUpload(UserAppPackageUpload):

    def get_namespace(self, path):
        return Namespace.organization(path)


class RequestUploadPackage(APIView):
    permission_classes = [UploadPackagePermission]

    def upload_url(self):
        return reverse("token-package-upload")

    def uploader_type(self, request):
        return "token"

    def uploader_id(self, request):
        return request.token.id

    def post(self, request):
        app = request.token.app
        return self.request_upload(request, app)

    def request_upload(self, request, app):
        serializer = RequestUploadPackageSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        filename = serializer.validated_data["filename"]
        description = serializer.validated_data.get("description", "")
        commit_id = serializer.validated_data.get("commit_id", "")
        build_type = serializer.validated_data.get("build_type", "Debug")
        channel = serializer.validated_data.get("channel", "")

        if settings.STORAGE_TYPE == "LocalFileSystem":
            ret = {
                "upload_url": build_absolute_uri(self.upload_url()),
                "storage": settings.STORAGE_TYPE
            }
            return Response(ret)

        ret = default_storage.request_upload_url(app.install_slug, filename)
        data = {
            "type": "package",
            "file": ret["file"],
            "description": description,
            "commit_id": commit_id,
            "build_type": build_type,
            "channel": channel,
            "uploader_type": self.uploader_type(request),
            "uploader_id": self.uploader_id(request)
        }
        instance = FileUploadRecord.objects.create(
            universal_app=app,
            data=data
        )
        ret["record_id"] = instance.id
        ret["storage"] = settings.STORAGE_TYPE
        return Response(ret)


class UserAppRequestUploadPackage(RequestUploadPackage):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def upload_url(self):
        return reverse("user-package-upload")

    def uploader_type(self, request):
        return "user"

    def uploader_id(self, request):
        return request.user.id

    def post(self, request, namespace, path):
        app = self.check_and_get_app(request, namespace, path)
        return self.request_upload(request, app)


class OrganizationAppRequestUploadPackage(UserAppRequestUploadPackage):

    def get_namespace(self, path):
        return Namespace.organization(path)

    def upload_url(self):
        return reverse("org-package-upload")


class CheckUploadPackage(APIView):
    permission_classes = [UploadPackagePermission]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, record_id):
        app = request.token.app
        return self.get_record(request, app, record_id)

    def get_record(self, request, app, record_id):
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
            if record.data.get("type", "") != "package":
                raise Http404
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            data = {
                "status": "waiting"  # expired
            }

        return Response(data)

    def put(self, request, record_id):
        app = request.token.app
        return self.update_record(request, app, record_id)

    def update_record(self, request, app, record_id):
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
            if record.data.get("type", "") != "package":
                raise Http404
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            extra = record.data
            file = default_storage.open(extra["file"])
            commit_id = extra.get("commit_id", "")
            description = extra.get("description", "")
            build_type = extra.get("build_type", "Debug")
            channel = extra.get("channel", "")
            uploader = AppAPIToken.objects.get(id=extra["uploader_id"])
            instance = create_package(
                uploader, app, file, commit_id, description, channel, build_type
            )
            record.package = instance
            try:
                default_storage.delete(extra["file"])
            except:   # noqa: E722
                pass
            record.save()
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(instance, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }

        return Response(data)


class UserAppCheckUploadPackage(CheckUploadPackage):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def get(self, request, namespace, path, record_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.get_record(request, app, record_id)

    def put(self, request, namespace, path, record_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.update_record(request, app, record_id)


class OrganizationAppCheckUploadPackage(UserAppCheckUploadPackage):

    def get_namespace(self, path):
        return Namespace.organization(path)


class TokenAppSymbolUpload(UserAppPackageUpload):

    permission_classes = [UploadPackagePermission]

    def get_namespace(self, app):
        if app.owner:
            return Namespace.user(app.owner.username)
        elif app.org:
            return Namespace.organization(app.org.path)
        else:
            return None

    def url_name(self, app):
        if app.owner:
            return "user-app-package"
        elif app.org:
            return "org-app-package"
        return ""

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"
        return ""

    def post(self, request, package_id):
        app = request.token.app
        return self.upload_symbol_file(request, app, package_id)

    def upload_symbol_file(self, request, app, package_id):
        serializer = UploadSymbolFileSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        try:
            package = Package.objects.get(package_id=package_id, app__universal_app=app)
        except Package.DoesNotExist:
            raise Http404
        file = serializer.validated_data["file"]
        package.symbol_file = file
        package.save()

        context = {
            "plist_url_name": self.plist_url_name(app),
            "namespace": self.get_namespace(app).path,
            "path": app.path,
        }
        serializer = PackageSerializer(package, context=context)
        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        location = reverse(
            self.url_name(app),
            args=(self.get_namespace(app).path, app.path, package.package_id),
        )
        response["Location"] = build_absolute_uri(location)
        return response


class UserAppSymbolUpload(TokenAppSymbolUpload):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def post(self, request, namespace, path, package_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.create_package(request, app, package_id)


class OrganizationAppSymbolUpload(UserAppSymbolUpload):

    def get_namespace(self, path):
        return Namespace.organization(path)


class RequestUploadSymbolFile(APIView):
    permission_classes = [UploadPackagePermission]

    def upload_url(self, package_id):
        return reverse("token-symbol-upload", args=[package_id, ])

    def uploader_type(self, request):
        return "token"

    def uploader_id(self, request):
        return request.token.id

    def post(self, request, package_id):
        app = request.token.app
        return self.request_upload(request, app, package_id)

    def request_upload(self, request, app, package_id):
        serializer = RequestUploadSymbolFileSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        try:
            package = Package.objects.get(package_id=package_id, app__universal_app=app)
        except Package.DoesNotExist:
            raise Http404
        filename = serializer.validated_data["filename"]

        if settings.STORAGE_TYPE == "LocalFileSystem":
            ret = {
                "upload_url": build_absolute_uri(self.upload_url(package_id)),
                "storage": settings.STORAGE_TYPE
            }
            return Response(ret)

        ret = default_storage.request_upload_url(app.install_slug, filename)
        data = {
            "type": "symbol",
            "file": ret["file"],
            "uploader_type": self.uploader_type(request),
            "uploader_id": self.uploader_id(request)
        }
        instance = FileUploadRecord.objects.create(
            universal_app=app,
            data=data,
            package=package
        )
        ret["record_id"] = instance.id
        ret["storage"] = settings.STORAGE_TYPE
        return Response(ret)


class UserAppRequestUploadSymbolFile(RequestUploadSymbolFile):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def upload_url(self, package_id):
        return reverse("user-symbol-upload", args=[package_id, ])

    def uploader_type(self, request):
        return "user"

    def uploader_id(self, request):
        return request.user.id

    def post(self, request, namespace, path, package_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.request_upload(request, app, package_id)


class OrganizationAppRequestUploadSymbolFile(UserAppRequestUploadSymbolFile):

    def get_namespace(self, path):
        return Namespace.organization(path)

    def upload_url(self, package_id):
        return reverse("org-symbol-upload", args=[package_id, ])


class CheckUploadSymbolFile(APIView):
    permission_classes = [UploadPackagePermission]

    def plist_url_name(self, app):
        if app.owner:
            return "user-app-package-plist"
        elif app.org:
            return "org-app-package-plist"

    def get(self, request, record_id):
        app = request.token.app
        return self.get_record(request, app, record_id)

    def get_record(self, request, app, record_id):
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
            if record.data.get("type", "") != "symbol":
                raise Http404
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            data = {
                "status": "waiting"  # expired
            }

        return Response(data)

    def put(self, request, record_id):
        app = request.token.app
        return self.update_record(request, app, record_id)

    def update_record(self, request, app, record_id):
        try:
            record = FileUploadRecord.objects.get(id=record_id, universal_app=app)
            if record.data.get("type", "") != "symbol":
                raise Http404
        except FileUploadRecord.DoesNotExist:
            raise Http404

        if record.package:
            namespace = ""
            if app.owner:
                namespace = app.owner.username
            elif app.org:
                namespace = app.org.path
            context = {
                "plist_url_name": self.plist_url_name(app),
                "namespace": namespace,
                "path": app.path,
            }
            package = record.package

            extra = record.data
            file = default_storage.fast_open(extra["file"])
            package.symbol_file = file
            package.save()

            try:
                default_storage.delete(extra["file"])
            except:   # noqa: E722
                pass

            serializer = PackageSerializer(record.package, context=context)
            data = {
                "status": "completed",
                "data": serializer.data
            }
        else:
            raise Http404

        return Response(data)


class UserAppCheckUploadSymbolFile(CheckUploadSymbolFile):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, namespace):
        return Namespace.user(namespace)

    def check_and_get_app(self, request, namespace, path):
        if request.user.is_authenticated:
            app, role = check_app_upload_permission(
                request.user, path, self.get_namespace(namespace)
            )
            return app
        else:
            app = get_app(path, self.get_namespace(namespace))
            self.check_object_permissions(request, app)
            return app

    def get(self, request, namespace, path, record_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.get_record(request, app, record_id)

    def put(self, request, namespace, path, record_id):
        app = self.check_and_get_app(request, namespace, path)
        return self.update_record(request, app, record_id)


class OrganizationAppCheckUploadSymbolFile(UserAppCheckUploadSymbolFile):

    def get_namespace(self, path):
        return Namespace.organization(path)
