from django.urls import include, path

VERSION = 'v2'


def get_include(url, name, v=VERSION):
    """
    arg:
        url - route v2 version
        name: standart resource
        VERSION: current version api
    return:
    if v2 resource exists - returns route with resource v2
    else - returns route with resource v1
    """
    *root, t = name.split('.')
    pattern = []

    try:
        _name = '.'.join((*root, v, t))
        pattern.append(path(url, (include(_name))))
    except ModuleNotFoundError:
        pass
    finally:
        pattern.append(path(url, include(name)))
    return pattern
