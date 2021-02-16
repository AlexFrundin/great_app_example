from validator import Validator
from config.messages import Messages


# this class is use for validattion
class SendRequestValidator(Validator):
    user_id = 'required|numberic'
    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")
        }
    }

class ApproverejectValidator(Validator):
    user_id = 'required|numberic'
    message = {
        'user_id': {
            'required': Messages.IS_REQUIRED.format(field_name="User id"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="User id")
        }
    }

# this class is use for chat list validation
class ChatListValidator(Validator):
    page_limit = 'required|numberic'
    message = {
        'page_limit': {
            'required': Messages.IS_REQUIRED.format(field_name="Page Limit"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        }
    }

class CreateGroupValidator(Validator):
    group_name = 'required'

    message = {
        'group_name': {
            'required': Messages.IS_REQUIRED.format(field_name="Group Name")
        }
    }


class EditGroupValidator(Validator):
    group_id = 'required|numberic'
    group_name = 'required'
    group_image = 'required'

    message = {
        'group_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Group ID"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Page Limit")
        },
        'group_name': {
            'required': Messages.IS_REQUIRED.format(field_name="Group Name")
        },
        'group_image': {
            'required': Messages.IS_REQUIRED.format(field_name="Group Image")
        }
    }

class AddRemoveGroupValidator(Validator):
    group_id = 'required|numberic'
    type = 'required|between:1, 2'

    message = {
        'group_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Group ID"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Group ID")
        },
        'type': {
            'required': Messages.IS_REQUIRED.format(field_name="Type"),
            'between': Messages.SHOULD_BE_BETWEEN.format(field_name="Type", min_value=1, max_value=2)
        }
    }

class GroupDetailsValidator(Validator):
    group_id = 'required|numberic'

    message = {
        'group_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Group ID")
        }
    }

class UpdateLastMessageValidator(Validator):
    message = 'required'

    message = {
        'message': {
            'required': Messages.IS_REQUIRED.format(field_name="Message")
        }
    }


class LeaveGroupValidator(Validator):
    group_id = 'required|numberic'

    message = {
        'group_id': {
            'required': Messages.IS_REQUIRED.format(field_name="Group ID"),
            'numberic': Messages.SHOULD_BE_NUMERIC.format(field_name="Group ID")
        }
    }