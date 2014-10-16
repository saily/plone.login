# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from plone.login import MessageFactory as _
from plone.login.interfaces import IRegisterForm
from plone.z3cform import layout
from z3c.form import button
from z3c.form import field
from z3c.form import form
from zope.component import getMultiAdapter


class RegisterForm(form.EditForm):
    ''' Implementation of the registration form '''

    fields = field.Fields(IRegisterForm)

    id = 'RegisterForm'
    label = _(u'Sign up')
    description = _(u'Join the club.')

    ignoreContext = True

    render = ViewPageTemplateFile('templates/register.pt')

    prefix = ''

    def updateWidgets(self):

        super(RegisterForm, self).updateWidgets(prefix='')
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        if use_email_as_login:
            self.widgets['email'].tabindex = 1
        else:
            self.widgets['email'].tabindex = 2
            self.widgets['username'].tabindex = 1
            klass = getattr(self.widgets['username'], 'klass', '')
            if klass:
                self.widgets['username'].klass = ' '.join([
                    klass, _(u'stretch')
                ])
            else:
                self.widgets['username'].klass = _(u'stretch')
            self.widgets['username'].placeholder = _(u'Username')
            self.widgets['username'].autocapitalize = _(u'off')
        klass = getattr(self.widgets['email'], 'klass', '')
        if klass:
            self.widgets['email'].klass = ' '.join([klass, _(u'stretch')])
        else:
            self.widgets['email'].klass = _(u'stretch')
        self.widgets['email'].placeholder = _(u'Email address')
        self.widgets['email'].autocapitalize = _(u'off')
        self.widgets['password'].tabindex = 3
        klass = getattr(self.widgets['password'], 'klass', '')
        if klass:
            self.widgets['password'].klass = ' '.join([klass, _(u'stretch')])
        else:
            self.widgets['password'].klass = _(u'stretch')
        self.widgets['password'].placeholder = _(u'Super secure password')
        self.widgets['password_confirm'].tabindex = 4
        klass = getattr(self.widgets['password_confirm'], 'klass', '')
        if klass:
            self.widgets['password_confirm'].klass = ' '.join([
                klass, _(u'stretch')
            ])
        else:
            self.widgets['password_confirm'].klass = _(u'stretch')
        self.widgets['password_confirm'].placeholder = _(u'Confirm password')

    def updateFields(self):
        super(RegisterForm, self).updateFields()
        fields = field.Fields(IRegisterForm)
        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        if use_email_as_login:
            fields.remove('username')

    @button.buttonAndHandler(_('Register'), name='register')
    def handleRegister(self, action):

        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u'authenticator')
        if not authenticator.verify():
            raise Unauthorized
        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        password = str(data.get('password'))
        username = str(data.get('username'))
        email = data.get('email')

        portal_props = getToolByName(self.context, 'portal_properties')
        props = portal_props.site_properties
        use_email_as_login = props.getProperty('use_email_as_login')
        if use_email_as_login:
            username = email = str(data.get('email'))

        registration = getToolByName(self.context, 'portal_registration')
        try:
            registration.addMember(username, password)
        except (AttributeError, ValueError), err:
            IStatusMessage(self.request).addStatusMessage(err, type='error')
            return

        authenticated = self.context.acl_users.authenticate(username,
                                                            password,
                                                            self.request)
        if authenticated:
            self.context.acl_users.updateCredentials(self.request,
                                                     self.request.response,
                                                     username,
                                                     password)

        membership_tool = getToolByName(self.context, 'portal_membership')
        member = membership_tool.getMemberById(username)

        # XXX: Improve this for further fields
        member.setMemberProperties({'email': email})

        login_time = member.getProperty('login_time', '2000/01/01')
        if not isinstance(login_time, DateTime):
            login_time = DateTime(login_time)
        initial_login = login_time == DateTime('2000/01/01')
        if initial_login:
            # TODO: Redirect if this is initial login
            pass

        IStatusMessage(self.request).addStatusMessage(
            _(u'You are now logged in.'), 'info')

        # TODO: Add way to configure the redirect
        self.request.response.redirect(self.context.absolute_url())


class RegisterFormView(layout.FormWrapper):
    form = RegisterForm
