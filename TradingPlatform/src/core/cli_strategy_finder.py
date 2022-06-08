
import os
import sys

import time

import threading

from engine import Engine


import logging
logger = logging.getLogger("ex_logger")


class StrategyThread(threading.Thread):
    """
    strategy thread
    """
    
    config = {}
    report_file_name = ""
    
    def __init__(self, config):
        """
        init 
        """
        threading.Thread.__init__(self)
        self.config = config
        
        
    def run(self):
        """
        run
        """
        
        engine = Engine(None, None)
        engine.set_config(self.config)
        engine.run()
        engine.report_strategy()
        
    
def main(args):
    """
    main
    """
    
    # init engine without web socket and without
    
    init_price_ma = 5
    init_price_roc_th_ = -0.005
    
    for signal_thresh_idx in range(1, 10):
            
        for profit_trgt_idx in range(1, 10):
            
            for price_ma_idx in range(1, 10):
                
                for price_roc_idx in range(1, 10):
            
                    signal_thresh = float(signal_thresh_idx - 1) / 10000 
                    profit_trgt = float(profit_trgt_idx) / 10000
                    price_ma = price_ma_idx
                    price_roc_th = float(float(price_roc_idx) / 1000) * (-1)
                    
                    config = {}
                    config['exchange_client_name'] = "binance"
                    config['api_key'] = ""
                    config['api_secret'] = ""
                    config['number_of_periods'] = int(500)
                    config['period_type'] = "1m"
                    config['boll_rolling_window'] = int(21)
                    config['market_code'] = "BTCUSD"
                    config['starting_amnt'] = float(10)
                    config['input_pos_ttl'] = int(1440)
                    config['enable_lvdt'] = False
                    config['enable_trxs'] = False
                    
                    config['signal_thresh'] = float(signal_thresh)
                    config['profit_trgt'] = float(profit_trgt)
                    
                    config['price_ma_'] = int(price_ma)
                    config['price_roc_th_'] = float(price_roc_th)
                    
                    try:
                        t = StrategyThread(config)
                        t.start()
                        t.join()
                    
                    except:
                        
                        pass
                        
                    
            
            
                
                
            
            
    

if __name__ == '__main__':
    """
    cli launcher
    """
    main(sys.argv)
        
    