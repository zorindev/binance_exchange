
import threading
import time

queue = []

class Engine(object):
    """
    engine
    """
    
    def __init__(self, global_queue):
        
        self.queue = global_queue
        self.count = 0
        
    def run(self):
        
        while(1):
    
            self.count += 1
        
            self.queue.append(self.count)
            
            time.sleep(1)
    
    
    

class Transmission(object):
    """
    transmission
    """
    
    def __init__(self, global_queue):

        self.queue = global_queue
        
    
    def run(self):
       
        while(1):
            
            if(len(self.queue) > 0):
                
                item = self.queue.pop(0)
                print(item)
            
            time.sleep(1)
    
    
    
def main():
    """
    """
    
    en = Engine(queue)
    tr = Transmission(queue)
    
    en_thread = threading.Thread(target = en.run)
    tr_thread = threading.Thread(target = tr.run)
    
    en_thread.start()
    tr_thread.start()
    
if(__name__ == "__main__"):
    main()