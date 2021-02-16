from validator import Validator
from config.messages import Messages

class UserListValidator(Validator):
    user_id = 'required|numberic'
    page_limit = 'required|digits'

    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")
        },
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page limit")
        }
    }

class AddRemoveInterestValidator(Validator):
    user_id = 'required|numberic'
    interested_user_id = 'required|numberic'

    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")
        },
        'interested_user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Interested User Id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Interested User Id")
        },
    }

class ApproveRejectValidator(Validator):
    event_id = 'required|numberic'

    message = {
        'event_id': {
            'required': Messages.IS_REQUIRED.format(field_name="event id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="event id")
        }
    }