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

class NoInlineValidation(InlineValidationView):

    def __call__(self, fname=None, fset=None):
        if fname:
            return super(NoInlineValidation, self).__call__(fname, fset=fset)
        else:
            return
            return "{'errmsg': ''}"


def importStep(context):
    logger.info('processing import step !')


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


def dummyfactory(
    ifcs,
    portal_type,
    context=_default,
    request=_default,
    form=_default,
    widget=_default,
):
    """
    Object Factory used in subform to gather data from
    POST requests

    When you have a schema field to construct objects, this help
    you to make an object factory that can construct objects
    from the posted data

    ifcs: list of interfaces specified as schema.Object(schema=ifc)
    portal_type: portal_type to use as a factory for this object

    context, request, form and widget are the z3c.form's discriminators
    """
    if not isinstance(ifcs, (tuple, set, list)):
        ifcs = [ifcs]
    ifcs = list(ifcs)
    if context is _default:
        context = Interface
    if request is _default:
        request = Interface
    if form is _default:
        form = Interface
    if widget is _default:
        widget = Interface

    class AbstractBaseFactory(object):
        """Abstract schema.Object factory."""
        implements(IObjectFactory)
        adapts(
            getSpecification(context),
            getSpecification(request),
            getSpecification(form),
            getSpecification(widget),
        )

        def __init__(self, c, r, f, w):
            pass

        def __call__(self, value):
            fti = getUtility(IDexterityFTI, name=portal_type)
            nobj = createObject(fti.factory)
            nobj.portal_type = fti.getId()
            fields = []
            for ifc in ifcs:
                if not ifc.providedBy(nobj):
                    alsoProvides(nobj, ifc)
                for name, fk in schema.getFieldsInOrder(ifc):
                    if name in fields:
                        continue
                    setattr(nobj, name, value.get(name, None))
                    fields.append(name)
            notify(ObjectCreatedEvent(nobj))
            return nobj
    for ifc in ifcs:
        ifname = '{0}.{1}'.format(*(ifc.__module__, ifc.__name__))
        provideAdapter(AbstractBaseFactory, name=ifname)
