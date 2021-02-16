from validator import Validator
from config.messages import Messages


# this class is use for edit profile validation
class NotificationListValidator(Validator):
    page_limit = 'required|numberic'
    page_offset = 'required|digits'

    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Offset")
        }
    }

# this class is use for report user profile validation
class ReportUserProfile(Validator):
    user_id = 'required|numberic'
    reason_id = 'required|numberic'

    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="user_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="user_id")
        },
        'reason_id': {
            'required': Messages.IS_REQUIRED.format(field_name="reason_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="reason_id")
        }
    }

# this class is use for validattion
class OtherUserSavedPostListValidator(Validator):
    user_id = 'required|numberic'
    page_limit = 'required|decimal'
    page_offset = 'required|digits'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="user_id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="user_id")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Offset")
        }
    }
