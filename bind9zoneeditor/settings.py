
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

htpasswd_file = 'htpasswd'

try:
    from local_settings import *
except:
    pass
