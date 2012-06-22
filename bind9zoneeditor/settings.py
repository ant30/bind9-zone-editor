
zones = {
        'example.com': 'db.example.com',
        }

protected_names = {
        'example.com':('mail',
                       'www',
                       '@',
                       ),
        }

rndc_command = 'rndc'

try:
    from local_settings import *
except:
    pass
