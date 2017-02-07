import threading
from wsgiref import simple_server

from ws4py.server import wsgirefserver
from ws4py.server import wsgiutils


class WebSocketServerThread(threading.Thread):
    def __init__(self, host, port, webSocketServerClass):
        super(WebSocketServerThread, self).__init__()
        self.__host = host
        self.__port = port
        self.__webSocketServerClass = webSocketServerClass
        self.__server = None

    def run(self):
        def handler_cls_builder(*args, **kwargs):
            return self.__webSocketServerClass(*args, **kwargs)

        self.__server = simple_server.make_server(
            self.__host,
            self.__port,
            server_class=wsgirefserver.WSGIServer,
            handler_class=wsgirefserver.WebSocketWSGIRequestHandler,
            app=wsgiutils.WebSocketWSGIApplication(handler_cls=handler_cls_builder)
        )
        self.__server.initialize_websockets_manager()
        self.__server.serve_forever()

    def stop(self):
        self.__server.shutdown()


# webSocketServerClass should be a subclass of ws4py.websocket.WebSocket
def run_websocket_server_thread(host, port, webSocketServerClass):
    wss_thread = WebSocketServerThread(host, port, webSocketServerClass)
    wss_thread.start()
    return wss_thread
