import re

from deform import Form
import deform
import colander
from webhelpers.paginate import Page, PageURL_WebOb

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPForbidden, HTTPCreated
from pyramid.security import remember
from pyramid.security import forget

from layouts import Layouts

from zoneparser import Zone, zone_reload_signal, ZoneReloadError
from userdb import UserDB

from bind9zoneeditor import settings


recordtype_choices = (
    ('CNAME', 'CNAME'),
    ('A', 'A'),
)


RE_IP = r"^(?:\d{1,3}\.){3}(?:\d{1,3})$"
RE_NAME =  r"^[\w.]+[^.]$"


class Record(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    type = colander.SchemaNode(colander.String(),
                    widget=deform.widget.SelectWidget(values=recordtype_choices)
                )
    target = colander.SchemaNode(colander.String())
    weight = colander.SchemaNode(colander.Integer())
    comment = colander.SchemaNode(colander.String(),
                                  missing=unicode(""))


def record_validator(form, value):
    if value['type'] == 'A':
        if not re.match(RE_IP, value['target']):
            exc = colander.Invalid(form, 'Invalid targe value using A record type')
            exc['target'] = colander.Invalid(
                  form, "A IP value is required (255.255.255.255)")
            raise exc

    elif value['type'] == 'CNAME':
        if not re.match(RE_NAME, value['target']):
            exc = colander.Invalid(form, 'Invalid targe value using A record type')
            exc['target'] = colander.Invalid(
                  form, "A NAME value is required 'ej2' for 'ej2.example.com' ")
            raise exc


class ZoneViews(Layouts):

    def __init__(self, request):
        self.request = request

    @view_config(renderer="templates/zone_list.pt", route_name="zonelist",
                 permission="view")
    def zone_list(self):
        zones = settings.zones.keys()
        return {"zones": zones}

    @view_config(renderer="templates/zone.pt", route_name="zoneview",
                 permission="view")
    def zone_view(self):
        zonename = self.request.matchdict['zonename']
        page = int(self.request.params['page']) if 'page' in self.request.params else 0
        search = self.request.params['search'] if 'search' in self.request.params else None
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)

        if search:
            records = zone.get_records(name=search)
        else:
            records = zone.get_records()

        entries = []
        for record in records:
            protected = name_is_protected(zonename, record.name)
            entries.append({'record':record,
                            'protected': protected})

        page_url = PageURL_WebOb(self.request)
        entries = Page(entries, page, url=page_url)

        return {"zonename": zonename,
                "entries": entries,
                "serial": zone.serial,
                }

    @view_config(renderer="templates/record.pt", route_name="record_add",
                 permission="edit")
    def record_add(self):
        zonename = self.request.matchdict['zonename']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)

        schema = Record(validator=record_validator)
        form = deform.Form(schema, buttons=('submit',))

        response = {"zonename": zonename,
                    "recordname": "new"}
        response["form"] = form.render()

        if 'submit' in self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
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


    @view_config(route_name="record_delete",
                 permission="edit")
    def record_delete(self):
        zonename = self.request.matchdict['zonename']
        recordname = self.request.matchdict['recordname']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)
        if name_is_protected(zonename, recordname):
            raise HTTPForbidden("You can not modify this domain name")

        zone.del_record(recordname)
        response = HTTPFound()
        response.location = self.request.route_url('zoneview',
                                                    zonename=zonename)
        return response

    @view_config(renderer="templates/record.pt", route_name="record",
                 permission="edit")
    def record_edit(self):
        zonename = self.request.matchdict['zonename']
        recordname = self.request.matchdict['recordname']
        zonefile = settings.zones[zonename]
        zone = Zone(zonename, zonefile)
        protected = name_is_protected(zonename, recordname)
        response = {"zonename": zonename,
                    "recordname": recordname}

        if self.request.POST and protected:
            return HTTPForbidden("You can not modify this domain name")

        elif protected:
            response['protected'] = protected
            response['record'] = zone.get_record(recordname)
            return response

        schema = Record(validator=record_validator)
        form = deform.Form(schema, buttons=('submit',))

        if self.request.POST:
            controls = self.request.POST.items()
            try:
                data = form.validate(controls)
            except deform.ValidationFailure, e:
                response['form'] = e.render()
                return response
            else:
                zone.add_record(**data)
                response = HTTPFound()
                response.location = self.request.route_url('record',
                                                            zonename=zonename,
                                                            recordname=data['name'])
                return response

        record = zone.get_record(recordname)
        response['form'] = form.render(record.todict())
        return response

    @view_config(renderer="templates/applychanges.pt", route_name="apply",
                 permission="edit")
    def applychanges(self):
        zonename = self.request.matchdict['zonename']
        try:
            zone_reload_signal(zonename, get_rndc_command())
        except ZoneReloadError, e:
            return {"zonename": zonename,
                    "msg": e.message,
                    }

        return {"zonename": zonename }


    @view_config(renderer="templates/login.pt", context=HTTPForbidden)
    @view_config(renderer="templates/login.pt", route_name="login")
    def login(self):
        request = self.request
        login_url = request.resource_url(request.context, 'login')
        referrer = request.url
        if referrer == login_url:
            referrer = '/' # never use the login form itself as came_from
        came_from = request.params.get('came_from', referrer)
        message = ''
        login = ''
        password = ''
        if 'form.submitted' in request.params:
            login = request.params['login']
            password = request.params['password']
            userdb = UserDB(settings.htpasswd_file)
            if userdb.check_password(login, password):
                headers = remember(request, login)
                return HTTPFound(location=came_from,
                                 headers=headers)
            message = 'Failed login'

        return dict(
            page_title="Login",
            message=message,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
            )

    @view_config(route_name="logout")
    def logout(self):
        headers = forget(self.request)
        url = self.request.route_url('login')
        return HTTPFound(location=url, headers=headers)


def name_is_protected(zonename, name):
    return (hasattr(settings, 'protected_names') and
            zonename in settings.protected_names and
            name in settings.protected_names[zonename])

def get_rndc_command():
    return getattr(settings, 'rndc_command', 'rndc')
