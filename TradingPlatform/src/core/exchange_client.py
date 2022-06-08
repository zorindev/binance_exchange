

import logging
import traceback
logger = logging.getLogger("ex_logger")


class ExchangeClient(object):
    
    exchange_client = None
    
    def __init__(self):
        """
        init
        """
        
        logger.info("INIT EXCHANGE_CLIENT_FACTORY")
        
        
    def get_exchange_client(
        self, 
        
        # api
        api_key, 
        api_secret,
        
        # market 
        exchange_client_name,
        market_code,
        starting_amount,
        
        # bollinger  
        number_of_periods, 
        period_type, 
        boll_rolling_window,
        signal_thresh,
        
        # rsi
        rsi_period,
        stoch_period,
        smooth_k,
        smooth_d,
        rsi_entry_limit,
        rsi_exit_limit,
        
        # sma
        ctrl_sma_limit,
        
        # control
        enable_live_data,
        enable_transactions,
        enable_bollinger_signal_eval,
        enable_stoch_rsi_signal_eval,
        enable_sma_signal_eval,
        static_df_period
        
        ):
        
        # return <class 'binance_client.binance_client'>
        #module = __import__(exchange_client_name + "_client")
        #class_ = getattr(module, exchange_client_name + "_client")
        
        # returns core.binance_client
        logger.info("IN GET EXCHANGE CLIENT")
        
        logger.info("INSTANTIATION CLIENT MODULE")
        exchange_client_name = "binance"
        
        try:
            module = __import__("core." + exchange_client_name + "_client")
        except Exception as e:
            print(e)
            traceback.print_exc()
            
        class_ = getattr(module, exchange_client_name + "_client")
        class_ = getattr(class_, exchange_client_name + "_client")
        logger.info("DONE INSTANTIATING CLIENT MODULE")
        
        logger.info("INSTANTIATING EXCANGE CLIENT IN FACTORY")
        self.exchange_client = class_(
            # api
            api_key, 
            api_secret,
            
            # market 
            exchange_client_name,
            market_code,
            starting_amount,
            
            # bollinger  
            number_of_periods, 
            period_type, 
            boll_rolling_window,
            signal_thresh,
            
            # rsi
            rsi_period,
            stoch_period,
            smooth_k,
            smooth_d,
            rsi_entry_limit,
            rsi_exit_limit,
            
            # sma
            ctrl_sma_limit,
            
            # control
            enable_live_data,
            enable_transactions,
            enable_bollinger_signal_eval,
            enable_stoch_rsi_signal_eval,
            enable_sma_signal_eval,
            static_df_period
        )
        logger.info("DONE INSTANTIATING EXCANGE CLIENT IN FACTORY")
        
        return self.exchange_client
    
    
    
    