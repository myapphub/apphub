import requests
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.client import (OAuth2Client,
                                                           OAuth2Error)
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from dj_rest_auth.registration.views import SocialConnectView
from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlencode

from user.integration.base import BaseSocialLoginView
from util.name import parse_name


class WecomAccount(ProviderAccount):
    def get_avatar_url(self):
        return self.account.extra_data.get("avatar")

    def to_str(self):
        return self.account.extra_data.get(
            "name", super(WecomAccount, self).to_str()
        )


class CustomWecomProvider(OAuth2Provider):
    id = "custom_wecom"
    name = "wecom"
    account_class = WecomAccount

    def extract_uid(self, data):
        return data["userid"]

    def extract_common_fields(self, data):
        first_name, last_name = parse_name(data.get("name", ""))
        return dict(
            username=data.get("userid"),
            name=data.get("name"),
            first_name=first_name,
            last_name=last_name,
            email=data.get("email", None),
        )


class WecomOAuth2Client(OAuth2Client):

    def get_redirect_url(self, authorization_url, extra_params):
        if extra_params.get("inwxwork", None):
            url = "https://open.weixin.qq.com/connect/oauth2/authorize"
            params = {
                "appid": self.consumer_key,
                "redirect_uri": self.callback_url,
                "scope": self.scope,
                "response_type": "code",
                "agentid": extra_params["agentid"]
            }
            return "%s?%s#wechat_redirect" % (url, urlencode(params))
        else:
            params = {
                "appid": self.consumer_key,
                "redirect_uri": self.callback_url
            }
            if self.state:
                params["state"] = self.state
            params.update(extra_params)
            return "%s?%s" % (authorization_url, urlencode(params))

    def get_access_token(self, code):
        token_cache_key = "wecom_access_token"
        wecom_access_token = cache.get(token_cache_key)
        if wecom_access_token:
            return {
                "access_token": wecom_access_token["access_token"],
                "expires_in": wecom_access_token["expires_in"],
                "code": code
            }
        # TODO: cache token
        data = {
            "corpid": self.consumer_key,
            "corpsecret": self.consumer_secret,
        }
        url = self.access_token_url
        # TODO: Proper exception handling
        resp = requests.get(url, params=data)
        resp.raise_for_status()
        access_token = resp.json()
        if not access_token or "access_token" not in access_token:
            raise OAuth2Error("Error retrieving access token: %s" % resp.content)
        cache.set(token_cache_key, access_token, access_token["expires_in"])
        return {
            "access_token": access_token["access_token"],
            "expires_in": access_token["expires_in"],
            "code": code
        }


class CustomWecomOAuth2Adapter(OAuth2Adapter):
    provider_id = CustomWecomProvider.id

    authorize_url = "https://open.work.weixin.qq.com/wwopen/sso/qrConnect"
    access_token_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    user_info_url = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"

    def complete_login(self, request, app, token, **kwargs):
        params = {
            "access_token": token.token,
            "code": kwargs["response"]["code"]
        }
        resp = requests.get(self.user_info_url, params=params)
        resp.raise_for_status()
        extra_data = resp.json()
        if extra_data.get("errcode", 0) != 0:
            errcode = extra_data.get("errcode", 0)
            if errcode == 42001 or errcode == 40014:
                token_cache_key = "wecom_access_token"
                cache.delete(token_cache_key)
            raise OAuth2Error("Error retrieving code: %s" % resp.content)

        user_ticket = extra_data.get("user_ticket", "")
        if user_ticket:
            params2 = {
                "access_token": token.token,
            }
            user_info_url2 = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserdetail"
            payload = {
                "user_ticket": user_ticket
            }
            resp2 = requests.post(user_info_url2, params=params2, json=payload)
        else:
            user_info_url2 = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
            params2 = {
                "access_token": token.token,
                "userid": extra_data["userid"]
            }
            resp2 = requests.get(user_info_url2, params=params2)

        if resp2.json().get("errcode", 0) != 0:
            raise OAuth2Error("Error retrieving code: %s" % resp2.content)
        extra_data = resp2.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


class WecomLogin(BaseSocialLoginView):
    adapter_class = CustomWecomOAuth2Adapter
    client_class = WecomOAuth2Client
    callback_url = settings.EXTERNAL_WEB_URL + "/user/auth/wecom/redirect"

    def register_provider(self):
        providers.registry.register(CustomWecomProvider)

    def authorize_extra_params(self, provider):
        params = {
            "agentid": provider.get_settings().get("agent_id", "")
        }
        user_agent = self.request.headers.get("User-Agent", "")
        if user_agent.find(" wxwork/") != -1:
            params["inwxwork"] = True
        return params


class WecomConnect(SocialConnectView):
    adapter_class = CustomWecomOAuth2Adapter
