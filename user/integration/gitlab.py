from allauth.socialaccount import providers
from allauth.socialaccount.providers.gitlab.views import (GitLabOAuth2Adapter,
                                                          GitLabProvider)
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class CustomGitLabProvider(GitLabProvider):
    id = "custom_gitlab"

    def extract_common_fields(self, data):
        ret = super().extract_common_fields(data)
        first_name, last_name = parse_name(ret.get("name", ""))
        ret["first_name"] = first_name
        ret["last_name"] = last_name
        return ret


class CustomGitLabOAuth2Adapter(GitLabOAuth2Adapter):
    provider_id = CustomGitLabProvider.id


class GitLabLogin(BaseSocialLoginView):
    adapter_class = CustomGitLabOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/gitlab/redirect"

    def register_provider(self):
        providers.registry.register(CustomGitLabProvider)


class GitLabConnect(SocialConnectView):
    adapter_class = GitLabOAuth2Adapter
