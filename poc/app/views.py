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

        schema = Record()
        form = deform.Form(schema, buttons=('submit',))
        response = {"zonename": zonename,
                    "record": zone.get_record(recordname, recordtype),
                    "form": form.render()}

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except ValidationVailure, e:
                response['form'] = e.render()
            print data
        return response

