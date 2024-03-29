from allauth.socialaccount import providers
from allauth.socialaccount.providers.github.views import (GitHubOAuth2Adapter,
                                                          GitHubProvider)
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class CustomGitHubProvider(GitHubProvider):
    id = "custom_github"

    def extract_common_fields(self, data):
        ret = super().extract_common_fields(data)
        first_name, last_name = parse_name(ret.get("name", ""))
        ret["first_name"] = first_name
        ret["last_name"] = last_name
        return ret


class CustomGitHubOAuth2Adapter(GitHubOAuth2Adapter):
    provider_id = CustomGitHubProvider.id


class GitHubLogin(BaseSocialLoginView):
    adapter_class = CustomGitHubOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/github/redirect"

    def register_provider(self):
        providers.registry.register(CustomGitHubProvider)


class GitHubConnect(SocialConnectView):
    adapter_class = GitHubOAuth2Adapter
