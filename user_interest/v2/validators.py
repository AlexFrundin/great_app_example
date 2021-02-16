from validator import Validator

from config.messages import Messages


class InputUserSuggestValidator(Validator):
    user_id = 'required|numberic'
    page_limit = 'required|digits'
    page_offset = 'required|digits'

    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")
        },
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page offset")
        }
    }
