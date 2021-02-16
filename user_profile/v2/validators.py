from validator import Validator
from config.messages import Messages


class EditProfileValidator(Validator):
    name = 'required'
    user_causes = 'required'

    message = {
        'name': {'required': Messages.IS_REQUIRED.format(field_name="Name")}
    }

class UserPostListValidator(Validator):
    page_limit = 'required|decimal'
    page_offset = 'required|digits'
    id = 'required'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'decimal': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Page offset")
        }
    }
