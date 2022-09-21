from urllib.parse import unquote

from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from application.permissions import (Namespace, check_app_manager_permission,
                                     check_app_view_permission)
from distribute.models import StoreApp, StoreAppVersionRecord
from distribute.serializers import (StoreAppAppStoreAuthSerializer,
                                    StoreAppHuaweiStoreAuthSerializer,
                                    StoreAppSerializer,
                                    StoreAppVersionSerializer,
                                    StoreAppVivoAuthSerializer,
                                    StoreAppXiaomiStoreAuthSerializer,
                                    StoreAppYingyongbaoStoreAuthSerializer)
from distribute.stores.app_store import AppStore
from distribute.stores.base import StoreType
from distribute.stores.huawei import HuaweiStore
from distribute.stores.store import get_store
from distribute.stores.vivo import VivoStore
from distribute.stores.xiaomi import XiaomiStore
from distribute.stores.yingyongbao import YingyongbaoStore


class UserStoreAppBase(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def store_type(self):
        pass

    def get_serializer(self, data):
        pass

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        try:
            store_app = StoreApp.objects.get(app__universal_app=app, store=self.store_type())  # noqa: E501
        except StoreApp.DoesNotExist:
            raise Http404
        serializer = StoreAppSerializer(store_app)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        try:
            StoreApp.objects.get(app__universal_app=app, store=self.store_type())
            return Response({}, status=status.HTTP_409_CONFLICT)
        except StoreApp.DoesNotExist:
            pass
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(universal_app=app)
        data = StoreAppSerializer(instance).data
        return Response(data, status=status.HTTP_201_CREATED)


class OrganizationStoreAppBase(UserStoreAppBase):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppAppstore(UserStoreAppBase):

    def store_type(self):
        return StoreType.AppStore

    def get_serializer(self, data):
        return StoreAppAppStoreAuthSerializer(data=data)


class OrganizationStoreAppAppstore(UserStoreAppAppstore):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppVivo(UserStoreAppBase):

    def store_type(self):
        return StoreType.Vivo

    def get_serializer(self, data):
        return StoreAppVivoAuthSerializer(data=data)


class OrganizationStoreAppVivo(UserStoreAppVivo):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppHuawei(UserStoreAppBase):

    def store_type(self):
        return StoreType.Huawei

    def get_serializer(self, data):
        return StoreAppHuaweiStoreAuthSerializer(data=data)


class OrganizationStoreAppHuawei(UserStoreAppHuawei):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppXiaomi(UserStoreAppBase):

    def store_type(self):
        return StoreType.Xiaomi

    def get_serializer(self, data):
        return StoreAppXiaomiStoreAuthSerializer(data=data)


class OrganizationStoreAppXiaomi(UserStoreAppXiaomi):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserStoreAppYingyongbao(UserStoreAppBase):

    def store_type(self):
        return StoreType.Yingyongbao

    def get_serializer(self, data):
        return StoreAppYingyongbaoStoreAuthSerializer(data=data)


class OrganizationStoreAppYingyongbao(UserStoreAppYingyongbao):
    def get_namespace(self, path):
        return Namespace.organization(path)


def update_store_app_current_version(store_app):
    store = get_store(store_app.store)(store_app.auth_data)
    try:
        data = store.store_current()
        version = data["version"]
        if not version:
            return None
    except:  # noqa: E722
        return None

    try:
        ret = StoreAppVersionRecord.objects.get(
            app=store_app.app,
            store=store_app.store,
            short_version=version)
        ret.save()
    except StoreAppVersionRecord.DoesNotExist:
        ret = StoreAppVersionRecord.objects.create(
            app=store_app.app,
            store=store_app.store,
            short_version=version)
    return ret


class UserStoreAppCurrentVersion(APIView):

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(
            request.user, path, self.get_namespace(namespace)
        )
        stores = [
            StoreType.AppStore,
            StoreType.Huawei,
            StoreType.Vivo,
            StoreType.Xiaomi,
            StoreType.Yingyongbao
        ]
        versions = []
        for store in stores:
            ret = StoreAppVersionRecord.objects.filter(
                app__universal_app=app,
                store=store).order_by("-update_time").first()
            if ret:
                versions.append(ret)
        serializer = StoreAppVersionSerializer(versions, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        stores = [
            StoreType.AppStore,
            StoreType.Huawei,
            StoreType.Vivo,
            StoreType.Xiaomi,
            StoreType.Yingyongbao
        ]

        versions = []
        for store in stores:
            try:
                store_app = StoreApp.objects.get(app__universal_app=app, store=store)
            except StoreApp.DoesNotExist:
                continue

            ret = update_store_app_current_version(store_app)
            if ret:
                versions.append(ret)

        serializer = StoreAppVersionSerializer(versions, many=True)
        return Response(serializer.data)


class OrganizationStoreAppCurrentVersion(UserStoreAppCurrentVersion):

    def get_namespace(self, path):
        return Namespace.organization(path)


class AppStoreAppCurrentVersion(APIView):
    def get(self, request, country_code_alpha2, appstore_app_id):
        auth_data = {
            "country_code_alpha2": country_code_alpha2,
            "appstore_app_id": appstore_app_id,
        }
        store = AppStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class VivoStoreAppCurrentVersion(APIView):
    def get(self, request, vivo_store_app_id):
        auth_data = {
            "vivo_store_app_id": vivo_store_app_id,
        }
        store = VivoStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class HuaweiStoreAppCurrentVersion(APIView):
    def get(self, request):
        store_url = unquote(request.GET.get("store_url", ""))
        auth_data = {
            "store_url": store_url,
        }
        store = HuaweiStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class XiaomiStoreAppCurrentVersion(APIView):
    def get(self, request, xiaomi_store_app_id):
        auth_data = {
            "xiaomi_store_app_id": xiaomi_store_app_id,
        }
        store = XiaomiStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class YingyongbaoStoreAppCurrentVersion(APIView):
    def get(self, request):
        bundle_identifier = request.GET.get("bundle_identifier", "")
        auth_data = {
            "bundle_identifier": bundle_identifier,
        }
        store = YingyongbaoStore(auth_data)
        data = store.store_current()
        return Response(data, status=status.HTTP_200_OK)


class UserStoreAppList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(
            request.user, path, self.get_namespace(namespace)
        )
        store_app_list = StoreApp.objects.filter(app__universal_app=app)
        serializer = StoreAppSerializer(store_app_list, many=True)
        return Response(serializer.data)


class OrganizationStoreAppList(UserStoreAppList):
    def get_namespace(self, path):
        return Namespace.organization(path)
