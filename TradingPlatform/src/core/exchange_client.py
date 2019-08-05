

class ExchangeClient(object):
    
    exchange_client = None
    
    def __init__(self):
        pass
        
        
    def get_exchange_client(self, exchange_client_name, api_key, api_secret, number_of_periods, period, rolling_window):
        module = __import__(exchange_client_name + "_client")
        class_ = getattr(module, exchange_client_name + "_client")
        self.exchange_client = class_(api_key, api_secret, number_of_periods, period, rolling_window)
        
        return self.exchange_client
    
    
    
    