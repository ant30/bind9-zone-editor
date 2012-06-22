from deform import Form
import deform
import colander

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPCreated

from layouts import Layouts

from zoneparser import Zone, zone_reload_signal, ZoneReloadError

import settings


recordtype_choices = (
    ('CNAME', 'CNAME'),
    ('A', 'A'),
)

class Record(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    recordtype = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())
    weight = colander.SchemaNode(colander.Integer())
    comment = colander.SchemaNode(colander.String())


class ZoneViews(Layouts):

    def __init__(self, request):
        self.request = request

    @view_config(renderer="templates/zone_list.pt", route_name="zonelist")
    def zone_list(self):
        zones = settings.zones.keys()
        return {"zones": zones}

    @view_config(renderer="templates/zone.pt", route_name="zoneview")
    def zone_view(self):
        zonename = self.request.matchdict['zonename']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)
        records = zone.get_records()
        entries = []
        for record in records:
            protected = name_is_protected(zonename, record.name)
            entries.append({'record':record,
                            'protected': protected})

        return {"zonename": zonename,
                "entries": entries,
                "serial": zone.serial,
                }

    @view_config(renderer="templates/record.pt", route_name="record_add")
    def record_add(self):
        zonename = self.request.matchdict['zonename']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)

        schema = Record()
        form = deform.Form(schema, buttons=('submit',))

        response = {"zonename": zonename}
        response["form"] = form.render()

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except ValidationVailure, e:
                response['form'] = e.render()
                return response
            if not name_is_protected(zonename, data['name']):
                zone.add_record(**data)
                response = HTTPFound()
                response.location = self.request.route_url('record',
                                                            zonename=zonename,
                                                            recordname=data['name'])
                return response
            else:
                return HTTPForbidden()

        return response


    @view_config(renderer="templates/record.pt", route_name="record")
    def record_edit(self):

        zonename = self.request.matchdict['zonename']
        recordname = self.request.matchdict['recordname']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)
        protected = name_is_protected(zonename, recordname)
        response = {"zonename": zonename}

        if self.request.POST and protected:
            return HTTPForbidden("You can not modify this domain name")

        elif protected:
            response['protected'] = protected
            response['record'] = zone.get_record(recordname)
            return response

        schema = Record()
        form = deform.Form(schema, buttons=('submit',))

        if self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except ValidationVailure, e:
                response['form'] = e.render()
                return response
            else:
                zone.add_record(**data)
                response = HTTPFound()
                response.location = self.request.route_url('record',
                                                            zonename=zonename,
                                                            recordname=data['name'])

        record = zone.get_record(recordname)
        response['form'] = form.render(record.todict())
        return response


    @view_config(renderer="templates/applychanges.pt", route_name="apply")
    def applychanges(self):
        zonename = self.request.matchdict['zonename']
        try:
            zone_reload_signal(zonename, get_rndc_command())
        except ZoneReloadError, e:
            return {"zonename": zonename,
                    "msg": e.message,
                    }

        return {"zonename": zonename }

def name_is_protected(zonename, name):

    return (hasattr(settings, 'protected_names') and
            zonename in settings.protected_names and
            name in settings.protected_names[zonename])

def get_rndc_command():
    return getattr(settings, 'rndc_command', 'rndc')
