

"""


/usr/bin/python service.py > /dev/null 2>&1 &


"""

import sys
import asyncio

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import time 


import tornado
import tornado.platform.asyncio
from tornado.options import define, options
import threading
from core import engine
from core import transmission



import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("ex_logger")

nh = logging.NullHandler()

rfh = RotatingFileHandler(filename="./logs/process.log", mode='a', maxBytes=50000000, backupCount=25, encoding=None, delay=False)
rfh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rfh.setFormatter(formatter)

logger.handlers = []
logger.propagete = False
logger.addHandler(rfh)

logging.getLogger("tornado.access").handlers = []
logging.getLogger("tornado.application").handlers = []
logging.getLogger("tornado.general").handlers = []

logging.getLogger("tornado.access").addHandler(nh)
logging.getLogger("tornado.application").addHandler(nh)
logging.getLogger("tornado.general").addHandler(nh)

logging.getLogger("tornado.access").propagate = False
logging.getLogger("tornado.application").propagate = False
logging.getLogger("tornado.general").propagate = False


signal_queue = []
message_queue = []

define("port", default=8888, help="", type=int)

class Application(tornado.web.Application):
    
    def __init__(self):
        logger.info("SERVICE INIT")
        
        # WEB INIT
        handlers = [(r"/", IndexHandler), (r"/websocket", SocketHandler)];
        settings = dict(
            cookie_secret = "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path = os.path.join(os.path.dirname(__file__), "web/templates"),
            static_path = os.path.join(os.path.dirname(__file__), "web/static"),
            xsrf_cookies = True,
            debug = True
        )
        
        super(Application, self).__init__(handlers, **settings)    
        
        
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
        

    
engine_thread = None
en = None  


historic_enable_live_data = None  

        
class SocketHandler(tornado.websocket.WebSocketHandler):
    
    tr = None
    ws = None
    
    transmission_thread = None

    def open(self):
        """
        open socket
        """
        
        global engine_thread
        global en
        global historic_enable_live_data

        logger.info("opening websocket")        
        SocketHandler.ws = self
        
        
    
    def on_close(self):
        """
        close socket
        """
        
        #global engine_thread
        #global en
        #global historic_enable_live_data
        
        logger.info("closing websocket")
        #SocketHandler.ws = None
        #self.tr = None
        #self.transmission_thread = None
        
        
    def on_message(self, message):
        """
        on message 
        """
        
        global engine_thread
        global en
        global historic_enable_live_data
        
        parsed = tornado.escape.json_decode(message)
        logger.info("received websocket message")
        if "action" in parsed and parsed['action'] != None and parsed['action'] == "start" and engine_thread == None:
            logger.info("message action = %s", parsed['action'])
            
            if(en == None):
                logger.info(" initializing engine from service")
                en = engine.Engine(
                    sigq = signal_queue,
                    msgq = message_queue
                )
                
            if(en):
                en.start_was_called()
                en.set_config(parsed)
                
            if("enable_lvdt" in parsed):
                historic_enable_live_data = parsed['enable_lvdt']
                logger.info(" HISTORIC_ENABLE_LIVE_DATA IS SET")
                
            if(self.tr == None):
                logger.info(" INIT TRANSMISSION CALLED FROM SERVICE ")
                self.tr = transmission.Transmission(
                    sigq = signal_queue,
                    msgq = message_queue,
                    websocket = self, 
                    encoder = tornado.escape,
                    config = parsed
                )    
                logger.info(" DONE INIT TRANSMISSION CALLED FROM SERVICE ")
            
            if(engine_thread == None):
                logger.info("INIT ENGINE THREAD")
                engine_thread = threading.Thread(target = en.run)
                logger.info("DONE INIT ENGINE THREAD")
                    
            if(engine_thread):
                logger.info("START ENGINE")
                engine_thread.start()
                logger.info("DONE START ENGINE")
                
            if(self.transmission_thread == None):
                logger.info("INIT TRANSMISSOIN THREAD")
                self.transmission_thread = threading.Thread(target = self.tr.run)
                logger.info("DONE INIT TRANSMISSOIN THREAD")
                
                logger.info("START TRANSMISSION")    
                self.transmission_thread.start()
                logger.info("DONE START TRANSMISSION")
                
            if(self.tr):    
                logger.info("PUT TRANSMISSION IN GEAR")
                self.tr.in_gear()
                logger.info("DONE PUT TRANSMISSION IN GEAR")

        
        elif "action" in parsed and parsed['action'] != None and parsed['action'] == "stop" and engine_thread != None:
            logger.info("message action = %s", parsed['action'])
            
            if(en):
                en.stop_was_called()
                en.reset_client()
            
            engine_thread = None
            en = None
            
            if(self.tr):
                self.tr.neutral()
            
            
        elif "action" in parsed and parsed['action'] != None and parsed['action'] == "status":
            
            logger.info("message action = %s", parsed['action'])
            
            #thread_is_alive = engine_thread.is_alive()
            status = ""
            
            logger.info(" getting status from service ")
            if(engine_thread):
                logger.info(" engine thread initialised ")
                
                if(en):
                    logger.info(" engine initialized ")
                    en_state = en.get_state()
                    
                    if(en_state >= 0):
                        status = "running"
                            
                    elif(en_state < 0):
                        status = "stopped"
                            
            else:
                status = "not_initialized"
                
            logger.info(" status = %s", status)
            
            self.write_message(tornado.escape.json_encode({"status": status}))
                
                
        elif "action" in parsed and parsed['action'] != None and parsed['action'] == "reconnect" and engine_thread != None:
            
            logger.info("message action = %s", parsed['action'])
            
            if(self.tr):
                self.tr.ping()
            
            
            parsed['enable_lvdt'] = historic_enable_live_data
            self.tr = transmission.Transmission(
                sigq = signal_queue,
                msgq = message_queue,
                websocket = self, 
                encoder = tornado.escape,
                config = parsed
            )
            
            self.tr.in_gear()
            
            self.transmission_thread = threading.Thread(target = self.tr.run)
            self.transmission_thread.start()
            
            
        
    
    @classmethod
    def send_updates(cls, message):
        """
        send update 
        """
        
        message = tornado.escape.json_encode(message)
        logger.info("sending an update from websocket: %s", message)    
        cls.ws.write_message(message)
        
        
def main():
    
    logger.info(" application init ... ")
    #options.logging = None
    #logging.getLogger('tornado.access').disabled = True
     
    asyncio.set_event_loop_policy(tornado.platform.asyncio.AnyThreadEventLoopPolicy())
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
    
    
if __name__ == "__main__":
    main()
