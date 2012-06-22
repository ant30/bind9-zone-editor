import re

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'serial':re.compile(r'(?P<serial>\d{10}) *; *serial'),
    'record':re.compile(r'^(?P<name>(?:[a-zA-Z0-9-.]*|@)) *(?:(?P<preference>\d+) *|)(?:IN *|)(?P<recordtype>A|CNAME) *(?P<target>[a-zA-Z0-9-.]*)'
                        r'(?: *;(?P<comment>.*)$|)'),
}

MATCH_RE_STR = {
    'record':r'^%(name)s *%(rtype)',
    'record_p':r'^{name} *(?:\d+ *|)(?:IN *|){rtype}',
    'serial':r'(?P<serial>\d{10}) *; *serial',
}


class Zone(object):
    def __init__(self, domain, filename):
        self.domain = domain
        self.filename = filename
        self.serial = None
        self.names = dict()
        zonefile = open(self.filename, 'r')
        for line in zonefile.readlines():
            serial_line = PARSER_RE['serial'].search(line)
            if serial_line:
                self.serial = serial_line
                continue
            record_line = PARSER_RE['record'].search(line)
            if record_line:
                self.__add_record(**record_line.groupdict())
        zonefile.close()
        assert self.serial, "ERROR: No serial is detected or defined"

    def __add_record(self, name, recordtype, target, preference=None, comment=None):
        self.names[(name, recordtype)] = {'preference': preference,
                                          'comment': comment,
                                          'target': target,
                                          }

    def __del_record(self, name, recordtype):
        del self.names[(name, recordtype)]

    def __exist_record(self, name, recordtype):
        return (name, recordtype) in self.names


    def __str_record(self, name, recordtype):
        record = self.names[(name, recordtype)]
        return "%s %s %s ;%s" % (name,
                                 recordtype,
                                 record['target'],
                                 record['comment'])


    def __str_serial(self, name, recordtype):
        return "                %s      ;serial aaaammdd" % self.serial

    def __save_record_to_file(self, name, recordtype):
        record = self.names[(name, recordtype)]
        match = re.compile(MATCH_RE_STR['record'] % {'name':name, 'rtype': recordtype})

        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()

        n = 0
        while n < len(lines):
            if match.match(lines[n]):
                lines[n] = self.__str_record(name, recordtype)
                break
            n += 1

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()


    def __save_serial_to_file(self, name, recordtype):
        record = self.names[(name, recordtype)]
        match = re.compile(MATCH_RE_STR['serial'])

        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()

        n = 0
        while n < len(lines):
            if match.match(lines[n]):
                lines[n] = self.__str_serial()
                break
            n += 1

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()


    def get_records(self, name=None, recordtype=None, name_exact=None):
        filters = []

        if name:
            def filter_name(n, rt):
                return n.find(name) >= 0
            filters.append(filter_name)

        if recordtype:
            def filter_type(n, rt):
                return rt == recordtype
            filters.append(filter_type)

        if name_exact:
            def filter_name_exact(n, rt):
                return n == name >= 0
            filters.append(filter_name)


        if filters:
            return filter(lambda (n, rt): all([f(n, rt) for f in filters]),
                         self.names)
        else:
            return self.names

    def get_record(self, name, rtype):
        record = self.names[(name, rtype)]
        return {'name': name,
                'recordtype': rtype,
                'target': record['target'],
                'comment': record['comment'],
                }


    def add_record(self, name, recordtype, target, description=None, preference=None):
        if name.endswith(self.domain):
            entry = name.replace(".%s" % self.domain, "")
        elif name.endswith('.'):
            entry = name[:-1]
        else:
            entry = name

        if not self.get_records(name=entry):
            self.__add_record(name=entry,
                              recordtype=recordtype,
                              target=target,
                              description=description,
                              preference=preference,
                              )
            self.__save_record_to_file(name, recordtype)


    def update_serial(self):
        today_str = today.strftime("%Y%m%d")
        if self.serial.startswith(today_str):
            change = self.serial[8:]
            inc_change = int(change) + 1
            serial = long("%s%02d" % (today_str, inc_change))
        else:
            serial = long("%s01" % today_str)
        self.serial = serial

    def get_serial(self):
        return self.serial


