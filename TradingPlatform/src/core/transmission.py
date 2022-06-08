
import asyncio
import time
import tornado.websocket

import traceback
import logging
logger = logging.getLogger("ex_logger")

class Transmission(object):
    """
    transmission - this thread can be killed and reinstantiated with a fresh working websocket without having to kill the engine
    """
    
    DEFAULT_PARKED_FREQUENCY    = 5
    DEFAULT_RUNNING_FREQUENCY   = 1
    DEFAULT_STATIC_FREQUENCY    = 0
    
    def __init__(self, sigq = None, msgq = None, websocket = None, encoder = None, config = None):
        """
        init
        """
        
        logger.info("TRANSMISSION INIT")
        
        self.frequency = self.DEFAULT_RUNNING_FREQUENCY
        
        try:
            self.config = config
            if(self.config != None):
                if(self.config['enable_lvdt'] != True):
                    self.frequency = self.DEFAULT_STATIC_FREQUENCY
                    
        except Exception:
            traceback.print_exc() 
        
        self.signal_queue = sigq
        self.message_queue = msgq
        self.websocket = websocket
        self.encoder = encoder
        
        self.on = True
        self.is_in_gear = False
        
        self.ping_transmission = False
        
        logger.info(" DONE TRANSMISSION INIT ")
    
        
    #@profile    
    def neutral(self):
        """
        not in gear
        """
        
        logger.info(" placing transmission in neutral ")
        self.is_in_gear = False
        self.frequency = self.DEFAULT_PARKED_FREQUENCY
        
    #@profile
    def in_gear(self):
        """
        in gear
        """
        
        logger.info(" placing transmission in gear ")
        self.is_in_gear = True
        self.frequency = self.DEFAULT_RUNNING_FREQUENCY
        if(self.config != None):
            if(self.config['enable_lvdt'] != True):
                self.frequency = self.DEFAULT_STATIC_FREQUENCY
        
        
    def ping(self):
        """
        ping transmission
        """
        self.ping_transmission = True
        
            
    #@profile    
    def run(self):
        """
        thread RT
        """
        
        logger.info(" entered transmission run ")
        while True:
            
            if(self.is_in_gear):    
                #logger.info(" running transmission. frequency is %s", str(self.frequency))
                        
                if(len(self.message_queue) > 0):
                    
                    logger.info(" transmission received a message")
                    message = self.message_queue.pop(0)
                    
                    if(message == "OFF"):
                        logger.info(" OFF signal received. stopping transmission ")
                    
                    try:
                        logger.info(" sending message through the websocket ... ")
                        self.websocket.write_message(self.encoder.json_encode(message))
                        
                    except Exception as e:
                        logger.error(" exception occured while sending the message through the socket: %s", str(e))
                        
            elif(self.ping_transmission):
                logger.info(" transmisson ping received. responding  ... ")
                self.websocket.write_message(self.encoder.json_encode(" transmission ping "))
                self.ping_transmission = False
                    
                
            time.sleep(self.frequency)
            
        logger.info(" transmission exec loop has been exited ")
            
                