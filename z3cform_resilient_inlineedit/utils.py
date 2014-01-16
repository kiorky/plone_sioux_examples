# -*- coding: utf-8 -*-
import logging
from plone.app.z3cform.inline_validation import InlineValidationView

logger = logging.getLogger('foo')

class NoInlineValidation(InlineValidationView):

    def __call__(self, fname=None, fset=None):
        if fname:
            return super(NoInlineValidation, self).__call__(fname, fset=fset)
        else:
            return
            return "{'errmsg': ''}"
