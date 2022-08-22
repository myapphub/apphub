import os

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

try:
    import oss2
except:  # noqa: E722
    pass

try:
    from system.info import info

    info["time"] = parse_datetime(info["time"])
except:  # noqa: E722
    info = {"time": timezone.now(), "commit_id": ""}


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def info_api(request):
    data = {
        "name": "AppHub",
        "version": "0.1.0",
        "time": timezone.make_aware(timezone.make_naive(info["time"])),
        "commit_id": info["commit_id"],
    }
    return Response(data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def current(request):
    data = {
        "time": timezone.make_aware(timezone.make_naive(timezone.now())),
    }
    return Response(data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def backup(request):
    if settings.DATABASES_ENGINE == "django.db.backends.sqlite3":
        database_name = settings.DATABASES["default"]["NAME"]
        access_key_id = settings.ALIYUN_OSS_ACCESS_KEY_ID
        access_key_secret = settings.ALIYUN_OSS_ACCESS_KEY_SECRET
        end_point = settings.ALIYUN_OSS_ENDPOINT
        bucket_name = settings.ALIYUN_OSS_BUCKET_NAME
        auth = oss2.AuthV2(access_key_id, access_key_secret)
        endpoint_is_cname = False if end_point.endswith(".aliyuncs.com") else True
        bucket = oss2.Bucket(auth, end_point, bucket_name, is_cname=endpoint_is_cname)
        remote_db_file = str(database_name)
        if remote_db_file.startswith("/"):
            remote_db_file = remote_db_file[1:]
        if settings.MEDIA_ROOT:
            prefix = settings.MEDIA_ROOT
            if prefix.startswith("/"):
                prefix = prefix[1:]
            remote_db_file = os.path.join(prefix, remote_db_file)
        if database_name and os.path.isfile(database_name):
            bucket.put_object_from_file(remote_db_file, database_name)

    return Response({})
