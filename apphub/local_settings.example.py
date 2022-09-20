# flake8: noqa

# Copy the example configuration file from [apphub/local_settings.example.py](apphub/local_settings.example.py) to apphub/local_settings.py, or mount configuration file to apphub/local_settings.py if you deploy by docker.
# All settings in local_settings.example.py can be set by environment variables, too.
# Uncomment any settings you wish to config.

# SECRET_KEY
# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-SECRET_KEY
# A secret key for a particular Django installation. This is used to provide cryptographic signing, and should be set to a unique, unpredictable value. # noqa: E501
# You can generate by python code
# ``` python
# python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'  # noqa: E501
# ```
# SECRET_KEY = "your secret key"

# DEBUG_MODE
# Default: False
# A boolean that turns on/off debug mode.
# DEBUG_MODE = False

# EXTERNAL_WEB_URL
# Default: 'http://localhost:8000'
# The [dashboard](https://github.com/myapphub/dashboard) access url.
# Users use the url to access apphub website.
# EXTERNAL_WEB_URL = 'http://localhost:8000'

# EXTERNAL_API_URL
# Default: 'http://localhost:8000/api'
# The apphub api base url, used by dashbaord.
# This url is the apphub backend api endpoint.
# EXTERNAL_API_URL = ''

# TIME_ZONE
# Default: 'America/Chicago'
# A string representing the time zone for this installation. See the list https://en.wikipedia.org/wiki/List_of_tz_database_time_zones # noqa: E501
# TIME_ZONE = 'America/Chicago'

# LANGUAGE_CODE
# Default: 'en-us'
# A string representing the language code for this installation.
# LANGUAGE_CODE = 'en-us'


# Email settings

# EMAIL_HOST
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host
# Default: 'localhost'
# The host to use for sending email.
# EMAIL_HOST = 'localhost'

# EMAIL_PORT
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-port
# Default: 25
# Port to use for the SMTP server defined in EMAIL_HOST.
# EMAIL_PORT = 25

# EMAIL_USE_SSL
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-use-tls
# Default: False
# Whether to use a TLS (secure) connection when talking to the SMTP server.
# EMAIL_USE_SSL = False

# EMAIL_HOST_USER
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-user
# Default: '' (Empty string)
# Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won’t attempt authentication. # noqa: E501
# EMAIL_HOST_USER = ''

# EMAIL_HOST_PASSWORD
# https://docs.djangoproject.com/en/4.0/ref/settings/#email-host-password
# Default: '' (Empty string)
# Password to use for the SMTP server defined in EMAIL_HOST.
# EMAIL_HOST_PASSWORD = ''

# DEFAULT_FROM_EMAIL
# https://docs.djangoproject.com/en/4.0/ref/settings/#std-setting-DEFAULT_FROM_EMAIL
# Default: 'webmaster@localhost'
# Default email address to use for various automated correspondence from the site manager(s).
# DEFAULT_FROM_EMAIL = 'webmaster@localhost'


# Database settings
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES_ENGINE
# Default: 'django.db.backends.sqlite3'
# The database backend to use.
# Options:
#   - 'django.db.backends.sqlite3
#   - 'django.db.backends.mysql'
#   - 'django.db.backends.postgresql'
# DATABASES_ENGINE = ''

# DATABASE_NAME
# Default: '' (Empty string)
# The name of the database to use. For SQLite, it’s the full path to the database file.
# DATABASE_NAME = ''

# DATABASE_HOST
# Default: '' (Empty string)
# Which host to use when connecting to the database. An empty string means localhost. Not used with SQLite.
# DATABASE_HOST = 0

# DATABASE_PORT
# Default: '' (Empty string)
# The port to use when connecting to the database. An empty string means the default port. Not used with SQLite.
# DATABASE_PORT = 0

# DATABASE_USER
# Default: '' (Empty string)
# The username to use when connecting to the database. Not used with SQLite.
# DATABASE_USER = ''

# DATABASE_PASSWORD
# Default: '' (Empty string)
# The passowrd to use when connecting to the database. Not used with SQLite.
# DATABASE_PASSWORD = ''


# Auth settings

# ENABLE_EMAIL_ACCOUNT
# Default: True
# Enable email login, and email should be verified
# ENABLE_EMAIL_ACCOUNT = True

# ACCOUNT_EMAIL_DOMAIN
# Default: '' (Empty string)
# ACCOUNT_EMAIL_DOMAIN = ''


# SOCIAL_ACCOUNT
# Default: ''
# Social account type list, separate with comma, example "feishu,slack,dingtalk"
# Options:
#   - 'feishu'
#   - 'slack'
#   - 'dingtalk'
#   - 'wecom'
#   - 'teams'
#   - 'gitlab'
#   - 'github'
# SOCIAL_ACCOUNT = ''

# FEISHU_APP_ID = ''
# FEISHU_APP_SECRET = ''

# SLACK_CLIENT_ID = ''
# SLACK_CLIENT_SECRET = ''

# DINGTALK_AGENT_ID = ''
# DINGTALK_APP_KEY = ''
# DINGTALK_APP_SECRET = ''

# WECOM_AGENT_ID = ''
# WECOM_CORP_ID = ''
# WECOM_APP_SECRET = ''

# GITHUB_CLIENT_ID = ''
# GITHUB_CLIENT_SECRET = ''

# GITLAB_CLIENT_ID = ''
# GITLAB_CLIENT_SECRET = ''
# GITLAB_URL = 'https://gitlab.com'


# Storage settings

# MEDIA_ROOT
# Default: 'var/media/'
# Absolute filesystem path to the directory that will hold user-uploaded files.
# MEDIA_ROOT = 'var/media/'

# MEDIA_URL
# Default: EXTERNAL_WEB_URL + '/media/'
# URL that handles the media served from MEDIA_ROOT, used for managing stored files.
# MEDIA_URL = EXTERNAL_WEB_URL + '/media/'

# STORAGE_TYPE
# Default: 'LocalFileSystem'
# Default file storage class to be used for any file-related operations that don’t specify a particular storage system. # noqa: E501
# Options:
#   - 'LocalFileSystem'
#   - 'AmazonAWSS3'
#   - 'AzureBlobStorage'
#   - 'GoogleCloudStorage
#   - 'AlibabaCloudOSS'
#   - 'TencentCOS'
# STORAGE_TYPE = 'LocalFileSystem'


# AlibabaCloudOSS settings
# ALIYUN_OSS_ACCESS_KEY_ID = ''
# ALIYUN_OSS_ACCESS_KEY_SECRET = ''
# ALIYUN_OSS_BUCKET_NAME = ''
# ALIYUN_OSS_PUBLIC_READ = False
# ALIYUN_OSS_ENDPOINT = ''

# AmazonAWSS3 S3
# AWS_STORAGE_ACCESS_KEY_ID = ''
# AWS_STORAGE_SECRET_ACCESS_KEY = ''
# AWS_STORAGE_PUBLIC_READ = False
# AWS_STORAGE_BUCKET_NAME = ''
# AWS_STORAGE_REGION_NAME = 'us-east-1'
# AWS_CLOUDFRONT_KEY = ''
# AWS_CLOUDFRONT_KEY_ID = ''
