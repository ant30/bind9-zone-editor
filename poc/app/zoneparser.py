import re



# SERIAL = yyyymmddnn ; serial
EXPRESIONS = {
    'serial':re.compile(r'(?P<serial>\d{10}) *; *serial'),
    'record':re.compile(r'^(?P<name>(?:[a-zA-Z0-9-.]*|@)) *(?:(?P<preference>\d+) *IN *)(?P<recordtype>A|CNAME) *(?P<target>[a-zA-Z0-9-.]*)'
                        r'(?: *;(?P<comment>.*)$|)')
}

zonefile = open('db.sevi.mobi')
for line in zonefile.readlines():
    serial_line = EXPRESIONS['serial'].search(line)
    if serial_line:
        print "SERIAL:", serial_line.group('serial')
        continue
    record_line = EXPRESIONS['record'].search(line)
    if record_line:
        print "RECORD:", record_line.groups()


