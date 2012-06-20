from deform import Form
import deform
import colander

from pyramid.view import view_config

from layouts import Layouts

from nstool import NsZone

import settings


recordtype_choices = (
    ('CNAME', 'CNAME'),
    ('A', 'A'),
    ('MX', 'MX'),
)

class Record(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    recordtype = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())


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
        zone = NsZone(zonename, zonefile)
        return {"zonename": zonename,
                "records": zone.get_records(),
                }


    @view_config(renderer="templates/record.pt", route_name="record")
    def record_edit(self):

        zonename = self.request.matchdict['zonename']
        recordtype = self.request.matchdict['recordtype']
        recordname = self.request.matchdict['recordname']
        zonefile = settings.zones[zonename]
        zone = NsZone(zonename, zonefile)
        protected = recordname in settings.protected_zones

        schema = Record()
        record = zone.get_record(recordname, recordtype)

        response = {"zonename": zonename,
                    "record": zone.get_record(recordname, recordtype)}
        if not protected:
            form = deform.Form(schema, buttons=('submit',))
        else:
            form = deform.Form(schema)

        if record:
            response["form"] = form.render(record)
        else:
            response["form"] = form.render()

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except ValidationVailure, e:
                if record:
                    response['form'] = e.render(record)
                else:
                    response['form'] = e.render()
            if not protected:
                zone.add_record(data['name'],
                            data['recordtype'],
                            data['target'])
                zone.save()
            else:
                # Return 403 (No editable)
                pass
        return response

    @view_config(renderer="templates/applychanges.pt", route_name="apply")
    def applychanges(self):
        zonename = self.request.matchdict['zonename']
        zonefile = settings.zones[zonename]
        zone = NsZone(zonename, zonefile)
        msg = ''
        zone.apply()
        return {"zonename": zonename,
                "msg": msg,
                }
