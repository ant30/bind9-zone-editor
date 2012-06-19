from easyzone import easyzone
from easyzone.zone_reload import ZoneReload


DEFAULT_TTL = 3600
RNDC_CMD = '/usr/sbin/rndc'


class NsZone:
    def __init__(self, name, file):
        self.name = name
        self.file = file
        self.zone = easyzone.zone_from_file(name, file)
        self.records = []
        for (name, item) in self.zone.names.items():
            for record_type in ('A', 'MX', 'CNAME'):
                record = item.records(record_type)
                if record and record.items and isinstance(record.items[0], str):
                    values = ' '.join(record.items)
                    self.records.append({'name': name,
                                         'recordtype': record_type,
                                         'target': values
                                        })

    def get_records(self, name=None, record_type=None, name_exact=None):
        filters = []

        if name:
            def filter_name(item):
                return item['name'].find(name) >= 0
            filters.append(filter_name)

        if record_type:
            def filter_type(item):
                return item['recordtype'] == record_type
            filters.append(filter_type)

        if name_exact:
            def filter_name_exact(item):
                return item['name'] == name >= 0
            filters.append(filter_name)


        records = self.records
        if filters:
            return filter(lambda item: all([f(item) for f in filters]),
                         records)
        else:
            return records

    def get_record(self, name, rtype):
        return filter(lambda item: item['name'] == name and
                        item['recordtype'] == rtype, self.records)[0]

    def add_record(self, name, record_type, target, ttl=DEFAULT_TTL):
        if name.endswith(self.zone.domain):
            entry = name
        elif name.endswith('.'):
            entry = ''.join((name, self.zone.domain))
        else:
            entry = '.'.join((name, self.zone.domain))

        if entry not in self.zone.names:
            self.zone.add_name(entry)
        newname = self.zone.names[entry]
        newname.ttl = ttl
        record =  newname.records(record_type, create=True)
        if record is None:
            newname.records(record_type).add(str(target))
        else:
            for item in record.items:
                record.delete(item)
            record.add(str(target))


    def save(self):
        self.zone.save()

    def apply(self):
        r = ZoneReload(rndc=RNDC_CMD)
        r.reload(self.zone.domain)
