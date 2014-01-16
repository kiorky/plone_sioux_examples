# -*- coding: utf-8 -*-
import logging

from Acquisition import aq_parent

from OFS.interfaces import IItem
from OFS.SimpleItem import SimpleItem

from plone.app.z3cform.inline_validation import InlineValidationView
from plone.dexterity.interfaces import IDexterityFTI

from z3c.form.interfaces import NOVALUE, IObjectFactory
from z3c.form.util import getSpecification

from zope.lifecycleevent import ObjectCreatedEvent
from zope.component.hooks import getSite
from zope.component import (
    provideAdapter, adapts, createObject, getUtility)
from zope.event import notify
from zope.globalrequest import getRequest
from zope import schema
from zope.interface import alsoProvides, Interface, implements

from foo import MessageFactory as _

_default = object()

logger = logging.getLogger('foo')

def is_zope_object(obj):
    """Return only true for acquisition wrapped obj."""
    try:
        return (
            IItem.providedBy(obj)
            and not aq_parent(obj) is None
        )
    except Exception:
        return False


def get_source_context(context):
    # if we are in addform and adding subforms objs, just
    # get the context of the subform(published object view) itself
    # match z3cform NOVALUE + dict
    if not is_zope_object(context):
        try:
            context = getSite().REQUEST['PUBLISHED'].context
        except Exception:
            context = getRequest()['PUBLISHED'].context
    if context is NOVALUE:
        raise Exception('Cant get a valid context!')
    return context

