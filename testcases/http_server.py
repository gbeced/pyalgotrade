import threading
import http.server


class WebServerThread(threading.Thread):
    def __init__(self, host, port, handlerClass):
        super(WebServerThread, self).__init__()
        self.__host = host
        self.__port = port
        self.__handlerClass = handlerClass
        self.__server = None

    def run(self):
        def handler_cls_builder(*args, **kwargs):
            return self.__handlerClass(*args, **kwargs)

        self.__server = http.server.HTTPServer((self.__host, self.__port), handler_cls_builder)
        self.__server.serve_forever()

    def stop(self):
        self.__server.shutdown()


# handlerClass should be a subclass of (BaseHTTPServer.BaseHTTPRequestHandler.
# The handler instance will get a thread and server attribute injected.
def run_webserver_thread(host, port, handlerClass):
    wss_thread = WebServerThread(host, port, handlerClass)
    wss_thread.start()
    return wss_thread
