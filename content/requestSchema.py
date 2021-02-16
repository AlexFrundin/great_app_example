from validator import Validator
from config.messages import Messages

# this class is use for validation
class SearchListValidator(Validator):
    search_text = 'required'
    message = {
        'search_text': {
            'required': Messages.IS_REQUIRED.format(field_name="Search Text")
        }
    }