
zones = {
        'example.com': 'db.example.com',
        }

protected_zones = (
        'mail.example.com',
        'www.example.com',
        )

try:
    from local_settings import *
except:
    pass
