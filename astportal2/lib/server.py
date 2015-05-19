from gevent import reinit
from gevent.monkey import patch_all
reinit()
patch_all(dns=False)

# WebSocket acceleration
import wsaccel
wsaccel.patch_ws4py()

from ws4py.server.geventserver import WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py import configure_logger
configure_logger()

# For paste.deploy server_runner instantiation (egg:astportal2#ws4py)
def serve(wsgi_app, global_config, **kw):

    ws_handler = kw.get('websocket_resource')
    host = kw.get('host', '0.0.0.0')
    port = int(kw.get('port', 8080))

    print('Starting WebSocket (ws4py) enabled Gevent HTTP server on http://%s:%s' % (
         host, port))
    s = WSGIServer((host, port), WrapWebSocket(host, port, wsgi_app, ws_handler))
    s.serve_forever()


def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module ) # May fail if not found!

    for comp in parts[1:]:
        m = getattr(m, comp)

    return m


class WrapWebSocket(object):

   def __init__(self, host, port, wsgi_app, ws_handler):
      self.host = host
      self.port = port
      self.wsgi_app = wsgi_app
      self.ws = WebSocketWSGIApplication(handler_cls=get_class(ws_handler))

   def __call__(self, environ, start_response):

      ws = environ.get('HTTP_UPGRADE')
      if ws == 'websocket':
         return self.ws(environ, start_response)

      return self.wsgi_app(environ, start_response)

