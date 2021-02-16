from config.messages import Messages
from validator import Validator


class CausesValidator(Validator):
    causes = 'required'


class SubCausesValidator(Validator):
    subcauses = 'required'


class ListValidator(Validator):
    page_limit = 'required|numberic'
    page_offset = 'required|digits'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Limit")
        },
        'page_offset': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Offset"),
            'digits': Messages.SHOULD_BE_NUMERIC.format(field_name="Post Offset")
        },
    }
