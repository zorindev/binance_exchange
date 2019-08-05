'''
Created on May 18, 2019

@author: leaz
'''


import time
from exchange_client import ExchangeClient
import pandas as pd



class Engine(object):
    
    state = 0
    
    websocket = None
    encoder = None
    
    exchange_name = None
    
    exchange_client_factory = ExchangeClient()
    exchange_client = None
    
    
    def __init__(self, websocket = None, encoder = None):
        
        self.websocket = websocket
        self.encoder = encoder
    
    def set_config(self, config):
        
        print("config: ", config)
        self.exchange_client = self.exchange_client_factory.get_exchange_client(
            config['exchange_client_name'], 
            config['api_key'], 
            config['api_secret'],
            config['number_of_periods'],
            config['period'],
            config['rolling_window']
        )
        
        
    def run(self):
        
        while self.state != -1:
            
            
            if self.state == 0:
                """
                attempts to buy
                """
                
                try:
                    self.state = self.exchange_client.compose_data_frame("BNBBTC", self.state)
                
                    self.report()
                    
                except:
                    pass
                
            
            #elif self.state == 1:
            #    """
            #    wait for the buy to complete
            #    """
            #    pass
            
            
            elif self.state == 2:
                """
                attempt to sell
                """
                self.state = self.exchange_client.compose_data_frame("BNBBTC", self.state)
                
                self.report()
            
            
            time.sleep(1)
            #break
            
        
    def report(self):
        
        
        df = self.exchange_client.get_dataframe()
        #df.dropna(inplace = True)
        
        msg = {
            "exchange": "exchange",
            
            "market": "market",
            
            "open_time": pd.Series(df['open_time_str']).to_json(orient='values'),
            
            "K": pd.Series(df['%K']).to_json(orient='values'),
            
            "D": pd.Series(df['%D']).to_json(orient='values'),
            
            "BLL": pd.Series(df['boll_low']).to_json(orient='values'),
            
            "BLU": pd.Series(df['boll_high']).to_json(orient='values'),
            
            "close": pd.Series(df['close']).to_json(orient='values'),
            
            "signal": pd.Series(df['signal']).to_json(orient='values'),
            
            "signal_date": pd.Series(df['signal_date']).to_json(orient='values'),
            
            "df_compose_time": self.exchange_client.get_df_compose_time(),
            
            "klines_exec_time": self.exchange_client.get_klines_exec_time(),
            
            "klines_size": len(df.index),
            
            "klines_call_count": self.exchange_client.get_call_count(),
            
            "state": self.state
        }
        
        if self.websocket != None and self.encoder != None:
            self.websocket.write_message(self.encoder.json_encode(msg))
        else:
            print(" websocket is not available in engine ")
            
            
    def set_state(self, state):
        self.state = state
        
        
    def reset_client(self):
        self.exchange_client.set_data_frame(None)
        
        
        