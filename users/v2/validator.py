# this class is use for validation
from validator import Validator, BaseRule
from validator.validators import default_rules
from datetime import date
from config.messages import Messages


class AgeValidator(BaseRule):
    age = 13
    name = 'gt_13'
    message = "You need to be at least 13 years old"
    description = "validate user age"

    def check_value(self):
        current_year = date.today().year
        age = current_year - int(self.field_value)
        self.status = age >= self.age

    def check_null(self):
        pass


default_rules.update({AgeValidator.get_name(): AgeValidator})


class SignupValidator(Validator):
    name = 'required'
    email = 'required|email'
    password = 'required'
    device_token = 'required'
    device_type = 'required'

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


class PreDataValidator(Validator):
    email = 'required|email|unique:users.User, email'
    dob = 'gt_13'

    message = {
        'email': {
            'required': Messages.IS_REQUIRED.format(field_name="Email"),
            'email': Messages.EMAIL_NOT_EMAIL,
            'unique': Messages.EMAIL_EXITS,
        },
        'dob': {
            'required': Messages.IS_REQUIRED.format(field_name="dob")
        }
    }
