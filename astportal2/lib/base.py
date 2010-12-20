# -*- coding: utf-8 -*-

"""The base Controller API."""

from tg import TGController, tmpl_context
from tg.render import render
from tg import request
from pylons.i18n import _, ungettext, N_
from tw.api import WidgetBunch
import astportal2.model as model

from tw.jquery import jquery_js

__all__ = ['Controller', 'BaseController']


class BaseController(TGController):
    """
    Base class for the controllers in the application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.

    """

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # TGController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        request.identity = request.environ.get('repoze.who.identity')
        tmpl_context.identity = request.identity
        jquery_js.inject()
#        from tw.jquery.ui import ui_tabs_js, jquery_ui_all_js
#        from tw.uitheme import uilightness_css
#        jquery_ui_all_js.inject()
#        uilightness_css.inject()
        return TGController.__call__(self, environ, start_response)
