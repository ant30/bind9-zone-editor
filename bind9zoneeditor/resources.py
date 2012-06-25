from pyramid.security import Allow

from pyramid.security import Authenticated

class SiteFolder(dict):
    __acl__ = [
        (Allow, Authenticated, 'view'),
        (Allow, Authenticated, 'edit')
    ]

    def __init__(self, name, parent, title):
        self.__name__ = name
        self.__parent__ = parent
        self.title = title

root = SiteFolder('', None, 'Site')

from pyramid.security import DENY_ALL

def bootstrap(request):
    # Let's make:
    # /
    return root
