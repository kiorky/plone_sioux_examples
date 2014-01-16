#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
from zope.interface import implements

from zope.schema.interfaces import ISource, IContextSourceBinder, IVocabularyFactory
from Acquisition import aq_parent
from OFS.interfaces import IItem

from zope.schema.vocabulary import SimpleVocabulary
from zope.component.hooks import getSite
from utils import (
    get_source_context,
    is_zope_object)

from wellknown import IWellKnown


def get_parent(context):
    context = get_source_context(context)
    parent = aq_parent(context)
    return parent


def get_wellknownparent(context):
    parent = get_parent(context)
    plone = getSite()
    while (
        parent is not plone
        and not IWellKnown.implementedBy(parent)
        and is_zope_object(parent)
    ):
        parent = get_parent(parent)
    return parent


def make_terms(terms, rawLinesStr):
    rawLines = rawLinesStr.split('\n')
    lines = [l for l in rawLines if l.strip('\r').strip(' ')]
    for line in lines:
        key = line.split('|')[0]
        label = line.split('|')[1]
        terms.append(SimpleVocabulary.createTerm(key, str(key), label))
    return terms


def make_voc(terms, linesstr):
    return SimpleVocabulary(make_terms(terms, linesstr))


class _MyVoc(object):
    """Voc. without grok"""
    implements(IVocabularyFactory)

    def __call__(self, context):
        # laboratories : attribute acquired from parent doctoral college
        terms = []
        parent = get_wellknownparent(context)
        linesstr = ''
        if IWellKnown.implementedBy(parent):
            linesstr = parent.superfield
        return make_voc(terms, linesstr)

MyVoc = _MyVoc()

# vim:set et sts=4 ts=4 tw=80:
