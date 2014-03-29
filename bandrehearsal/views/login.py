from pyramid.view import view_config

from ..models import User, DBSession
from ..helpers import generic_edit_view
from pyramid.security import remember
from pyramid.i18n import TranslationString as _
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.orm.exc import NoResultFound

import colander
import deform


class LoginSchema(colander.Schema):
    user = colander.SchemaNode(
        colander.String(),
        description=_("Type your user"))
    password = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.PasswordWidget(size=20),
        description=_("Type your password"))


class LoginView(object):

    def __init__(self, request):
        self.request = request
        self.fail = False
        self.next_page = request.params.get('next') or \
            request.route_url('home')
        self.buttons = ('submit', )

    @view_config(route_name='login',
            renderer='bandrehearsal:templates/login.mako')
    def login(self):
        if self.request.POST:
            user = self.request.POST.get('user', '')
            passwd = self.request.POST.get('password', '')
            try:
                logged_user = User.log(user, passwd)
            except User.WrongCredential:
                self.fail = True
            else:
                headers = remember(self.request, logged_user.login)
                return HTTPFound(location=self.next_page, headers=headers)
        form = self.login_form()
        return {'form': form.render(),
             'requirements': form.get_widget_resources(),
             'next': self.next_page,
             'fail': self.fail}

    def login_form(self):
        return deform.Form(LoginSchema(), buttons=self.buttons)


@view_config(name='list', context=User,
    renderer='bandrehearsal:templates/users.mako', permission='edit')
def list_users(request):
    users = User.actives()
    return {'list': users}


@view_config(name='delete', context=User,
    renderer='bandrehearsal:templates/users.mako', permission='edit')
def delete_user(request):
    request.context.active = False
    return {'status': 'success'}


class UserEditSchema(colander.Schema):

    name = colander.SchemaNode(
            colander.String(),
            description=_("Type your name"))
    password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5),
            widget=deform.widget.CheckedPasswordWidget(size=20),
            description=_('Type your password and confirm it'))
    login = colander.SchemaNode(
            colander.String(),
            description=_("Type your login"))
    email = colander.SchemaNode(
            colander.String(),
            validator=colander.Email(),
            description=_('Type your e-mail'))
    phone = colander.SchemaNode(
            colander.String(),
            description=_('Type your phone number'),
            missing=colander.drop)
    

@view_config(name='edit', context=User,
    renderer='bandrehearsal:templates/users.mako', permission='edit')
def edit_user(request):
    def unique_login(form, value):
        try:
            DBSession.query(User).filter_by(login=value['login']).one()
        except NoResultFound:
            exc = colander.Invalid(form, _('User login already in use'))
            raise exc
    form = deform.Form(UserEditSchema(validator=unique_login), buttons=(_('send'),))
    return generic_edit_view(request, form)


@view_config(name='view', context=User,
    renderer='bandrehearsal:templates/users.mako', permission='view')
def view_user(request):
    return {'user': request.context}
