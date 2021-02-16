from validator import Validator
from config.messages import Messages


# this class is use for validattion
class LoginValidator(Validator):
    email = 'required|email'
    device_type = 'required|numberic'
    user_role_id = 'required|numberic'

    message = {
        'email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL
        },
        'device_type': {
            'required': Messages.IS_REQUIRED.format(field_name="Device type"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Device type")
        },
        'user_role_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User role id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User role id")
        }
    }


# this class is use for validattion
class SocialLoginValidator(Validator):
    social_login_id = 'required|numberic'
    device_type = 'required|numberic'
    social_token = 'required'
    user_role_id = 'required|numberic'

    message = {
        'social_login_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Social Login ID"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Social Login ID")
        },
        'device_type': {
            'required': Messages.IS_REQUIRED.format(field_name="Device type"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Device type")
        },
        'social_token': {
            'required': Messages.IS_REQUIRED.format(field_name="Social Token"),
        },
        'user_role_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User role id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User role id")
        }
    }

# this class is use for validation
class SignupValidator(Validator):
    name = 'required'
    email = 'required|email'
    password = 'required'
    device_token = 'required'
    device_type = 'required'
    user_causes = 'required'
    user_sub_causes = 'required'

    message = {
        'name': {'required': Messages.IS_REQUIRED.format(field_name="Name")},
        'email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL
        },
        'password': {
            'required': Messages.IS_REQUIRED.format(field_name="Password")
        },
        'device_token': {'required': Messages.IS_REQUIRED.format(field_name="Device Token")},
        'device_type': {
            'required': Messages.IS_REQUIRED.format(field_name="Device Type"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Device Type")
        }
    }

# this class is use for apple sign in validation
class AppleSignupValidator(Validator):
    password = 'required'
    device_token = 'required'
    device_type = 'required'
    user_causes = 'required'

    message = {
        'password': {
            'required': Messages.IS_REQUIRED.format(field_name="Password")
        },
        'device_token': {'required': Messages.IS_REQUIRED.format(field_name="Device Token")},
        'device_type': {
            'required': Messages.IS_REQUIRED.format(field_name="Device Type"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Device Type")
        }
    }

# this class is use for validation
class ForgotValidator(Validator):
    email = 'required|email'
    message = {
        'email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL
        }
    }


class ResetValidator(Validator):
    tokenValue = 'required'
    token = 'required'
    password = 'required'
    message = {
        'tokenValue': {
            'required': Messages.IS_REQUIRED.format(field_name="tokenValue")
        },
        'token': {
            'required': Messages.IS_REQUIRED.format(field_name="token")
        },
        'password': {
            'required': Messages.IS_REQUIRED.format(field_name="password")
        }
    }


# this class is use for refresh Token validation
class RefreshValidator(Validator):
    refresh_token = 'required'
    message = {
        'refresh_token': {
            'required': Messages.IS_REQUIRED.format(field_name="Refresh token")
        }
    }


# this class is use for refresh Token validation
class ChangePasswordValidator(Validator):
    password = 'required'
    new_password = 'required'
    message = {
        'password': {
            'required': Messages.IS_REQUIRED.format(field_name="Old password")
        },
        'new_password': {
            'required': Messages.IS_REQUIRED.format(field_name="New password")
        }
    }


# this class is use for validattion
class UsernameValidator(Validator):
    username = 'required|max_length:150'
    message = {
        'username': {
            'required': Messages.IS_REQUIRED.format(field_name="Username"),
            'max_length': Messages.MAXIMUM_LIMIT_OF_CHARACTERS
        }
    }


# this class is use for validattion
class CheckPasswordValidator(Validator):
    password = 'required|max_length:150'
    message = {
        'password': {
            'required': Messages.IS_REQUIRED.format(field_name="Password")
        }
    }


# this class is use for validattion
class AccessTokenValidator(Validator):
    user_id = 'required|numberic'
    device_id = 'required'
    refresh_token = 'required'

    message = {
        'user_id': {'required': Messages.IS_REQUIRED.format(field_name="User id"),
                    'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")},
        'device_id': {'required': Messages.IS_REQUIRED.format(field_name="Device id")},
        'refresh_token': {'required': Messages.IS_REQUIRED.format(field_name="Refresh token")}
    }


class VerifyOtpValidator(Validator):
    user_email = 'required|email'
    otp = 'required|numberic'

    message = {
        'user_email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL
        },
        'otp': {
            'required': Messages.IS_REQUIRED.format(field_name="OTP"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="OTP")
        },
    }


class ResendOtpValidator(Validator):
    user_email = 'required|email'

    message = {
        'user_email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL
        }
    }


# block-unblock user id
class BlockUnblockValidator(Validator):
    blocked_user_id = 'required|numberic'

    message = {
        'blocked_user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Blocked User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Blocked User id")
        }
    }


# Change Setting of app user
class SettingToggleValidator(Validator):
    request_type = 'required|max_length:20'

    message = {
        'request_type': {
            'required': Messages.IS_REQUIRED.format(field_name="request_type"),
            'max_length': Messages.MAX_LENGTH.format(field_name="request_type", max_value="20")
        }
    }


# Change Setting of app user
class UserBlockedValidator(Validator):
    page_limit = 'required|decimal'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        }
    }


# Change Setting of app user
class InterestedUserListValidator(Validator):
    type = 'required|numberic|between:1, 2'
    page_limit = 'required|numberic'
    page_offset = 'required|digits'
    user_id = 'required|digits'

    message = {
        'type': {
            'required': Messages.IS_REQUIRED.format(field_name="Type"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Type"),
            'between': Messages.SHOULD_BE_BETWEEN.format(field_name="Type", min_value=1, max_value=2)
        },
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Offset")
        },
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User Id"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="User Id")
        }
    }
