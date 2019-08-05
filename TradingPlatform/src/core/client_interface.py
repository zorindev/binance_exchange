
from interface import implements, Interface

class ExchangeClientInterface(Interface):
    
    def get_server_time(self):
        pass
    
    def get_current_price(self, str_symbol, str_period, int_number_of_records):
        pass
    
    def get_dataframe(self):
        pass
    
    def set_data_frame(self, df):
        pass
    
    def get_df_compose_time(self):
        pass
    
    def get_klines_exec_time(self):
        pass
    
    def get_call_count(self):
        pass