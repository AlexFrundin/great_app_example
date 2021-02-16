from config.messages import Messages


def requestErrorMessagesFormate(params):
    try:
        for dat in params:
            for target_list in params[dat]:
                return params[dat][target_list]
    except Exception as e:
        return Messages.INVALID_REQUEST
