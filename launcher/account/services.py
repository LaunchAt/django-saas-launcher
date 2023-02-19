import datetime
from typing import Dict, Optional

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import check_password, make_password
from django.utils.timezone import now

from launcher.services import BaseService

from . import signals
from .models import (
    Account,
    EmailChangeCode,
    PasswordResetCode,
    PhoneNumberChangeCode,
    SignupCode,
)

User: AbstractBaseUser = get_user_model()

JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)

JWT_EXPIRATION_TIME = getattr(settings, 'JWT_EXPIRATION_TIME', 3600)

JWT_REFRESH_EXPIRATION_TIME = getattr(settings, 'JWT_REFRESH_EXPIRATION_TIME', 2592000)


def generate_token(subject: str, expiration_time: int) -> str:
    """
    Generates a JSON Web Token (JWT) with the provided subject and expiration time.

    Args:
        subject (str):
            The subject of the token, representing the entity to which the token refers.
        expiration_time (int):
            The number of seconds from now after which the token will expire.

    Returns:
        str: The encoded JWT as a string.
    """
    issued_at = now()
    return jwt.encode(
        {
            'sub': subject,
            'exp': issued_at + datetime.timedelta(seconds=expiration_time),
            'iat': issued_at,
        },
        JWT_SECRET_KEY,
        algorithm='HS256',
    )


class AccountService(BaseService):
    def signup_with_email(
        self,
        *,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> User:
        """
        Sign up a user with email and password.

        Args:
            email (Optional[str]): The user's email address. Defaults to None.
            password (Optional[str]): The user's password. Defaults to None.

        Returns:
            User: A new User object.
        """
        try:
            account = Account.objects.get_by_natural_key(email)
            user = account.user
        except Account.DoesNotExist:
            user = User.objects.create_user(email, email=email, password=password)
            user.account = Account.objects.create(
                user=user,
                email=email,
                password=make_password(password),
            )
        else:
            if account.is_verified:
                self.bad_request(code='email_already_taken')
        signup_code, is_created = SignupCode.objects.get_or_create(user=user)
        if not is_created:
            signup_code.refresh()
        signals.signup(sender=self, account=user.account, code=signup_code)
        return user

    def signup_with_phone_number(
        self,
        *,
        phone_number: Optional[str] = None,
        password: Optional[str] = None,
    ) -> User:
        """
        Sign up a new user with a phone number and password.

        Args:
            phone_number (Optional[str]): The user's phone number.
            password (Optional[str]): The user's password.

        Returns:
            The newly created user object.
        """
        try:
            account = Account.objects.get_by_natural_key(phone_number)
            user = account.user
        except Account.DoesNotExist:
            user = User.objects.create_user(phone_number, password=password)
            user.account = Account.objects.create(
                user=user,
                phone_number=phone_number,
                password=make_password(password),
            )
        else:
            if account.is_verified:
                self.bad_request(code='phone_number_already_taken')
        signup_code, is_created = SignupCode.objects.get_or_create(user=user)
        if not is_created:
            signup_code.refresh()
        signals.signup(sender=self, account=user.account, code=signup_code)
        return user

    def resend_signup_code(self, *, account_id: Optional[str] = None) -> None:
        """
        Resend a signup code to the user's account.

        Args:
            account_id (Optional[str]): The ID of the user's account.
        """
        try:
            queryset = Account.objects.filter(id=account_id)
            account = queryset.active_set().select_related('user').get()
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if account.is_verified:
            self.bad_request(code='already_verified')
        signup_code, is_created = SignupCode.objects.get_or_create(user=account.user)
        if not is_created:
            signup_code.refresh()
        signals.signup(sender=self, account=account, code=signup_code)

    def verify_signup(
        self,
        *,
        account_id: Optional[str] = None,
        code: Optional[str] = None,
    ) -> None:
        """
        Verify the user's account with the provided code.

        Args:
            account_id (Optional[str]): The ID of the user's account.
            code (Optional[str]): The verification code.
        """
        assert account_id and code
        try:
            queryset = Account.objects.filter(id=account_id)
            user = queryset.active_set().select_related('user').get()
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if user.account.is_verified:
            self.bad_request(code='already_verified')
        try:
            signup_code: SignupCode = SignupCode.objects.get(user=user)
        except SignupCode.DoesNotExist:
            self.unauthorized(code='invalid_code')
        if signup_code.is_expired:
            self.unauthorized(code='code_expired')
        if signup_code.base_32_code == code or signup_code.six_digits_code == code:
            user.account.update(is_verified=True)
            signup_code.delete()
        else:
            self.unauthorized(code='invalid_code')

    def signin(
        self,
        *,
        email: Optional[str] = None,
        password: Optional[str] = None,
        phone_number: Optional[str] = None,
        username: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Authenticates a user by email, phone number or username and password.

        Args:
            email (Optional[str]): The email address of the user.
            password (Optional[str]): The password of the user.
            phone_number (Optional[str]): The phone number of the user.
            username (Optional[str]): The username of the user.

        Returns:
            Dict[str, str]:
                A dictionary containing the access_token and refresh_token
                if the user is authenticated.
        """
        assert email or phone_number or username
        try:
            identifier = email or phone_number or username
            account = Account.objects.get_by_natural_key(identifier)
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if not account.is_verified:
            self.unauthorized(code='account_not_verified')
        if not check_password(password, account.password):
            self.unauthorized(code='invalid_password')
        if not account.user.is_active:
            self.unauthorized(code='user_suspended')
        access_token = generate_token(account.id.hex, JWT_EXPIRATION_TIME)
        refresh_token = generate_token(account.id.hex, JWT_REFRESH_EXPIRATION_TIME)
        return {'access_token': access_token, 'refresh_token': refresh_token}

    def authenticate_by_access_token(
        self,
        *,
        access_token: Optional[str] = None,
    ) -> User:
        """
        Authenticates a user by the access token.

        Args:
            access_token (Optional[str]): The access token.

        Returns:
            User: The authenticated user.
        """
        assert access_token is not None
        try:
            payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            self.unauthorized(code='token_expired')
        except jwt.InvalidTokenError:
            self.unauthorized(code='invalid_token')
        try:
            account = Account.objects.select_related('user').get(id=payload.get('sub'))
        except Account.DoesNotExist:
            self.unauthorized(code='invalid_token')
        if account.is_deleted:
            self.unauthorized(code='user_deleted')
        if not account.user.is_active:
            self.unauthorized(code='user_suspended')
        return account.user

    def refresh_access_token(
        self,
        *,
        refresh_token: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Refreshes access token using refresh token and returns the new access and
        refresh token.

        Args:
            refresh_token (Optional[str]): A JWT refresh token string.

        Returns:
            Dict[str, str]: A dictionary containing new access and refresh tokens.
        """
        assert refresh_token is not None
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            self.bad_request(code='token_expired')
        except jwt.InvalidTokenError:
            self.bad_request(code='invalid_token')
        try:
            account = Account.objects.select_related('user').get(id=payload.get('sub'))
        except Account.DoesNotExist:
            self.bad_request(code='invalid_token')
        if account.is_deleted:
            self.bad_request(code='user_deleted')
        if not account.user.is_active:
            self.bad_request(code='user_suspended')
        access_token = generate_token(account.id.hex, JWT_EXPIRATION_TIME)
        refresh_token = generate_token(account.id.hex, JWT_REFRESH_EXPIRATION_TIME)
        return {'access_token': access_token, 'refresh_token': refresh_token}

    def reset_password_with_email(self, *, email: Optional[str] = None) -> None:
        """
        Sends password reset email to the account with the given email.

        Args:
            email (Optional[str]): An email address string to reset the password.
        """
        try:
            account = Account.objects.get_by_natural_key(email)
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if not account.is_verified:
            self.unauthorized(code='account_not_verified')
        password_reset_code, is_created = PasswordResetCode.objects.get_or_create(
            user=account.user,
        )
        if not is_created:
            password_reset_code.refresh()
        signals.password_reset(sender=self, account=account, code=password_reset_code)

    def reset_password_with_phone_number(
        self,
        *,
        phone_number: Optional[str] = None,
    ) -> None:
        """
        Sends password reset SMS to the account with the given phone number.

        Args:
            phone_number (Optional[str]): A phone number string to reset the password.
        """
        try:
            account = Account.objects.get_by_natural_key(phone_number)
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if not account.is_verified:
            self.unauthorized(code='account_not_verified')
        password_reset_code, is_created = PasswordResetCode.objects.get_or_create(
            user=account.user,
        )
        if not is_created:
            password_reset_code.refresh()
        signals.password_reset(sender=self, account=account, code=password_reset_code)

    def verify_reset_password(
        self,
        *,
        code: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        phone_number: Optional[str] = None,
        username: Optional[str] = None,
    ) -> None:
        """
        Verify reset password code.

        Args:
            code (Optional[str]): Password reset code string.
            email (Optional[str]): Email string.
            password (Optional[str]): New password string.
            phone_number (Optional[str]): Phone number string.
            username (Optional[str]): Username string.
        """
        try:
            identifier = email or phone_number or username
            account = Account.objects.get_by_natural_key(identifier)
        except Account.DoesNotExist:
            self.not_found(code='not_found')
        if not account.is_verified:
            self.bad_request(code='account_not_verified')
        try:
            password_reset_code = PasswordResetCode.objects.get(user=account.user)
        except PasswordResetCode.DoesNotExist:
            self.unauthorized(code='invalid_code')
        if password_reset_code.is_expired:
            self.unauthorized(code='code_expired')
        if (
            password_reset_code.base_32_code == code
            or password_reset_code.six_digits_code == code
        ):
            account.update(password=make_password(password))
            password_reset_code.delete()
        else:
            self.unauthorized(code='invalid_code')

    def change_password(
        self,
        *,
        user: Optional[User] = None,
        old_password: Optional[str] = None,
        new_password: Optional[str] = None,
    ) -> None:
        """
        Change the password of the given user.

        Args:
            user (Optional[User]): The user whose password should be changed.
            old_password (Optional[str]): The current password of the user.
            new_password (Optional[str]): The new password to be set.
        """
        assert user and old_password and new_password
        if not check_password(old_password, user.account.password):
            self.unauthorized(code='invalid_password')
        user.account.update(password=make_password(new_password))

    def change_email(
        self,
        *,
        user: Optional[User] = None,
        email: Optional[str] = None,
    ) -> None:
        """
        Change the email address of the given user.

        Args:
            user (Optional[User]): The user whose email address should be changed.
            email (Optional[str]): The new email address to be set.
        """
        assert user and email
        try:
            email_change_code = EmailChangeCode.objects.get(user=user)
        except EmailChangeCode.DoesNotExist:
            email_change_code = EmailChangeCode.objects.create(user=user, email=email)
        else:
            email_change_code.refresh(email)
        user.account.email = email
        signals.email_change(sender=self, account=user.account, code=email_change_code)

    def verify_change_email(
        self,
        *,
        code: Optional[str] = None,
        user: Optional[User] = None,
    ) -> User:
        """
        Verify and apply the email address change for the given user.

        Args:
            user (Optional[User]): The user whose email address is being changed.
            code (Optional[str]):
                The verification code sent to the user's new email address.

        Returns:
            User: The updated user object.
        """
        assert user and code
        try:
            email_change_code = EmailChangeCode.objects.get(user=user)
        except EmailChangeCode.DoesNotExist:
            self.unauthorized(code='invalid_code')
        if email_change_code.is_expired:
            self.unauthorized(code='code_expired')
        if (
            email_change_code.base_32_code == code
            or email_change_code.six_digits_code == code
        ):
            user.account.update(email=email_change_code.email)
            email_change_code.delete()
            return user
        self.unauthorized(code='invalid_code')

    def change_phone_number(
        self,
        *,
        user: Optional[User] = None,
        phone_number: Optional[str] = None,
    ) -> None:
        """
        Change the phone number of the given user.

        Args:
            user (Optional[User]): The user whose phone number should be changed.
            phone_number (Optional[str]): The new phone number to be set.
        """
        assert user and phone_number
        try:
            phone_number_change_code = PhoneNumberChangeCode.objects.get(user=user)
        except PhoneNumberChangeCode.DoesNotExist:
            phone_number_change_code = PhoneNumberChangeCode.objects.create(
                user=user,
                phone_number=phone_number,
            )
        else:
            phone_number_change_code.refresh(phone_number)
        user.account.phone_number = phone_number
        signals.phone_number_change(
            sender=self,
            account=user.account,
            code=phone_number_change_code,
        )

    def verify_change_phone_number(
        self,
        *,
        code: Optional[str] = None,
        user: Optional[User] = None,
    ) -> User:
        """
        Verify the phone number change code provided by the user.

        Args:
            code (Optional[str]): The code to verify.
            user (Optional[User]): The user to change the phone number for.

        Returns:
            User: The updated user object.
        """
        assert user and code
        try:
            phone_number_change_code = PhoneNumberChangeCode.objects.get(user=user)
        except PhoneNumberChangeCode.DoesNotExist:
            self.unauthorized(code='invalid_code')
        if phone_number_change_code.is_expired:
            self.unauthorized(code='code_expired')
        if (
            phone_number_change_code.base_32_code == code
            or phone_number_change_code.six_digits_code == code
        ):
            user.account.update(phone_number=phone_number_change_code.phone_number)
            phone_number_change_code.delete()
            return user
        self.unauthorized(code='invalid_code')

    def change_username(
        self,
        *,
        user: Optional[User] = None,
        username: Optional[str] = None,
    ) -> User:
        """
        Change the username for the specified user.

        Args:
            user (Optional[User]): The user to change the username for.
            username (Optional[str]): The new username.

        Returns:
            User: The updated user object.
        """
        assert user and username
        try:
            account = Account.objects.get_by_natural_key(username)
        except Account.DoesNotExist:
            pass
        else:
            if account.id != user.account_id:
                self.bad_request(code='username_already_taken')
        account.update(username=username)
        user.account = account
        return user
