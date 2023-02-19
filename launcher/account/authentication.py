from rest_framework.authentication import TokenAuthentication

from .services import AccountService

account_service = AccountService()


class JWTAuthentication(TokenAuthentication):
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        user = account_service.authenticate_by_access_token(access_token=key)
        return user, user.account
