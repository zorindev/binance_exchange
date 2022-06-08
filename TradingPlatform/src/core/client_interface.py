
import logging
logger = logging.getLogger("ex_logger")

from interface import implements, Interface

class ExchangeClientInterface(Interface):
    
    #@profile
    def get_server_time(self):
        pass
    
    #@profile
    def ping(self):
        pass
    
    #@profile
    def get_current_price(self, str_symbol, str_period, int_number_of_records):
        pass
    
    #@profile
    def load_exchange_info(self):
        pass
     
    #@profile
    def compose_data_frame(self, given_state):
        pass
    
    #@profile
    def get_dataframe(self):
        pass
    
    #@profile
    def set_data_frame(self, df):
        pass
    
    #@profile
    def get_df_compose_time(self):
        pass
    
    #@profile
    def get_klines_exec_time(self):
        pass
    
    #@profile
    def get_call_count(self):
        pass
    
    #@profile
    def get_direction(self):
        pass
    
    #@profile
    def get_pofit(self):
        pass
    
    #@profile
    def get_cycle_profit(self):
        pass
    
    #@profile
    def get_average_trade_duration(self):
        pass
    
    #@profile
    def get_average_gain(self):
        pass
    
    #@profile
    def get_cycle_count(self):
        pass
    
    #@profile
    def get_cycle_duration(self):
        pass
    
    #@profile
    def get_static_df_file_name(self):
        pass    
    
    #@profile
    def get_dfs_time_boundary_utx(self):
        pass
    
    #@profile
    def get_dfs_timeboundary_str(self):
        pass

    #@profile
    def get_total_cycle_time(self):
        pass
    
    #@profile
    def get_average_purchase_price(self):
        pass
    
    
    
    
    
    #@profile
    def get_target_entry_price(self):
        pass
    
    
    #@profile
    def get_target_units_bought(self):
        pass
    
    #@profile
    def get_avg_units_bought(self):
        pass
    
    #@profile
    def get_target_units_sold(self):
        pass
    

    #@profile
    def get_exit_price(self):
        pass
    
    
    def get_avg_exit_price(self):
        pass
    
    
    #@profile
    def get_bids_total(self):
        pass
    
    #@profile
    def get_bids_avg_price(self):
        pass
    
    #@profile
    def get_asks_total(self):
        pass
    
    #@profile
    def get_asks_avg_price(self):
        pass
    
    #@profile
    def get_price_sma7_delta_sum(self):
        pass
    
    #@profile
    def get_price_sma25_delta_sum(self):
        pass
    
    #@profile
    def get_price_smactrl_delta_sum(self):
        pass
    
    def get_price_sma_back_ctrl_delta_sum(self):
        pass
    
    def get_error(self):
        pass
    
    def get_buy_fee(self):
        pass
    
    def get_sell_fee(self):
        pass
    
    def get_buy_fee_currency(self):
        pass
    
    def get_sell_fee_currency(self):
        pass
    
    
    
    
    
    