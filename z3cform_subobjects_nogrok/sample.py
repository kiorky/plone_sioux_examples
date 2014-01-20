# -*- coding: utf-8 -*-

import datetime
import logging

from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import (
    newSecurityManager, setSecurityManager)
from AccessControl.User import nobody, UnrestrictedUser as BaseUnrestrictedUser

from Acquisition import aq_parent

from collective import dexteritytextindexer
from DateTime import DateTime
from five import grok

from OFS.interfaces import IItem

from plone.app.z3cform import layout

from plone.autoform.interfaces import IFormFieldProvider

from plone.dexterity.browser import add, edit
from plone.dexterity.content import Container
from plone.directives import (
    dexterity, form)

from plone.i18n.normalizer.interfaces import IIDNormalizer

from plone import api
from plone.indexer import indexer
from plone.supermodel import model

from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.exceptions import EmailAddressInvalid
from Products.CMFDefault.utils import checkEmailAddress

from Products.Five.browser import BrowserView

import z3c.form
from z3c.form import button, field
from z3c.form.interfaces import NOVALUE, IObjectFactory, HIDDEN_MODE

from zope.browserpage.viewpagetemplatefile import (
    ViewPageTemplateFile as Zope3PageTemplateFile)
from zope.component import getUtility, provideAdapter
from zope.component.hooks import getSite
from zope.event import notify
from zope import schema
from zope.interface import alsoProvides, Interface, implements

from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from zope.schema import ValidationError
from zope.schema.vocabulary import SimpleVocabulary

from sample.utils import dummyfactory
from sample import MessageFactory as _


logger = logging.getLogger('sample')

mainobjMainLaboratory = _(u'mainobj main research unit')
reviewerwaitforcorrections = _(u'Reviewer wait for corrections')


class UnrestrictedUser(BaseUnrestrictedUser):
    """Unrestricted user that still has an id.
    """
    def getId(self):
        """Return the ID of the user.
        """
        return "Anonymousmainobj"


class Iinner_contenttype(form.Schema):
    """
    Description of the inner content type"
    """
    dexteritytextindexer.searchable('title')
    title = schema.TextLine(
        title=_(u"French title"),
        description=_(u"French title of the mainobj subject."),
        required=True,
        default=u'titre de la these',
    )


class inner_contenttype(Container):
    implements(Iinner_contenttype)


class Imainobj(form.Schema):
    """
    Description of the Example Type
    """
    dexteritytextindexer.searchable('title')
    title = schema.TextLine(
        title=_(u"French title"),
        description=_(u"French title of the mainobj subject."),
        required=True,
        default=u'titre de la these',
    )
    inner_contenttypes = schema.List(
        title=u"Inner_contenttypes for the mainobj",
        description=u"Inner_contenttypes",
        required=False,
        value_type=schema.Object(Iinner_contenttype))

alsoProvides(Imainobj, IFormFieldProvider)


@form.default_value(field=Imainobj['title'])
def openDefaultValue(data):
    return "foo"


@indexer(Imainobj)
def mainobj_opening_date(obj):
    return DateTime(obj.opening_date.isoformat())


provideAdapter(mainobj_opening_date, name="THESISopening_date")


class mainobj(Container):
    implements(Imainobj)


class FormMixin(object):
    def update(self):
        dummyfactory((Iinner_contenttype,), 'sample.inner_contenttype')

    def filter_inner_contenttype(self, data):
        inner_contenttypes = {}
        for k in ['inner_contenttypes']:
            inner_contenttypes[k] = data.get(k, [])
            if k in data:
                del data[k]
        return inner_contenttypes

    def applyInner_contenttype(self, container, inner_contenttype):
        normalizer = getUtility(IIDNormalizer)
        added = []
        for k, data in inner_contenttype.items():
            for obj in data:
                id = obj.inner_contenttype_body
                if isinstance(id, list):
                    id = id[0]
                id = normalizer.normalize("inner_contenttype_{0}".format(id))
                if id in container.objectIds():
                    container.manage_delObjects([id])
                obj.id = id
                newName = container._setObject(id, obj)
                added.append(container[newName])
        return added


class EditForm(dexterity.EditForm, FormMixin):
    schema = Imainobj
    title = _(u'Edit a mainobj')
    hidden_groups = ('inner_contenttype',)

    def update(self):
        FormMixin.update(self)
        super(dexterity.EditForm, self).update()
        toadd = []
        todelete = []
        for group in self.groups:
            if group.__name__ == 'inner_contenttype':
                group.mode = HIDDEN_MODE
                for w in group.widgets:
                    group.widgets[w].mode = HIDDEN_MODE
                toadd.append(group)
            else:
                toadd.append(group)
        for i in todelete:
            del i
        self.groups = tuple(toadd)


class edit_form(edit.DefaultEditView):
    form = EditForm
    index = Zope3PageTemplateFile("templates/form.pt")


class AddForm(add.DefaultAddForm, FormMixin):
    schema = Imainobj
    ignoreContext = True
    title = _(u'Add a mainobj')

    def update(self):
        FormMixin.update(self)
        super(add.DefaultAddForm, self).update()

    @button.buttonAndHandler(_(u'Save'))
    def handleApply(self, action):
        sm = getSecurityManager()
        portal = api.portal.get()
        data, errors = self.extractData()
        if errors:
            self.status = _("Please correct errors")
            return
        try:
            inner_contenttype = self.filter_inner_contenttype(data)
            try:
                # go Admin, even in anymomous mode !
                tmp_user = UnrestrictedUser(
                    sm.getUser().getId(), '', ['Manager'], '')
                tmp_user = tmp_user.__of__(portal.acl_users)
                newSecurityManager(None, tmp_user)
                # Call the function
                # for edit form, use : self.applyChanges(data)
                obj = self.createAndAdd(data)
                # context is the mainobj repo
                obj = obj.__of__(self.context)
                self.applyInner_contenttype(obj, inner_contenttype)
                contextURL = self.context.absolute_url()
                self.request.response.redirect(contextURL)
            except Exception:
                # If special exception handlers are needed, run them here
                raise
        finally:
            # Restore the old security manager
            setSecurityManager(sm)

    @button.buttonAndHandler(_(u'Cancel'))
    def handleCancel(self, action):
        data, errors = self.extractData()
        # context is the mainobj repo
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)


class add_form(add.DefaultAddView):
    form = AddForm
    index = Zope3PageTemplateFile("templates/form.pt")


class View(grok.View):
    grok.context(Imainobj)
    grok.require('zope2.View')

    def searchInner(self, types=None, depth=1):
        if not isinstance(types, list):
            types = [types]
        catalog = api.portal.get_tool(name='portal_catalog')
        qr = {'path': {'query': '/'.join(self.context.getPhysicalPath()),
                       'depth': depth},
              'portal_type': types}
        return [a.getObject() for a in catalog.search(qr)]

    def getInner_contenttype(self):
        return self.searchInner('sample.customobj')
