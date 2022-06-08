

import time
from core.exchange_client import ExchangeClient
import pandas as pd

import sys
import traceback
import os
import json
import timeit

import gc


import logging
logger = logging.getLogger("ex_logger")


class Engine(object):
    
    MAX_ATTEMPTED_RECONNECTION = 25
    
    SLEEP_DURATION = 10
    
    RECONNECT_SLEEP_DURATION = 25
    
    RUNNING = 1
    
    OFF = 0
    
    #@profile 
    def __init__(self, sigq = None, msgq = None):
        """
        init 
        """
        
        logger.info("ENGINE INIT")
        
        self.signal_queue = sigq
        self.message_queue = msgq
        self.config = {}
        self.state = 0
        self.prev_state = 0
        self.exchange_client_factory = ExchangeClient()
        self.exchange_client = None
        self.stop_called = False
        self.attempted_reconnection_count = 0
        self.sleep_prd = 0
        
        logger.info(" ENGINE INIT DONE ")
    
    #@profile    
    def set_config(self, config):
        
        logger.info(" ENGINE SET CONFIG ")
        self.config = config
        
        self.exchange_client = self.exchange_client_factory.get_exchange_client(
            
            # api keys
            config['api_key'], 
            config['api_secret'],
            
            # market
            config['exchange_client_name'], 
            config['market_code'],
            config['starting_amnt'],
            
            # bollinger
            config['number_of_periods'],
            config['period_type'],
            config['boll_rolling_window'],
            config['signal_thresh'],
            
            # rsi
            config['rsi_period_'],
            config['stoch_period_'],
            config['smooth_k_'],
            config['smooth_d_'],
            config['rsi_entry_limit_'],
            config['rsi_exit_limit_'],
            
            # sma
            config['ctrl_sma_limit_'],
            
            # control
            config['enable_lvdt'],
            config['enable_trxs'],
            config['enable_boll'],
            config['enable_stochrsi'],
            config['enable_sma'],
            config['static_df_period_']
        )
        
        logger.info(" initialised the exchange client in engine: %s", config['exchange_client_name'])
        logger.info(" ENGINE SET CONFIG DONE ")
        
    #@profile 
    def run(self):
        """
        run engine thread
        """
        
        self.sleep_prd = self.SLEEP_DURATION
        if(self.config['enable_lvdt'] != True):        
            self.sleep_prd = 0
            
        else:    
            self.exchange_client.load_exchange_info()
            
            
        while self.state != -1:
         
            logger.info("running the engine, the frequency is %s", str(self.sleep_prd))
            
            if(self.stop_called == True):
                logger.info("terminating engine loop")
                self.queue_message("OFF", self.OFF)
                return
            
            if self.state == 0:
                """
                attempts to buy
                """
                
                logger.info("engine state is 0, attempting to buy")
                
                self.prev_state = self.state
                self.state = self.exchange_client.compose_data_frame(self.state)
                if(self.state > -1):
                    logger.info("response received from ex change client, now state is %s", str(self.state))
                    if(self.message_queue != None):
                        self.report()
                    else:
                        logger.info("engine.report was not called because the message was not added to the queue, state is %s", self.state)
                else:   
                    if(self.state == -1):
                        
                        # do report to propagate the error
                        self.report()
                        while(len(self.message_queue) > 0):
                            logger.info("waiting for the error message to propagate to UI ... ")
                            time.sleep(self.sleep_prd)
                        
                        logger.info("state had changed to -1 from a phase of state = 0")
                        self.stop_was_called()
                        # send a message to transmission to turn off
                        self.queue_message("OFF", self.OFF)
                        break
                     
                    elif(self.state == -2):
                        self.handle_connection_issue()
                    
            elif self.state == 1:
                """
                wait for the buy to complete
                """
                logger.info(" in state 1 in engine ")
                self.state = self.exchange_client.compose_data_frame(self.state)
                
                if(self.state > -1):
                    if(self.message_queue != None):
                        self.report()
                    logger.info(" in state 2  after report ")
                
                else:
                    if(self.state == -1):
                        logger.info("state had changed to -1 from a phase of state = 0")
                        
                        # do report to propagate the error
                        self.report()
                        while(len(self.message_queue) > 0):
                            logger.info("waiting for the error message to propagate to UI ... ")
                            time.sleep(self.sleep_prd)
                        
                        self.stop_was_called()
                        # send a message to transmission to turn off
                        self.queue_message("OFF", self.OFF)
                        break 
                    elif(self.state == -2):
                        self.handle_connection_issue()
                    
            
            elif self.state == 2:
                """
                attempt to sell
                """
                logger.info(" in state 2  before composing a df")
                self.prev_state = self.state
                self.state = self.exchange_client.compose_data_frame(self.state)
                logger.info(" in state 2  after composing a df")
                
                if(self.state > -1):
                    if(self.message_queue != None):
                        self.report()
                        
                    logger.info(" in state 2  after report ")
                    
                else:
                    """
                    turned off
                    """
                    
                    if(self.state == -1):
                        logger.info("Transitioned from state 2 to state -1. An error occured in client .... ")
                        
                        # do report to propagate the error
                        self.report()
                        while(len(self.message_queue) > 0):
                            logger.info("waiting for the error message to propagate to UI ... ")
                            time.sleep(self.sleep_prd)
                        
                        self.stop_was_called()
                    
                        # send a message to transmission to turn off
                        self.queue_message("OFF", self.OFF)
                        break
                
                    elif(self.state == -2):
                        logger.info(" In state 2 connection issue occurred. Attempting reconnection ... ")
                        self.handle_connection_issue()
                        
            elif(self.state == 3):
                """
                wait for sell to complete
                """
                logger.info(" In Engine state 3, waiting for sell to complete ")
                self.state = self.exchange_client.compose_data_frame(self.state)
                
                if(self.state > -1):
                    if(self.message_queue != None):
                        self.report()
                    logger.info(" in state 2  after report ")
                
                else:
                    if(self.state == -1):
                        logger.info("state had changed to -1 from a phase of state = 0")
                        
                        # do report to propagate the error
                        self.report()
                        while(len(self.message_queue) > 0):
                            logger.info("waiting for the error message to propagate to UI ... ")
                            time.sleep(self.sleep_prd)
                        
                        self.stop_was_called()
                        # send a message to transmission to turn off
                        self.queue_message("OFF", self.OFF)
                        break 
                    elif(self.state == -2):
                        self.handle_connection_issue()
                            
            
            elif(self.state == -1):
                """
                exit called
                """
                logger.info(" Returned to Engine with state = -1. Exiting .... ")
                self.stop_was_called()
                # send a message to transmission to turn off
                self.queue_message("OFF", self.OFF)
                break
    
            elif self.state == -2:
                """
                connection error occured
                """
                self.handle_connection_issue()
                
            logger.info(" SLEEP PEREIOD = %s ", self.sleep_prd)
            time.sleep(self.sleep_prd)
            logger.info("DONE WATING ")
            #break
            
        logger.info(" exited the loop because state was %s ", str(self.state))
        logger.info(" reseting state to init ")
        self.state = 0
        
    #@profile     
    def handle_connection_issue(self):
        """
        handle reconnection
        """

        while(self.attempted_reconnection_count <= self.MAX_ATTEMPTED_RECONNECTION):   
            logger.info(" Attempting reconnection %s", str((self.attempted_reconnection_count + 1)))
            time.sleep(self.RECONNECT_SLEEP_DURATION)
                    
            try:
                logger.info(" attempting reconnection in Engine ")
                server_time = self.exchange_client.ping()
                if("serverTime" in server_time):
                    self.attempted_reconnection_count = 0    
                    self.state = self.prev_state
                    logger.info(" reconnected .... ")
                    break
                
                else:                    
                    logger.warn(" reconnection was unsuccessful  but there was a response from the server, attempting next reconnection ")
                    self.attempted_reconnection_count += 1
                    
            except:
                logger.warn(" reconnection was unsuccessful, attempting next reconnection ")
                self.attempted_reconnection_count += 1
                    
                
        if(self.attempted_reconnection_count <= self.MAX_ATTEMPTED_RECONNECTION):
            """
            reconnected, continue to run
            """
            self.attempted_reconnection_count = 0;
            logger.info(" reconnected, resetting reconnection counter and resuming ... ")
            return
        
        else:
            """
            could not reconnect, exit
            """
            logger.info(" could not reconnect, the process is exiting ... ")
            logger.info(" sending a stop signal to transmissions ")
            self.queue_message("OFF", self.OFF)
            self.sleep_prd = self.SLEEP_DURATION
            if(self.config['enable_lvdt'] != True):
                self.sleep_prd = 0
            self.state = -1
                
    #@profile   
    def get_cleared_signal(self, df, field):
        """
        gets non zero numpy list of signal values
        """
        
        logger.info(" clearing signal for %s", field)
        try:
            s = df[field]
            l = s.to_list()
            ll = [i for i in l if i != 0 and i != "\"NaN\"" and i != "NaN" and i != ""] 
            cleared_signal_series = pd.Series(ll)
            return cleared_signal_series
        
        except:
            logger.error(" error occurred while clearing signal %s", field)
            return pd.Series.empty
        
    #@profile   
    def report_strategy(self):
        """
        report strategy
        """
        logger.info(" reporting strategy results ... ")
        ux = str(time.time())
        profit = round(self.exchange_client.get_pofit(), 6)
        file_name = "../zreport/" + str(profit) + "_" + ux + ".txt"
        self.config['profit'] = profit
        
        with open(file_name, 'w') as file:
            file.write(json.dumps(self.config, indent=4, sort_keys=False))
            
    #@profile 
    def report(self):
        """
        report df state
        """
        logger.info(" engine is reporting ... ")
        df = self.exchange_client.get_dataframe()
        
        try:
            if(df.empty):
                logger.error(" engine received an empty dataframe. setting state to -1 and turning the engine off ")
                
                msg = {
                "ERROR": self.exchange_client.get_error()
                }
                if self.message_queue != None and self.signal_queue != None:
                    #logger.error(" the following message is delivered by the engine, %s", json.dumps(msg)); 
                    self.queue_message(msg, self.RUNNING)
                
                self.state = -1
                return
            
        except:
            logger.error(" engine received an empty dataframe. setting state to -1 and turning the engine off ")
            
            msg = {
                "ERROR": self.exchange_client.get_error()
            }
            if self.message_queue != None and self.signal_queue != None:
                #logger.error(" the following message is delivered by the engine, %s", json.dumps(msg)); 
                self.queue_message(msg, self.RUNNING)
            
            self.state = -1
            return
        
        # params
        #profit = round(self.exchange_client.get_pofit(), 6)
        cycle_duration = self.exchange_client.get_cycle_duration()
        
        last_profit = round(self.exchange_client.get_cycle_profit(), 6)
        avg_trade_duration = self.exchange_client.get_average_trade_duration()
        avg_gain = round(self.exchange_client.get_average_gain(), 6)
        cycle_count = self.exchange_client.get_cycle_count()
        
        total_cycle_time = self.exchange_client.get_total_cycle_time()
        
        target_entry_price = self.exchange_client.get_target_entry_price()
        exit_price = self.exchange_client.get_exit_price()
        
        # get cleared signals
        buy_signal_field = 'buy_signal'
        buy_signal_date_field = 'buy_signal_date'
        sell_signal_field = 'sell_signal'
        sell_signal_date_field = 'sell_signal_date'        
        cleared_buy_signal          =   self.get_cleared_signal(df, buy_signal_field)
        cleared_buy_signal_dates    =   self.get_cleared_signal(df, buy_signal_date_field)
        cleared_sell_signal         =   self.get_cleared_signal(df, sell_signal_field)
        cleared_sell_signal_dates   =   self.get_cleared_signal(df, sell_signal_date_field)
        
        msg = {
            
            # generic
            "exchange": "exchange",
            "market": "market",
            "open_time": json.dumps(df['open_time_str'].tolist()), #pd.Series(df['open_time_str']).to_json(orient='values'),
            
            # bollinger
            "BLLC": json.dumps(df['boll_low_close'].tolist()), #pd.Series(df['boll_low_close']).to_json(orient='values'),
            "BLUC": json.dumps(df['boll_high_close'].tolist()), #pd.Series(df['boll_high_close']).to_json(orient='values'),
            "BLMC": json.dumps(df['boll_middle_close'].tolist()),
            
            # a stochastic of the RSI of close
            "STOCH_RSI_K": json.dumps(df['stoch_rsi_k'].tolist()), #pd.Series(df['stoch_rsi_k']).to_json(orient='values'),
            "STOCH_RSI_D": json.dumps(df['stoch_rsi_d'].tolist()), #pd.Series(df['stoch_rsi_d']).to_json(orient='values'),
            
            "PRICE_SMA_7": json.dumps(df['price_sma7'].tolist()), #pd.Series(df['price_sma7']).to_json(orient='values'),
            "PRICE_SMA_25": json.dumps(df['price_sma25'].tolist()), #pd.Series(df['price_sma25']).to_json(orient='values'),
            "PRICE_SMA_CTRL": json.dumps(df['price_smactrl'].tolist()), #pd.Series(df['price_smactrl']).to_json(orient='values'),
            
            "EMA_8": json.dumps(df['ema_8'].tolist()),
            "EMA_13": json.dumps(df['ema_13'].tolist()),
            "EMA_21": json.dumps(df['ema_21'].tolist()),
            "EMA_55": json.dumps(df['ema_55'].tolist()),
            
            "EMA_8_13_DIFF": json.dumps(df['ema_8_13_diff'].tolist()), 
            
            #"PRICE_SMA_BACK_CTRL": json.dumps(df['price_sma_back_ctrl'].tolist()),
            
            "PRICE_SMA_7_DELTA_SUM": self.exchange_client.get_price_sma7_delta_sum(),
            "PRICE_SMA_25_DELTA_SUM": self.exchange_client.get_price_sma25_delta_sum(),
            "PRICE_SMA_CTRL_DELTA_SUM": self.exchange_client.get_price_smactrl_delta_sum(),
            
            
            #"PRICE_SMA_BACK_CTRL_DELTA_SUM": self.exchange_client.get_price_sma_back_ctrl_delta_sum(),
            
            # price
            "low": json.dumps(df['low'].tolist()), #pd.Series(df['low']).to_json(orient='values'),
            "high": json.dumps(df['high'].tolist()), #pd.Series(df['high']).to_json(orient='values'),
            "open": json.dumps(df['open'].tolist()), #pd.Series(df['open']).to_json(orient='values'),
            "close": json.dumps(df['close'].tolist()), #pd.Series(df['close']).to_json(orient='values'),
            
            
            # redact signals by removing zeroes to allow scatter plotting
            "buy_signal": json.dumps(cleared_buy_signal.tolist()), #cleared_buy_signal.to_json(orient='values'),
            "buy_signal_date": json.dumps(cleared_buy_signal_dates.tolist()), #cleared_buy_signal_dates.to_json(orient='values'),
            "sell_signal": json.dumps(cleared_sell_signal.tolist()), #cleared_sell_signal.to_json(orient='values'),
            "sell_signal_date": json.dumps(cleared_sell_signal_dates.tolist()), #cleared_sell_signal_dates.to_json(orient='values'),
            
            "df_compose_time": self.exchange_client.get_df_compose_time(),
            "klines_exec_time": self.exchange_client.get_klines_exec_time(),
            "klines_size": len(df.index),
            "klines_call_count": self.exchange_client.get_call_count(),
            "state": self.state,
            
            "DIRECTION:": self.exchange_client.get_direction(),
            #"PROFIT": profit,
            "CYCLE_PROFIT": last_profit,
            "AVG_TRADE_DURATION": avg_trade_duration,
            "AVG_GAIN": avg_gain,
            "CYCLE_COUNT": cycle_count,
            "CYCLE_DURATION": cycle_duration,
            "TOTAL_CYCLE_TIME": total_cycle_time,
            
            "AVG_ENTRY_PRICE": self.exchange_client.get_average_purchase_price(),
            "DF_FILE_NAME": self.exchange_client.get_static_df_file_name(),
            "UTX_TIME_BOUNDARY": self.exchange_client.get_dfs_time_boundary_utx(),
            "STR_TIME_BOUNDARY": self.exchange_client.get_dfs_timeboundary_str(),
            
            "TARGET_ENTRY_PRICE": target_entry_price,
            
            "TARGET_UNITS_BOUGHT": self.exchange_client.get_target_units_bought(),
            "AVG_UNITS_BOUGHT": self.exchange_client.get_avg_units_bought(),
            "TARGET_UNITS_SOLD": self.exchange_client.get_target_units_sold(),
            
            "EXIT_PRICE": exit_price,
            "AVG_EXIT_PRICE": self.exchange_client.get_avg_exit_price(),
            
            "RANGE_SCORE": self.exchange_client.get_range_score(),
            "ERROR": self.exchange_client.get_error(),
            
            "BUY_FEE": self.exchange_client.get_buy_fee(),
            "SELL_FEE": self.exchange_client.get_sell_fee(),
            
            "BUY_FEE_CURRENCY": self.exchange_client.get_buy_fee_currency(),
            "SELL_FEE_CURRENCY": self.exchange_client.get_sell_fee_currency(),
             
        }
        
        if self.message_queue != None and self.signal_queue != None:
            #logger.error(" the following message is delivered by the engine, %s", json.dumps(msg)); 
            self.queue_message(msg, self.RUNNING)
            
        del df
        del msg
        gc.collect()
        
                
    #@profile 
    def queue_message(self, message, signal):
        """
        queue a message
        """
        logger.info(" queueing a message in engine ")
        try:
            for m in self.message_queue:
                self.message_queue.pop()
                del m
        except:
            pass
                
        try:
            for m in self.signal_queue:
                self.signal_queue.pop()
                del m
        except:
            pass
                
        self.message_queue.append(message)
        self.signal_queue.append(signal)
        
        logger.info(" message queue size " + str(len(self.message_queue)))
        logger.info(" signal queue size " + str(len(self.signal_queue)))
            
    #@profile 
    def get_state(self):
        """
        return state
        """
        return self.state
            
    #@profile 
    def start_was_called(self):
        """
        start engine
        """
        self.stop_called = False
        logger.info("ENGINE START WAS CALLED")
        
    #@profile  
    def stop_was_called(self):
        """
        stop engine
        """
        logger.info(" stopping engine and sending an OFF signal to transmission")
        self.stop_called = True
        self.queue_message("OFF", self.OFF)
        logger.info("ENGINE STOP WAS CALLED")
                
    #@profile 
    def set_state(self, state):
        """
        set the state
        """
        logger.info("starting the engine")
        self.state = state
        
    #@profile 
    def reset_client(self):
        """
        reset the client
        """
        logger.info("resetting the client from the engine")
        self.exchange_client.set_data_frame(None)
        