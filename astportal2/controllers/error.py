# -*- coding: utf-8 -*-
"""Error controller"""

from tg import request, expose

import inspect

__all__ = ['ErrorController']


class ErrorController(object):
    """
    Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    
    """

    @expose('astportal2.templates.error')
    def document(self, *args, **kwargs):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        try:
           code = resp.status_int
        except AttributeError:
           code = 500
        default_message = ("<p>We're sorry but we weren't able to process "
                           " this request.</p>")
        return dict(title='Erreur :(',
                    prefix=request.environ.get('SCRIPT_NAME', ''),
                    code=request.params.get('code', code),
                    message=request.params.get('message', default_message))
