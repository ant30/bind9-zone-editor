import re
import subprocess

# SERIAL = yyyymmddnn ; serial
PARSER_RE = {
    'serial':re.compile(r'(?P<serial>\d{10}) *; *serial'),
    'record':re.compile(r'^(?P<name>(?:[a-zA-Z0-9-.]*|@)) *(?:(?P<weight>\d+)'
                        r' *|)(?:IN *|)(?P<type>A|CNAME)'
                        r' *(?P<target>[a-zA-Z0-9-.]*)'
                        r'(?:(?: *|);(?P<comment>.*)$|)'),
}

MATCH_RE_STR = {
    'record':r'^{name} *(?:\d+ *|)(?:IN *|){rtype}',
    'serial':r'(?P<serial>\d{10}) *; *serial',
}

RNDC = "/usr/sbin/rndc"


class ZoneReloadError(Exception):
    pass

class Record(object):
    def __init__(self, name, type, target, weight=0, comment=''):
        self.name = name
        self.type = type
        self.target = target
        self.weight = weight or 0
        self.comment = comment or ''

    def __str__(self):
        return self.name

    def todict(self):
        return dict(name = self.name,
                    type = self.type,
                    target = self.target,
                    weight = self.weight,
                    comment = self.comment)


class ZoneFile(object):
    def __init__(self, filename):
        self.filename = filename

    def readfile(self):
        serial = None
        names = {}
        zonefile = open(self.filename, 'r')
        for line in zonefile.readlines():
            serial_line = PARSER_RE['serial'].search(line)
            if serial_line:
                serial = serial_line
                continue
            record_line = PARSER_RE['record'].search(line)
            if record_line:
                record = Record(**record_line.groupdict())
                names[str(record)] = record
        zonefile.close()
        return (serial, names)

    def __str_record(self, record):
        recordstr = record.name
        if record.weight:
            recordstr += " {0}".format(str(record.weight))

        recordstr += " {type} {target}".format(type=record.type,
                                              target=record.target)
        if record.comment:
            recordstr += ";{0}".format(record.comment)

        recordstr += '\n'
        return recordstr

    def __str_serial(self, serial):
        return "%s ;serial aaaammdd\n" % serial

    def save_record(self, record):
        match = re.compile(MATCH_RE_STR['record'].format(name=record.name,
                                                         rtype=record.type))
        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()
        n = 0
        while n < len(lines) and not match.match(lines[n]):
            n += 1

        if n == len(lines):
            lines.append(self.__str_record(record))
        else:
            lines[n] = self.__str_record(record)

        zonefile = open(self.filename, 'w')
        print lines
        zonefile.writelines(lines)
        zonefile.close()


    def remove_record(self, record):
        match = re.compile(MATCH_RE_STR['record'].format(name=record.name,
                                                         rtype=record.type))
        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()
        n = 0
        while n < len(lines) and not match.match(lines[n]):
            n += 1

        if n == len(lines):
            raise KeyError("Not Found, %s can't be deleted" % record.name)
        else:
            del lines[n]

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()

    def save_serial(self, serial):
        match = re.compile(MATCH_RE_STR['serial'])

        zonefile = open(self.filename, 'r')
        lines = zonefile.readlines()
        zonefile.close()

        n = 0
        while n < len(lines) and not match.match(lines[n]):
            if match.match(lines[n]):

                break
            n += 1

        if n == len(lines):
            raise KeyError("Serial not found in file %s" % self.filename)
        else:
            lines[n] = self.__str_serial()

        zonefile = open(self.filename, 'w')
        zonefile.writelines(lines)
        zonefile.close()



class Zone(object):
    def __init__(self, domain, filename):
        self.domain = domain
        self.zonefile = ZoneFile(filename)
        (self.serial, self.names) = self.zonefile.readfile()
        assert self.serial, "ERROR: Serial is undefined on %s" % self.filename

    def del_record(self, name):
        self.zonefile.remove_record(self.names[name])
        del self.names[name]

    def get_record(self, name):
        return self.names[name]

    def get_records(self, name=None, type=None, target=None,
                    name_exact=None):
        filters = []

        if name:
            def filter_name(r):
                return r.name.find(name) >= 0
            filters.append(filter_name)

        if type:
            def filter_type(r):
                return r.type == type
            filters.append(filter_type)

        if target:
            def filter_target(r):
                return r.target == target
            filters.append(filter_target)

        if name_exact:
            def filter_name_exact(r):
                return r.name == name >= 0
            filters.append(filter_name)

        if filters:
            return filter(lambda record: all([f(record) for f in filters]),
                         self.names.values())
        else:
            return self.names.values()

    def add_record(self, name, type, target, comment='', weight=0):
        if name.endswith(self.domain):
            entry = name.replace(".%s" % self.domain, "")
        elif name.endswith('.'):
            entry = name[:-1]
        else:
            entry = name

        record = Record(name=entry,
                        type=type,
                        target=target,
                        comment=comment,
                        weight=weight)

        self.zonefile.save_record(record)
        self.names[str(record)] = record

    def update_serial(self):
        today_str = today.strftime("%Y%m%d")
        if self.serial.startswith(today_str):
            change = self.serial[8:]
            inc_change = int(change) + 1
            serial = long("%s%02d" % (today_str, inc_change))
        else:
            serial = long("%s01" % today_str)
        self.zonefile.save_serial(self.serial)
        self.serial = serial


def zone_reload_signal(name, cmd):
    try:
        subprocess.check_output("%s reload %s" % (cmd, name),
                                stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, e:
        raise ZoneReloadError(e.output)
