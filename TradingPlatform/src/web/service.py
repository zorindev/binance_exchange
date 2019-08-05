

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import time 


from tornado.options import define, options

import threading
from core import engine
engine_thread = None


define("port", default=8888, help="", type=int)


class Application(tornado.web.Application):
    
    engine = None
    
    def __init__(self):
        
        # WEB INIT
        handlers = [(r"/", IndexHandler), (r"/test", TestHandler), (r"/websocket", SocketHandler)];
        settings = dict(
            cookie_secret = "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies = True,
            debug = True
        )
        
        super(Application, self).__init__(handlers, **settings)    
        
        
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
        
        
class TestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("test.html")
        
        
class SocketHandler(tornado.websocket.WebSocketHandler):
    
    en = None
    ws = None
    
    def open(self):
        print(" opened ")
        SocketHandler.ws = self
        self.en = engine.Engine(websocket = SocketHandler.ws, encoder = tornado.escape)
    
    
    def on_close(self):
        print(" closed ");
        SocketHandler.ws = None
        
        
    def on_message(self, message):
        
        global engine
        global engine_thread
        
        parsed = tornado.escape.json_decode(message)
        
        if "action" in parsed and parsed['action'] != None and parsed['action'] == "start" and engine_thread == None:
            print("starting the engine")
            self.en.set_config(parsed)
            engine_thread = threading.Thread(target=self.en.run)
            engine_thread.start()
        
        elif "action" in parsed and parsed['action'] != None and parsed['action'] == "stop" and engine_thread != None:
            print("stopping the engine")
            self.en.set_state(-1)
            self.en.reset_client()
            engine_thread = None
            
        else:
            
            print(" cannot process ", parsed, engine_thread)
            engine_thread = None
        
    
    @classmethod
    def send_updates(cls, message):
        message = tornado.escape.json_encode(message)    
        cls.ws.write_message(message)
        
        
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
    
    
if __name__ == "__main__":
    main()
