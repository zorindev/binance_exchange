import os
import sys
import glob
import math
from datetime import datetime, timedelta
import time
from datetime import timezone
from core.client_interface import ExchangeClientInterface
from interface import implements
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import pandas as pd
import numpy as np
from pandas_datareader import data
from pprint import pformat
from pip._internal.commands.search import highest_version
from decimal import Decimal
#from pandas.tests.io.test_parquet import df_compat
import traceback
import socket
import urllib3
#import urllib3.exceptions.ReadTimeoutError
from urllib3.exceptions import ReadTimeoutError
from urllib3.exceptions import ProtocolError
from jedi.debug import increase_indent
from pprint import pprint
from email.policy import default
import logging
import traceback
import pandas_ta as ta
from tinydb import TinyDB, Query
from _symtable import FREE


logger = logging.getLogger("ex_logger")

#import requests
#import requests.exceptions.RequestException


class binance_client(implements(ExchangeClientInterface)):
    
    # sleep period
    SLEEP_PERIOD_FOR_ORDER_HANDLING = 2
        
    # date format
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # default signal boundary
    LIMIT_THRESHOLD = 0.05
    
    # stoch rsi lower
    STOCH_LOW_BNDR = 20
    
    # stoch rsi upper
    STOCH_HIGH_BNDR = 80
    
    DEFAULT_MAX_LEVEL = 5
        
    # simple direction
    UP = "up"
    DOWN = "down"
    
    # DF types
    KLINES_ORIGINAL = "original"
    KLINES_RECALCULATED = "recalculated"
    DEPTH_BIDS = "bids_df"
    DEPTH_ASKS = "asks_df"
    
    INSUFFICIENT = "insufficient"
    
    DB_NAME = "db.json"

    #@profile 
    def __init__(self, 
                 
            # api
            api_key, 
            api_secret,
        
            # market 
            exchange_client_name = None,
            market_code = None,
            starting_amount = 0.00,
        
            # bollinger  
            number_of_periods = 500, 
            period_type = "1m", 
            boll_rolling_window = 21,
            signal_thresh = 0.0,
        
            # rsi
            rsi_period = 14,
            stoch_period = 14,
            smooth_k = 3,
            smooth_d = 3,
            rsi_entry_limit = 0.2,
            rsi_exit_limit = 0.8,
        
             # sma
             ctrl_sma_limit = 99,
        
            # control
            enable_live_data = False,
            enable_transactions = False,
            enable_bollinger_signal_eval = False,
            enable_stoch_rsi_signal_eval = False,
            enable_sma_signal_eval = False,
            static_df_period = "",
            
        ):
        """
        init
        """
        
        logger.info("INSATNTIATING BINANCE CLIENT")
        
        # exchange client
        self.client = None
        
        # exchange info
        self.exchange_info = None
        
        # pairs positions dict
        self.pairs_positions_dict = {}
    
        # holds the exchange response
        self.ticker = None
        
        # the dataframe
        self.df = None
        
        # state    
        self.state = 0
    
        self.historic_buy_signals = {}
        self.historic_sell_signals = {}
        self.historic_buy_signal_dates = {}
        self.historic_sell_signal_dates = {}
            
        # stats
        self.klines_exec_time = 0.00
        self.df_compose_time = 0.00
        self.call_count = 0
        
        self.simple_direction = ""
    
        # price that the asset was last purchased for
        self.entry_price = 0.00
        self.avg_entry_price = 0.00
        
        self.exit_price = 0.00
        self.avg_exit_price = 0.00
        
        self.fee_coef = 0.00075
        
        self.cycle_count = 0
        
        self.sales_count = 0
        
        self.cycle_duration = 0
        
        self.starting_amount = 0.0000
        
        self.trading_amount = 0.0000
        
        self.max_trading_amount = 200.0
        
        # how much was spent on a purchase
        self.amount_spent = 0.0000        
        
        self.total_profit = 0.0000
        
        self.cycle_profit = 0.0000
        
        self.target_units_bought = 0.0000
        
        self.position_open_date = None
        
        self.average_cycle_time = 0.00
        
        self.total_cycle_time = 0.00
        
        self.average_gain = 0.00
        
        self.average_trade_cycle_duration = 0

        # holds name of the dataframe for reporting
        self.next_df_filename = ""
    
        # holds timestamp boundary
        self.utx_time_boundary = ""
    
        # holds string time boundary
        self.str_time_boundary = ""
    
        self.enable_live_data = enable_live_data
        
        self.buy_order = {}
        
        self.sell_order = {}
        
        self.account = {}
        
        self.buy_fee = 0.00
        
        self.sell_fee = 0.00
        
        self.buy_fee_currency = ""
        
        self.sell_fee_currency = ""
        
        try:
            self.client = Client(api_key, api_secret)
        except:
            logger.info("client could not connect")
            if(self.enable_live_data):
                raise Exception("Unable to connet to the API. exiting ")
            
        np.set_printoptions(suppress=True)
        
        self.number_of_periods = number_of_periods * 1
        self.boll_rolling_window = boll_rolling_window * 1
        self.period = period_type
        
        # set threshold
        self.limit_threshhold = self.LIMIT_THRESHOLD
        if(signal_thresh != None):
            self.limit_threshhold = signal_thresh

        self.str_symbol = market_code
        
        self.symbol_info = None
    
        self.starting_amount = float(starting_amount * 1)
        
        self.trading_amount = float(starting_amount * 1)
        
        self.total_profit = 0.00

        
        self.target_units_bought = 0.00
        
        self.enable_live_data = enable_live_data
        
        self.enable_transactions = enable_transactions
        
        self.enable_bollinger_signal_eval = enable_bollinger_signal_eval
        
        self.enable_stoch_rsi_signal_eval = enable_stoch_rsi_signal_eval
        
        self.enable_sma_signal_eval = enable_sma_signal_eval
            
        self.target_units_bought = 0.0000
        self.avg_target_units_bought = 0.0000
        
        self.target_units_sold = 0.0000
        self.avg_target_units_sold = 0.0000
        
        self.avg_units_sold = 0.0000
        
        self.price_spread_mean = 0.0000
        
        
        # stock rsi settings 
        self.stoch_period = int(stoch_period)
        self.rsi_period = int(rsi_period)
        self.smooth_k_period = int(smooth_k)
        self.smooth_d_period = int(smooth_d)
        self.rsi_entry_limit = float(rsi_entry_limit)
        self.rsi_exit_limit = float(rsi_exit_limit) 
        
        self.RSI = None
        
        # market depth
        self.bids_total = 0.00
        self.bids_avg_price = 0.00
        self.asks_total = 0.00
        self.asks_avg_price = 0.00
        
        # static frame loading from csv
        self.static_df_files = []
        self.static_df_index = 0
        
        self.static_depth_bid_files = []
        self.static_depth_bid_index = 0
        
        self.static_depth_ask_files = []
        self.static_depth_ask_index = 0
        
        self.df_logging_timestamp = ""
        
        self.db = TinyDB(self.DB_NAME)
        
        self.delta_sma7_sum = 0.00
        self.delta_sma25_sum = 0.00
        self.delta_smactrl_sum = 0.00
        self.delta_emactrl_sum = 0.00
        self.delta_sma_back_ctrl_sum = 0.00
        
        self.sma_limit_7 = 7
        self.sma_limit_25 = 25
        self.ctrl_sma_limit = int(ctrl_sma_limit)
        
        self.static_df_period = static_df_period
        
        self.step_size = 0
        self.precision = 8
        
        self.tick_size = 0
        self.tick_precision = 0
        
        self.error = ""
        
        self.trading_range = None
        self.range_score = 0.00
        
        
        self.availBNB = 0.00
        
        self.fee_amount = 0.00
        
        self.base_asset = None
        
        self.quote_asset = None
        
        
        self.server_time = None
        
        
        self.bollinger_had_entry = False
        self.bollinger_had_entry = False
        
        self.rsi_had_entry = False
        self.rsi_had_exit = False
        
        self.candle_boundary = None
        
        
        self.enable_ema4_eval = True
        
        self.init_total_cycle_time = None
        
        
        self.insufficient_funds_condition = False
        
        
        self.entered_with_bollinger = -1
        
        
        self.ema_direction = -1
        
        
        self.ema_8_direction = -1
        
        
        self.ema_13_direction = -1
        
        
        self.ema_spread_direction = -1
        
        
        
       
        
        logger.info("DONE INSATNTIATING BINANCE CLIENT")
        
        
        
    
    #@profile 
    def _get_str_time(self, timestamp):
        """
        get time str
        """
        rtn = ""
        try:
            ts = int(int(timestamp)/1000)
            rtn = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        
        return rtn
    
    #@profile 
    def _get_timestamp_from_str(self, str_date_time, frmt):
        """
        returns timestanp from input str
        """
        
        timestamp = 0  
        try:  
            dt = datetime.strptime(str_date_time, frmt)
            timestamp = dt.replace(tzinfo=timezone.utc).timestamp()
        
        except Exception as e:
            logger.error(e)
        
        return timestamp
        
    
    
    
        
    #@profile 
    def calc_roc(self, attr, orig_num, new_num):
        """
        sets the rate of change returs equasion ready percetage
        """
        roc = (float(orig_num) - float(new_num)) / float(orig_num)
        #if(orig_num > new_num):
        roc *= -1
        #roc = (float(orig_num) - float(new_num)) / float(orig_num)
        #if(orig_num > new_num):
        #    roc = (float(new_num) - float(orig_num)) / float(new_num)
        setattr(self, attr, roc)
        
    
        
    #@profile             
    def ping(self):
        """
        get server time as a connection test
        """
        return self.client.get_server_time()
        
    #@profile 
    def get_server_time(self):
        """
        gets server time
        """
        server_time = int(time.time())
        if(self.enable_live_data):
            server_time = self.client.get_server_time()
            server_time['str_server_time'] = self._get_str_time(server_time['serverTime'])    
        return server_time 
    
    #@profile 
    def _reset_ticker(self):
        """
        reset
        """
        self.ticker = {
            "open_time": None,
            "open_time_str": None,
            "open_price": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
            "close_time": None,
            "close_time_str": None,
            "quote_asset_volume": None,
            "number_of_trades": None
        }
    
    #@profile 
    def get_current_price(self, str_symbol, str_period, int_number_of_records):
        """
        get current price
        """    
        self._reset_ticker()
        logger.info("getting current price for %s ", str_symbol)
        
        if(self.currennt_kline):
            self.one_kline = self.client.get_klines(
                symbol = str_symbol,
                interval = str_period,
                limit = int_number_of_records
            )
        
        if len(self.currennt_kline) > 0:
            self.ticker['open_time'] =          self.one_kline[len(self.one_kline) - 1][0]
            self.ticker['open_time_str'] =      self._get_str_time(self.one_kline[len(self.one_kline) - 1][0])
            self.ticker['open_price'] =         self.one_kline[len(self.one_kline) - 1][1]
            self.ticker['high'] =               self.one_kline[len(self.one_kline) - 1][2]
            self.ticker['low'] =                self.one_kline[len(self.one_kline) - 1][3]
            self.ticker['close'] =              self.one_kline[len(self.one_kline) - 1][4]
            self.ticker['volume'] =             self.one_kline[len(self.one_kline) - 1][5]
            self.ticker['close_time'] =         self.one_kline[len(self.one_kline) - 1][6]
            self.ticker['close_time_str'] =     self._get_str_time(self.one_kline[len(self.one_kline) - 1][6])
            self.ticker['quote_asset_volume'] = self.one_kline[len(self.one_kline) - 1][7]
            self.ticker['number_of_trades'] =   self.one_kline[len(self.one_kline) - 1][8]
            
        logger.info("done\n")
        return self.ticker
    
    #@profile 
    def __get_start_time(self, sma_size, period):
        """
        returns unix timestamp of right now minus sma_size days ago
        """
        period_size = int((period[:-1]))
        period_type = period[-1:]
        
        if(period_type == "d"):
            try:
                d = datetime.today() - timedelta(days=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            except Exception as e:                
                d = datetime.today() - timedelta(days=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").timetuple()))
        elif(period_type == "m"):
            try:
                d = datetime.today() - timedelta(minutes=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            except Exception as e:
                d = datetime.today() - timedelta(minutes=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").timetuple()))
        elif(period_type == "h"):
            try:
                d = datetime.today() - timedelta(hours=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            except Exception as e:
                d = datetime.today() - timedelta(hours=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").timetuple()))
        elif(period_type == "w"):
            try:
                d = datetime.today() - timedelta(weeks=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            except Exception as e:
                d = datetime.today() - timedelta(weeks=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").timetuple()))
        elif(period_type == "M"):
            try:
                d = datetime.today() - timedelta(months=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            except Exception as e:
                d = datetime.today() - timedelta(months=(sma_size * period_size))
                return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").timetuple()))
        else:
            return None
        
    #@profile 
    def calculate_bollinger(self, df = None, col_str_src = "", col_sfx = ""):
        """
        calculates bollinger
        """
        if(col_str_src != ""):
            if(col_str_src in df):
                
                
                
                df[col_str_src] = pd.to_numeric(df[col_str_src]).fillna(0)
                t = {"col": df[col_str_src]}
                tdf = pd.DataFrame(data = t)
                mean = tdf["col"].rolling(self.boll_rolling_window).mean()
                std = tdf["col"].rolling(self.boll_rolling_window).std()     
                high_key = col_sfx + '_high_' + col_str_src
                low_key = col_sfx + '_low_' + col_str_src
                mid_key = col_sfx + '_middle_' + col_str_src
                
                df[high_key] = pd.to_numeric((mean + (std * 2))).fillna(0).round(4)
                df[low_key] = pd.to_numeric((mean - (std * 2))).fillna(0).round(4)
                df[mid_key] = pd.to_numeric((mean)).fillna(0).round(4)
                
        return df
    
    
    def calculate_bollinger_ta(self, df = None, col_str_src = "", col_sfx = "", ma_mode = "", period = 20):
        """
        ta lib impl of bollinger bands
        """
        
        t = {col_str_src: round(df[col_str_src], 4)}
        tdf = pd.DataFrame(data = t)
        
        bbands_ta = ta.bbands(close = tdf[col_str_src], length = period, std = 2, mamode = ma_mode, offset = 0)
        
        high_key = col_sfx + '_high_' + col_str_src + '_' + ma_mode + '_' + str(period)
        low_key = col_sfx + '_low_' + col_str_src + '_' + ma_mode + '_' + str(period)
        mid_key = col_sfx + '_middle_' + col_str_src + '_' + ma_mode + '_' + str(period)
              
        df[high_key] = bbands_ta['BBU_' + str(period) + '_2.0']
        df[low_key] = bbands_ta['BBL_' + str(period) + '_2.0']
        df[mid_key] = bbands_ta['BBM_' + str(period) + '_2.0']
        
        return df
        
        
    
    #@profile 
    def calculate_price_spread(self, df, lower_col_name = "", upper_col_name = "", new_col = ""):
        """
        calculate the spread of the bollinger values and register them in a *_spread columns
        """
        logger.info("calculating price spread: lower_col = %s %s %s %s %s", lower_col_name, "; upper_col = ", upper_col_name, "; new_col = ", new_col)
        if(lower_col_name != "" and upper_col_name != ""):
            if(lower_col_name in df and upper_col_name in df):
                if(new_col != ""):
                    df[new_col] = df[upper_col_name] - df[lower_col_name]
        return df
    
    #@profile 
    def reset_historic_signals(self):
        """
        resets historic signals
        """    
        logger.info(" resetting historic signals ")
        #self.historic_buy_signals = {}
        #self.historic_sell_signals = {}
        #self.historic_buy_signal_dates = {}
        #self.historic_sell_signal_dates = {}
        pass
    
    #@profile 
    def log_data_frame(self, df, df_type = KLINES_ORIGINAL, exec_start = None):
        """
        log data frame
        """
        if(os.name == "nt"): 
            
            x = datetime.today().strftime('%Y/%m/%d')
            
            if(df_type == self.KLINES_ORIGINAL):
                self.df_logging_timestamp = str(datetime.now()).replace(" ", "_").replace(":", ".")
                
            if(self.df_logging_timestamp != ""):
                
                file_path_to_df = "./zdfs/" + str(datetime.today().strftime('%Y/%m/%d')) + "/"
                file_path_to_df_parts = file_path_to_df.split("/")
                
                file_path_to_df_asm = ""
                for part in file_path_to_df_parts:
                    
                    file_path_to_df_asm += part + "/"
                    
                    if(not os.path.exists(file_path_to_df_asm)):
                        os.mkdir(file_path_to_df_asm)
                    
                logged_df_filename = file_path_to_df + df_type + "_df_" + self.period + "_" + self.df_logging_timestamp + ".csv"
                logger.info(" logging df into a file: %s ", logged_df_filename)
                df.to_csv(logged_df_filename)
            
    #@profile 
    def get_live_dataframe(self, start_time, exec_start):
        """
        call klines and load dataframe
        """    
        logger.info(" getting a live df .... ")
        self.history_klines = self.client.get_klines(
            symbol = self.str_symbol,
            interval = self.period
            #,
            #startTime = start_time
        )
        exec_end = time.time()        
        self.klines_exec_time = (exec_end - exec_start)
        
        logger.info("obtained live df")
        
        # set current kline
        exec_start = time.time()
        self.currennt_kline = self.history_klines[len(self.history_klines) - 1]
        exec_end = time.time()
        self.current_kline_creation_time = (exec_end - exec_start)
        
        # create data frame
        labels = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', '1', '2', '3', '4', '5']
        df = pd.DataFrame(self.history_klines, columns=labels)
        self.log_data_frame(df, self.KLINES_ORIGINAL, exec_start)
        self.static_df_index += 1
        
        logger.info("done obtaiing live df")
        return df
    
    
    #@profile 
    def get_live_market_depth(self, df):
        """
        market depth
        """
        
        if(self.call_count == 1):
            historical_trades = self.client.get_historical_trades(symbol = self.str_symbol, limit = 1000)
            
            bids_map = {}
            asks_map = {}
            for trade in historical_trades:
            
                timestamp_key = int(str(trade['time'])[0:-3])    
                if(trade["isBuyerMaker"]):
                    if(timestamp_key in bids_map):
                        bids_map_entry = bids_map[timestamp_key]
                        bids_map_entry['price'] += float(trade['price'])
                        bids_map_entry['qty'] += float(trade['qty'])
                        bids_map[timestamp_key] = bids_map_entry
                        
                    else:
                        bids_map_entry = {}
                        bids_map_entry['price'] = float(trade['price'])
                        bids_map_entry['qty'] = float(trade['qty'])
                        bids_map[timestamp_key] = bids_map_entry
                        
                else:
                    if(timestamp_key in asks_map):
                        asks_map_entry = asks_map[timestamp_key]
                        asks_map_entry['price'] += float(trade['price'])
                        asks_map_entry['qty'] += float(trade['qty'])
                        asks_map[timestamp_key] = asks_map_entry
                        
                    else:
                        asks_map_entry = {}
                        asks_map_entry['price'] = float(trade['price'])
                        asks_map_entry['qty'] = float(trade['qty'])
                        asks_map[timestamp_key] = asks_map_entry
                       
            for key, bids_entry in bids_map.items():
                
                if(key in asks_map):
                    asks_entry = asks_map[key]
                    self.db.insert({
                        "depth_timestamp": key,
                        "bids_total": bids_entry['qty'],
                        "bids_avg_price": bids_entry['price'],
                        "asks_total": asks_entry['qty'],
                        "asks_avg_price": asks_entry['price'] 
                    })
                
            
        time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
        
        # get depth
        market_depth = self.client.get_order_book(symbol = self.str_symbol)
        bids_df = pd.DataFrame(market_depth['bids'], columns = ['price', 'amount'])
        asks_df = pd.DataFrame(market_depth['asks'], columns = ['price', 'amount'])
        
        # summarise depth
        bids_df['price'] = pd.to_numeric(bids_df['price'])
        bids_df['amount'] = pd.to_numeric(bids_df['amount'])
        
        asks_df['price'] = pd.to_numeric(asks_df['price'])
        asks_df['amount'] = pd.to_numeric(asks_df['amount'])
        
        self.bids_total = bids_df['amount'].sum()
        self.bids_avg_price = bids_df['price'].mean()
        
        self.asks_total = asks_df['amount'].sum()
        self.asks_avg_price = asks_df['price'].mean()
                
        #self.log_data_frame(bids_df, self.DEPTH_BIDS, None)
        #self.log_data_frame(asks_df, self.DEPTH_ASKS, None)
        #logger.info(" persisted df ")
        
        # get last row of df to capture the index timestamp
        
        try:
            v1 = df.iloc[-1:]['open_time'].values[-1:][0]
            v2 = v1[0:-3]
            v3 = str(v1[0:-3])
        except Exception as e:
            traceback.print_exc()
        
        str_timestamp_value = str(df.iloc[-1:]['open_time'].values[-1:][0])[0:-3]
        int_timestamp_value = int(str_timestamp_value)
        #timestamp_value2 = df.at[-1:, 'open_time']
        #timestamp_value3 = df.loc[-1:, 'open_time']
        
        # write the timestamp and summary to db to later fetch on the main iter loop
        self.db.insert({
            "depth_timestamp": int_timestamp_value,
            "bids_total": self.bids_total,
            "bids_avg_price": self.bids_avg_price,
            "asks_total": self.asks_total,
            "asks_avg_price": self.asks_avg_price, 
        })
                
        #depth_data = Query()
        #db_result = self.db.search(depth_data.depth_timestamp == timestamp_value)
        #print(db_result)
        #print(" end ")
        
        
    #@profile 
    def load_static_df_filenames(self, static_df_list_name = "", static_df_index_name = "", df_type = "", specific_date = "*"):
        """
        load static df filenames 
        """
        
        #if(self.static_df_index == 0):
        #    logger.info(" loading static df file names, self.static_df_index = %s ", str(self.static_df_index))
        #    self.static_df_files = glob.glob("./zdfs/" + df_type + "_df_*.csv")
        #    self.static_df_files.sort()
        
        
        x = datetime.today().strftime('%Y/%m/%d/%H')
        
        static_df_index = getattr(self, static_df_index_name)
        static_df_list = getattr(self, static_df_list_name)
        
        if(static_df_index != None and static_df_list != None):
            if(static_df_index == 0):
                logger.info(" loading static df file names, self.static_df_index = %s ", str(self.static_df_index))
                static_df_list = glob.glob("./zdfs/" + specific_date + "/" + df_type + "_df_*.csv")
                static_df_list.sort()
                
        setattr(self, static_df_index_name, static_df_index)
        setattr(self, static_df_list_name, static_df_list)
                
    #@profile 
    def load_next_static_dataframe(self):
        """
        load next df from dir
        """
        logger.info(" loading next static df ... ")
        self.load_static_df_filenames(
            static_df_list_name = "static_df_files",
            static_df_index_name = "static_df_index", 
            df_type = self.KLINES_ORIGINAL,
            specific_date = self.static_df_period
        )
        
        self.df_logging_timestamp = ""
        if(self.static_df_index <= len(self.static_df_files) - 1):            
            next_df_filename = self.static_df_files[self.static_df_index]
            
            self.df_logging_timestamp = "_".join(next_df_filename.split("_")[3:5]).replace(".csv", "")
            
            logger.info(" loading static df with index %s %s ", str(self.static_df_index), str(next_df_filename))
            self.next_df_filename = next_df_filename
            self.static_df_index += 1
            df = pd.read_csv(next_df_filename)
            
            return df
        
        else:
            logger.info(" could not load the next static df and returning an empty df ")
            return pd.DataFrame()
        
    #@profile 
    def load_next_static_depth(self):
        """
        load next static bid ask  
        """ 
        
        logger.info(" loading next static depth bids ")
        self.load_static_df_filenames(
            static_df_list_name = "static_depth_bid_files",
            static_df_index_name = "static_depth_bid_index", 
            df_type = self.DEPTH_BIDS
        )
        
        logger.info(" loading next static depth asks ")
        self.load_static_df_filenames(
            static_df_list_name = "static_depth_ask_files",
            static_df_index_name = "static_depth_ask_index", 
            df_type = self.DEPTH_ASKS
        )
        
        if(self.df_logging_timestamp != ""):
            for next_depth_file_name in self.static_depth_bid_files:
                if("_".join(next_depth_file_name.split("_")[3:5]) == self.df_logging_timestamp):
                    ddf = pd.read_csv(next_depth_file_name) 
                    
                    ddf['price'] = pd.to_numeric(ddf['price'])
                    ddf['amount'] = pd.to_numeric(ddf['amount'])
                    
                    self.bids_total = ddf['amount'].sum()
                    self.bids_avg_price = ddf['price'].mean()
                    
                    break
                
                
        if(self.df_logging_timestamp != ""):
            for next_depth_file_name in self.static_depth_bid_files:
                if("_".join(next_depth_file_name.split("_")[3:5]) == self.df_logging_timestamp):
                    ddf = pd.read_csv(next_depth_file_name) 
                    
                    ddf['price'] = pd.to_numeric(ddf['price'])
                    ddf['amount'] = pd.to_numeric(ddf['amount'])
                    
                    self.asks_total = ddf['amount'].sum()
                    self.asks_avg_price = ddf['price'].mean()
                    
                    break
         
    
        
    #@profile 
    def calculate_rsi(self, df, col = 'close', rsi_col_name = 'RSI'):
        """
        calculates RSI
        """    
        delta = df[col].diff().dropna()
        ups = delta * 0
        downs = ups.copy()
        ups[delta > 0] = delta[delta > 0]
        downs[delta < 0] = -delta[delta < 0]
        ups[ups.index[self.rsi_period - 1]] = np.mean(ups[:self.rsi_period])
        ups = ups.drop(ups.index[:(self.rsi_period - 1)])
        downs[downs.index[self.rsi_period - 1]] = np.mean(downs[:self.rsi_period]) #first value is sum of avg losses
        downs = downs.drop(downs.index[:(self.rsi_period - 1)])
        
        self.RS = ups.ewm(
            com = self.rsi_period - 1,
            min_periods = 0,
            adjust = False,
            ignore_na = False
        ).mean() / downs.ewm(
            com = self.rsi_period - 1,
            min_periods = 0,
            adjust = False,
            ignore_na = False
        ).mean()
        
        self.RSI = 100 - (100 / (1 + self.RS))

        df[rsi_col_name] = self.RSI
          
    #@profile   
    def calculate_stochastic_occ(self, df, src_col = '', stoch_name_col = ''):
        """
        stochastic
        """
        logger.info("calculate stochastic rsi ... ")
        
        if(src_col != "" and stoch_name_col != ""):
            interim_col = "STOCH_" + stoch_name_col
            df[interim_col]  = (df[src_col] - df[src_col].rolling(self.stochastic_period).min()) / (df[src_col].rolling(self.stochastic_period).max() - df[src_col].rolling(self.stochastic_period).min())

            k_col = interim_col + "_K"
            df[k_col] = df[interim_col].rolling(self.stoch_k_period).mean()
            
            d_col = interim_col + "_D"
            df[d_col] = df[k_col].rolling(self.stoch_d_period).mean()
            
            
    #@profile 
    def StochRSI(self, df, src_col = "close", d_col = "", k_col = "", rsi_period = 14, stoch_period = 14, smoothK = 3, smoothD = 3):
        """
        Stoch RSI
        """ 
        
        delta = df[src_col].diff().dropna()
        ups = delta * 0
        downs = ups.copy()
        ups[delta > 0] = delta[delta > 0]
        downs[delta < 0] = -delta[delta < 0]
        ups[ups.index[rsi_period - 1]] = np.mean(ups[:rsi_period]) #first value is sum of avg gains
        ups = ups.drop(ups.index[:(rsi_period - 1)])
        downs[downs.index[rsi_period - 1]] = np.mean( downs[:rsi_period] ) #first value is sum of avg losses
        downs = downs.drop(downs.index[:(rsi_period - 1)])
        
        ups_ewm = ups.ewm(
            com = rsi_period - 1,
            min_periods = 0,
            adjust = False,
            ignore_na =False).mean()
            
        downs_ewm = downs.ewm(
            com = rsi_period - 1, 
            min_periods = 0, 
            adjust = False, 
            ignore_na = False).mean()
             
        rs = ups_ewm / downs_ewm
          
        rsi = 100 - 100 / (1 + rs)
        
        stochrsi  = (rsi - rsi.rolling(stoch_period).min()) / (rsi.rolling(stoch_period).max() - rsi.rolling(stoch_period).min())
        df[k_col] = stochrsi.rolling(smoothK).mean()
        df[d_col] = df[k_col].rolling(smoothD).mean()

        return df

            
    #@profile         
    def calculate_supertrend(self, df, period = 14, factor = 3):
        """
        ta based supertrend
        """
        supertrend_df = ta.supertrend(
            high = df['high'], 
            low = df['low'], 
            close = df['close'], 
            length = period, 
            multiplier = factor
        )
       
        col_name_tr = ['supertrend', 'supertrend_direction', 'supertrend_l', 'supertrend_s']
        i = 0
        for col_name in supertrend_df.columns:
            df[col_name_tr[i]] = supertrend_df[col_name]
            i += 1
            
        df['supertrend_up_values'] = np.nan
        df['supertrend_down_values'] = np.nan
        df['supertrend_up_values'] = df[df['supertrend_direction'] > 0]['supertrend']
        df['supertrend_down_values'] = df[df['supertrend_direction'] < 0]['supertrend'] 
            
        return df
    
    
    #@profile 
    def eval_row_for_bollinger(self, row, thresh, sma_eval):
        """
        evals a row for bollinger signal
        """
        
        rtn = False
        
        if(self.enable_bollinger_signal_eval):
            
            if(self.state == 0):
                
                logger.info(" evalling bollinger at state 0 ") 
                     
                
                if(self.limit_threshhold > 0.0):
                    left = thresh
                    right = self.limit_threshhold
                else:
                    left = round(row['low'], self.tick_precision)
                    right = round(row['boll_low_close'], self.tick_precision)
            
                #if(round(row['low'], self.tick_precision) <= round(row['boll_low_close'], self.tick_precision) and round(row['close'], self.tick_precision) >= round(row['open'], self.tick_precision)):
                #if((row['low'] <= row['boll_low_close']) & (row['close'] > row['open'])):
                if((left <= right) & (row['close'] > row['open'])):
                    rtn = True
                    
                    logger.info("evalled bollinger to true as low(" + str(row['low']) + ") <= boll_low_close(" + str(row['boll_low_close']) + ") and close(" + str(row['close'])+ ") > open(" + str(row['open']) + ")")
                    
                else:
                    logger.info(" evalled bollinger to false as low(" + str(row['low']) + ") > boll_low_close(" + str(row['boll_low_close']) + ") or close(" + str(row['close'])+ ") < open(" + str(row['open']) + ")")
                    
            elif(self.state == 2):
                
                logger.info(" evalling bollinger at state 2 ")
                
                                
                sell_thresh = 0.0 
                
                if(self.limit_threshhold > 0.0):
                    
                    if(sma_eval):      
                        sell_thresh = (((round(row['high'], self.tick_precision) - round(row['boll_high_close'], self.tick_precision)) / round(row['high'], self.tick_precision)) * 100)
                    else:
                        sell_thresh = (((round(row['high'], self.tick_precision) - round(row['boll_middle_close'], self.tick_precision)) / round(row['high'], self.tick_precision)) * 100)
                        
                    left = sell_thresh
                    right = self.limit_threshhold
                    
                else:
                    
                    left = round(row['high'], self.tick_precision)
                    if(sma_eval):
                        right = round(row['boll_high_close'], self.tick_precision)
                    else:
                        right = round(row['boll_middle_close'], self.tick_precision)
                
                
                    
                    logger.info(" in bollinger eval state 2 sma was true ... ")
                    if(left >= right):
                        
                        rtn = True
                        
                        logger.info(" in bollinger eval state 2 evalled to True as " + str(left) + " >= " + str(right))
                    
                    else:
                        logger.info(" in bollinger eval state 2 evalled to False as " + str(left) + " < " + str(right))
                        
                
                    
                    logger.info(" in bollinger eval state 2 with sma false ... ")
                    if(left > right):
                        
                        rtn = True
                        
                        logger.info(" in bollinger eval state 2 evalled to True as " + str(row['high']) + " >= " + str(row['boll_middle_close']))
                        
                    else:       
                        logger.info(" in bollinger eval state 2 evalled to False as " + str(row['high']) + " < " + str(row['boll_middle_close']))
                        
                        
                        
            
            """
            if((left <= right) & (row['close'] > row['open'])):
                self.bollinger_had_entry = True
                
            elif(row['high'] > row['boll_high_close']):
                self.bollinger_had_entry = False
            """
                
            
        else:
            
            self.bollinger_had_entry = True
            rtn = True
            
        
        return rtn
    
    #@profile 
    def eval_row_for_stoch_rsi(self, row):
        """
        evals row for stoch rsi
        """
        
        rtn = False
        
        if(self.enable_stoch_rsi_signal_eval):
            
            if(self.state == 0):
                
                logger.info("evalling stoch rsi for state 0 ... ")
                if(row['stoch_rsi_k'] <= self.rsi_entry_limit and row['stoch_rsi_k'] > row['stoch_rsi_d']):
                    rtn = True
                    logger.info(" evalled stoch rsi for entry to " + str(rtn) + " as " + str(row['stoch_rsi_k']) + " <= " + str(self.rsi_entry_limit) + " and " + str(row['stoch_rsi_k']) + " > " + str(row['stoch_rsi_d']))
                else:
                    logger.info(" evalled stoch rsi for entry to " + str(rtn) + " as " + str(row['stoch_rsi_k']) + " > " + str(self.rsi_entry_limit) + " or " + str(row['stoch_rsi_k']) + " < " + str(row['stoch_rsi_d']))
                
            elif(self.state == 2):
                
                logger.info("evalling stoch rsi for state 2 ... ")
                if(row['stoch_rsi_k'] >= self.rsi_exit_limit and row['stoch_rsi_k'] < row['stoch_rsi_d']):
                    rtn = True
                    logger.info(" evalled stoch rsi for exit to " + str(rtn) + " as " + str(row['stoch_rsi_k']) + " >= " + str(self.rsi_exit_limit) + " and " + str(row['stoch_rsi_k']) + " > " + str(row['stoch_rsi_d']))
                else:
                    logger.info(" evalled stoch rsi for exit to " + str(rtn) + " as " + str(row['stoch_rsi_k']) + " < " + str(self.rsi_exit_limit) + " or " + str(row['stoch_rsi_k']) + " <= " + str(row['stoch_rsi_d']))
                    
            
            
            
            if(row['stoch_rsi_k'] <= self.rsi_entry_limit and row['stoch_rsi_k'] > row['stoch_rsi_d']):
                self.rsi_had_entry = True
                
            elif(row['stoch_rsi_k'] >= self.rsi_exit_limit and row['stoch_rsi_k'] < row['stoch_rsi_d']):
                self.rsi_had_entry = False
                
        else:
            
            self.rsi_had_entry = True
            rtn = True
                    
        return rtn
    
    #@profile 
    def eval_row_for_sma(self, row, i):
        """
        evals signals for SMA: if boll flag is true then ensure that given smacrl delta sum is positive
        if boll flag is false then ensure that sma 25 is higher than sma ctrl
        """
        
        rtn = False
             
        # if sma
        if(self.enable_sma_signal_eval):
            
            logger.info(" sme eval was enabled ")

            # if sma is positve
            if((self.delta_smactrl_sum > 0 and i >= self.ctrl_sma_limit) or (row['price_sma25'] > row['price_smactrl'])):
                rtn = True
                logger.info(" evalled row for sma to True as " + str(row['price_smactrl']) + " > 0 and ( (" + str(self.delta_smactrl_sum) + " > 0 and " + str(i) +" >= " + str(self.ctrl_sma_limit) +") or ( " + str(row['price_sma25']) + " > " + str(row['price_smactrl']) + "))")
                
            else:
                logger.info(" sma is negative so setting minimal profit margin  ")
                rtn = False
        else:
            rtn = True
             
        return rtn
    
    def eval_range(self, row):
        """
        eval ramge
        """
        
        # TODO: add control
        range_limit = 0.8
        
        rtn = False
        if(self.enable_live_data):
        
            rdiff = float(self.trading_range['highPrice']) - float(self.trading_range['lowPrice'])
            
            if(row['close'] <= (float(self.trading_range['lowPrice']) + (rdiff * range_limit))):
                rtn = True
                logger.info(" evalled range to True as " + str(row['close']) + " <= " + str((float(self.trading_range['lowPrice']) + (rdiff * range_limit))))
            else:
                logger.info(" evalled range to False as " + str(row['close']) + " > " + str((float(self.trading_range['lowPrice']) + (rdiff * range_limit))))
                
            self.range_score = float(row['close'] / float(self.trading_range['highPrice']))
            
        else:
            rtn = True
            
        return rtn
    
    
    
    #@profile 
    def load_exchange_info(self):
        """
        loads exchange info
        """
        
        try:
            self.exchange_info = self.client.get_exchange_info()
            symbols_info = self.exchange_info['symbols']
            
            for symbol_record in symbols_info:
                self.pairs_positions_dict[symbol_record['symbol']] = {'baseAsset': symbol_record['baseAsset'], 'quoteAsset': symbol_record['quoteAsset']}
            
        except Exception as e:
            traceback.print_exc(e)
            
            
    def register_cycle_duration(self):
        """
        registers cycle duration
        """
        
        # registering cycle duration
        
        if(self.position_open_date == None):
            self.init_total_cycle_time = self.total_cycle_time
            self.position_open_date = datetime.now()
            
        now_date = datetime.now()
        time_diff = (now_date - self.position_open_date)
        total_seconds = time_diff.total_seconds()
        #trade_duration = float(abs(total_seconds)/60)
        self.cycle_duration = abs(total_seconds)
        #logger.info(" the duration of this cycle is %s ", str(self.cycle_duration))
        
        
        # calculate average cycle duration
        #logger.info(" calculating average cycle duration ... ")
        if(self.enable_live_data):
            self.total_cycle_time = int(self.init_total_cycle_time + self.cycle_duration) #trade_duration
             
            if(self.sales_count > 0):
                self.average_cycle_time = self.total_cycle_time
                self.average_cycle_time /= self.sales_count
                self.average_cycle_time = int(self.average_cycle_time)
            else:
                self.average_cycle_time = int(self.total_cycle_time)
            
        else:
            self.total_cycle_time = 0
            self.average_cycle_time = 0
        #logger.info(" self.total_cycle_time = %s ", str(self.total_cycle_time))
        #logger.info(" self.average_cycle_time = %s ", str(self.average_cycle_time))
            
            
    def calculate_fee(self, state, trading_amount, price, base_asset, quote_asset):
        """
        calculates fee
        """
        
        fee_currency = ""
        fee_amount = 0.0
        
        # 1
        base_asset_units = 0.0
        if(state == 1):
            base_asset_units = round(float(trading_amount), self.precision) / round(float(price), self.precision)
        elif(state == 3):
            base_asset_units = trading_amount
        
        fee_level = 0.0
        fee_amount_in_base_asset = 0.0
        if(self.availBNB > 0.0):
            fee_level = 0.00075
        else:
            fee_level = 0.001
            
        fee_amount_in_base_asset = float(base_asset_units) * float(fee_level)
        bnb_quote_asset_symbol_str = "BNB" + quote_asset
        bnb_quote_asset_symbol = self.client.get_symbol_info(bnb_quote_asset_symbol_str)
        
        time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
        if(bnb_quote_asset_symbol != None):
            bnb_quote_asset_ticker = self.client.get_ticker(symbol = bnb_quote_asset_symbol_str)
            last_bnb_quote_asset_price = float(bnb_quote_asset_ticker['lastPrice']) 
            
            # 3
            last_bnb_base_asset_price = price / last_bnb_quote_asset_price
            
            # 4
            fee_amount_in_bnb = fee_amount_in_base_asset * last_bnb_base_asset_price
            
            if(fee_amount_in_bnb < self.availBNB):     
                fee_amount = fee_amount_in_bnb
                fee_currency = "BNB"
            
            else:
                
                fee_level = 0.001
                fee_amount_in_base_asset = float(base_asset_units) * float(fee_level)
                fee_amount = fee_amount_in_base_asset
                fee_currency = quote_asset
        else:
            
            fee_level = 0.001
            fee_amount_in_base_asset = float(base_asset_units) * float(fee_level)
            fee_amount = fee_amount_in_base_asset
            fee_currency = quote_asset
            
        return fee_amount, fee_currency
    
    
    def get_cached_server_time(self):
        """
        get server time once and then convert now to server_time
        """
        
        if(self.server_time == None):
            self.server_time = self.get_server_time()['str_server_time']
            
        ux_utc_current_time = datetime.utcnow() 
        
        ux_current_time = datetime.now()
        
        print(" debug ")
    
    
    def get_time_passed_since_start_time(self, ux_period_start_time, ux_period_end_time):
        """
        gets seconds passed since open time of period
        """
        
        elapsed_seconds_since_start = 0
        converted_ux_start_time = datetime.fromtimestamp(round(ux_period_start_time / 1000))
        ux_current_time = datetime.now()
        
        elapsed_seconds_since_start = int((ux_current_time - converted_ux_start_time).total_seconds())
        
        return elapsed_seconds_since_start
    
    
    def candle_eval(self, row):
        """
        evals each candle for entry and exit    
        """
        
        
        # debug
        #self.bollinger_had_entry = True 
        #self.rsi_had_entry = True
        ##
        
        
        candle_eval = False
            
        open_time = datetime.fromtimestamp(round(int(row['open_time']) / 1000))
        close_time = datetime.fromtimestamp(round(int(row['close_time']) / 1000))
        current_time = datetime.now()    
        current_open_diff = int((current_time - open_time).total_seconds())
        period_duration = int((close_time - open_time).total_seconds())
        #period_entry_boundary = float(((period_duration / 100) * 20))
        #period_exit_boundary = float(((period_duration / 100) * 80))
        current_percentage = float(current_open_diff / (period_duration / 100))
        
        if(self.state == 0):
            if(self.candle_boundary != close_time):
                if(self.bollinger_had_entry and self.rsi_had_entry):
                    if(current_percentage > 5 and current_percentage < 95):
                        cclose = row['close']
                        copen = row['open']
                        if(cclose > copen):
                            candle_eval = True
                
        elif(self.state == 2):
            if(current_percentage > 95):
                candle_eval = True
                self.candle_boundary = close_time 
    
        
        print("open time: " + str(open_time))
        print("current time: " + str(current_time))
        print("close time: " + str(close_time))
        print("current_open_diff: " + str(current_open_diff))
        print("period_duration: " + str(period_duration))
        #print("period_entry_boundary: " + str(period_entry_boundary))
        #print("period_exit_boundary: " + str(period_exit_boundary))
        print("current_percentage: " + str(current_percentage))
        
        
        
        #print("debug")
        #time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
        
        return candle_eval
    
    
    
    def eval_ema_direction(self, prev_row, row, col):
        """
        evals ema direction
        """
        
        ema_prev  = prev_row[col]
        ema  = row[col]
        
        ema_direction = -1
        
        if(ema < ema_prev):
            ema_direction = 0
        else:
            ema_direction = 1
            
        return ema_direction
    
    
    def eval_ema4(self, row):
        """
        eval ema4
        """
        
        rtn = False
        
        if(self.enable_ema4_eval):
            
            
            if(self.state == 0):
                
                if(self.ema_8_direction == 1 and self.ema_13_direction == 1 and self.ema_spread_direction == 1 and  (row['ema_8'] > row['ema_13']) ):
                    
                    rtn = True
                    
            elif(self.state == 2):
                
                if(self.ema_8_direction == 0 and self.ema_13_direction == 0 and self.ema_spread_direction == 0):
                
                    rtn = True
        else:
            rtn = True
            
        return rtn
            
            
        
    
    def eval_ema4_off(self, row, boll_eval_rslt):
        """
        ema 4 eval
        """
        
        rtn = False
        
        if(self.enable_ema4_eval):
            
           
                
            if(self.state == 0):
                
                
                # enter if the trend is up
                if(self.ema_direction == 1):
                    
                    #  enter if the trend is up
                    if( (row['ema_8'] > row['ema_13']) & (row['ema_8'] > row['ema_21']) & (row['ema_8'] > row['ema_55']) ):
                        rtn = True
                        logger.info(" evalled ema4 in state " + str(self.state) + " to True because (" + str(row['ema_8']) + " > " + str(row['ema_13']) + ") & (" + str(row['ema_13']) + " > " + str(row['ema_21']) + ") & (" + str(row['ema_21']) + " > " + str(row['ema_55']) + ") ")
                        
                        self.entered_with_bollinger = 0
                    
                # enter if bollinger is true
                #elif(  (row['ema_8'] > row['ema_55']) and self.eval_row_for_bollinger and boll_eval_rslt):
                elif(self.eval_row_for_bollinger and boll_eval_rslt):
                    rtn = True
                    logger.info(" evalled ema4 and boll in state 0 to true becasue is boll_enabled = " + str(self.eval_row_for_bollinger) + " and boll_eval_rslt = " + str(boll_eval_rslt) + " and " + str(row['ema_8']) + " > " + str(row['ema_55']))
                    
                    self.entered_with_bollinger = 1
                    
                else:
                    rtn = False
                    self.entered_with_bollinger = -1
                    
                    
                # debug force to enter state 2
                #rtn = True
                
                    
            elif(self.state == 2):
                
                
                """
                if( (row['ema_8'] <= row['ema_13']) | (row['ema_8'] <= row['ema_55'])): 
                    rtn = True
                    logger.info(" evalled ema4 in state " + str(self.state) + " to True because (" + str(row['ema_8']) + " <= " + str(row['ema_13']) + ") | (" + str(row['ema_13']) + " <= " + str(row['ema_21']) + ") | (" + str(row['ema_21']) + " <= " + str(row['ema_55']) + ") ")
                    
                el
                """
                
                # exit on 4_ema crossing down
                if( (self.ema_direction == 0) and (row['close'] <= row['ema_8']) and (row['ema_8'] > row['ema_55']) ):
                    rtn = True
                    logger.info(" evalled ema4 in state " + str(self.state) + " to True because (" + str(self.ema_direction) + " == 0 and " + str(row['close']) + " <= " + str(row['ema_13']))  
                    
                # exit on bollinger reaching middle if the trend is down
                elif( (row['ema_8'] < row['ema_55']) and (row['close'] >= row['ema_8']) ):
                    rtn = True
                    logger.info(" evalled ema4 in state " + str(self.state) + " to True because (" + str(row['ema_8']) + " < " + str(row['ema_55']) +" and (" + str(row['close']) + " >= " + str(row['boll_middle_close']) + ") ")  
                    
                else:
                    rtn = False
                    
                    
                # debug - force to stay in state 2
                #rtn = False
                
        else:
            rtn = True
        
        return rtn
    
    
    def calc_ema4(self, df):
        """
        calc ema 4
        """
        
        df['ema_8']  = ta.ema(df['close'], length =  8)
        df['ema_13'] = ta.ema(df['close'], length = 13)
        df['ema_21'] = ta.ema(df['close'], length = 21)
        df['ema_55'] = ta.ema(df['close'], length = 55)
        
        df['ema_8_13_diff'] = ta.ema( (df['ema_13'] - df['ema_8']), length = 3)
        
        df['ema_8_13_diff'] *= -1
        
        return df
    
    
    #@profile            
    def compose_data_frame(self, given_state):
        """
        composes dataframe out of all records in the given period
        """
        
        """
        print(" here ")
        
        order_status = self.client.get_order(
            symbol = self.str_symbol,
            orderId = "4455211214"
        )
        
        print("done")
        """
        
        

        if(self.str_symbol == ""):
            self.state = -1
            self.error = "symbol is not specified"
            return self.state
                
        #self.calculate_fee(self.state, test_quote_asset_amount, test_price, base_asset, quote_asset)
        
        if(self.enable_transactions):
            
            if(self.cycle_count == 0 or self.quote_asset == None):
                self.symbol_info = self.client.get_symbol_info(self.str_symbol)
                time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                
                self.base_asset = self.symbol_info['baseAsset']
                self.quote_asset = self.symbol_info['quoteAsset']
                
                
                
                #  {'filterType': '', 'minNotional': '10.00000000', 'applyToMarket': True, 'avgPriceMins': 5}
                
                filters = self.symbol_info['filters']
                for ftr in filters:
                    if ftr['filterType'] == 'LOT_SIZE':
                        self.step_size = float(ftr['stepSize'])
                
                    if(ftr['filterType'] == 'PRICE_FILTER'):
                        self.tick_size = float(ftr['tickSize'])
                        
                    if(ftr['filterType'] == 'MIN_NOTIONAL'):
                        self.min_trading_amount = float(ftr['minNotional'])
                
                if(self.step_size > 0):
                    self.precision = int(round(-math.log(self.step_size, 10), 0))  
                
                if(self.tick_size > 0):
                    self.tick_precision = int(round(-math.log(self.tick_size, 10), 0))
            
            
            
            
            self.account = self.client.get_account()
            time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
            
            if(self.quote_asset == None):
                logger.info("quote asset is not set and balance cannot be looked up")
                self.erro = "Quote asset is not set"
                return -1
            
            self.availBNB = 0.00
            for balance in self.account['balances']:
                if(balance['asset'] == "BNB"):
                    self.availBNB = float(balance['free'])
                
                elif(balance['asset'] == self.quote_asset):
                    self.trading_amount = math.floor(          (float(balance['free']) * 10)) / 10
                    logger.info("looked up trading amount = " + str(self.trading_amount))
                    
                    if(self.trading_amount > self.max_trading_amount):
                        self.trading_amount = self.max_trading_amount
                            
                    elif(self.trading_amount < self.min_trading_amount):    
                        self.insufficient_funds_condition = True
                        
                    else:
                        self.insufficient_funds_condition = False
                        
                            
            
                    
        
        # get 24 hour data every x calls
        if(self.enable_live_data):
            if((self.call_count % 25) == 0):
                logger.info(" obtaining valid range ")
                self.trading_range = self.client.get_ticker(symbol = self.str_symbol)
                time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
            
                
        logger.info(" Composing DF at %s, call count is %s ", str(datetime.now()), str(self.call_count))
        logger.info(" state is %s", str(self.state))
        self.state = given_state
        
        try:
                
            self.call_count += 1 
            # get start time
            start_time = int(str(self.__get_start_time(self.number_of_periods, self.period)) + "000")
            # get historic klines
            exec_start = time.time()
            if(self.enable_live_data):    
                
                logger.info(" live data enabled, fetching live DF ")
                df = self.get_live_dataframe(start_time, exec_start)
                
                if(df.empty):
                    self.state = -1
                    logger.info(" the df was empty, exiting with state = %s", str(self.state))
                    self.error = " live df was empty. exiting "
                    return self.state
                
            else:
                #logging.info(" static data enabled, fetching static DF ")
                df = self.load_next_static_dataframe()
                
                if(df.empty):
                    self.state = -1
                    logger.info(" the df was empty, exiting with state = %s", str(self.state))
                    self.error = "static df was empty. exiting "
                    return self.state
                
            logger.info(" prepping the df .... ")
            # set str open time
            
            
            open_time_str = []
            for index, row in df.iterrows():
                f_open_time = row['open_time']
                s_open_time = str(f_open_time)
                i_open_time = int(f_open_time)
                if(len(s_open_time) > 10):
                    f_open_time /= 1000
                    i_open_time = int(f_open_time)
                s_open_time = datetime.utcfromtimestamp(i_open_time).strftime('%Y-%m-%d %H:%M:%S')              
                open_time_str.append(s_open_time)
            df['open_time_str'] = open_time_str
            
            df.head()
            
            df['signal'] = 0
            df['signal_date'] = ""
            
            # set df index    
            df['open_time_copy'] = df['open_time']
            df = df.set_index(list(df)[0])
            df.rename(columns = {'open_time_copy': 'open_time'}, inplace = True)
            
            # initialize columns if they do not already exist
            df = df.drop(['1', '2', '3', '4', '5'], axis=1)
            
            # set df columns to numeric
            for col_name in ('open', 'high', 'low', 'close', 'volume'):
                df[col_name] = pd.to_numeric(df[col_name])
                
            df.head()
                
            cols_to_init = [
                'buy_signal', 
                'sell_signal', 
                'buy_thresh', 
                'sell_thresh',
                'stoch_rsi_k',
                'stock_rsi_d',
                'depth_bids_total',
                'depth_bids_avg_price',
                'depth_asks_total',
                'depth_asks_avg_price',
                'price_sma7',
                'price_sma7_delta',
                'price_sma25',
                'price_sma25_delta',
                'price_smactrl',
                'price_smactrl_delta',
                'price_sma_back_ctrl',
                'price_sma_back_ctrl_delta',
                'ema_8',
                'ema_13',
                'ema_21',
                'ema_55'
            ]
            for col_name in cols_to_init:
                if(not col_name in df):
                    df[col_name] = np.nan # 0.00
                    
            df['buy_signal_date'] = ''
            df['sell_signal_date'] = ''
            
            
            logger.info(" done df prep.")
            
            
            logger.info(" calculating bollinger for 'close'")
            df = self.calculate_bollinger(
                df, 
                col_str_src = 'close', 
                col_sfx = 'boll'
            )
            logger.info(" done bollinger calculation ")
                                  
            #df = self.calculate_bollinger_ta(df, col_str_src = "close", col_sfx = "boll_ta", ma_mode = "ema", period = 20);
            
            
            logger.info("calculate stoch rsi")
            df = self.StochRSI(
                df, src_col = 'close', 
                d_col = 'stoch_rsi_d', 
                k_col = 'stoch_rsi_k', 
                rsi_period = self.rsi_period, 
                stoch_period = self.stoch_period, 
                smoothK = self.smooth_k_period, 
                smoothD = self.smooth_d_period
            )
            logger.info("done rsi calculation")
            
            
            # calculate SMA and delta of it
            df['price_sma7'] = df['close'].rolling(self.sma_limit_7).mean()
            df['price_sma25'] = df['close'].rolling(self.sma_limit_25).mean()
            df['price_smactrl'] = df['close'].rolling(self.ctrl_sma_limit).mean()
             
            df['price_sma7_delta'] = df['price_sma7'].diff().shift(-1)
            df['price_sma25_delta'] = df['price_sma25'].diff().shift(-1)
            df['price_smactrl_delta'] = df['price_smactrl'].diff().shift(-1)
           
            # calculate simple trend = sum of deltas
            self.delta_sma7_sum = df['price_sma7_delta'].sum()
            self.delta_sma25_sum = df['price_sma25_delta'].sum()
            self.delta_smactrl_sum = df['price_smactrl_delta'].sum()
            
            
            df = self.calc_ema4(df)
            
            
            
            
            # drop the part of df where bolinger is not calculated
            df = df.iloc[self.boll_rolling_window:] 
            
            logger.info("starting the processing loop")
            i = 0
            for index, row in df.iterrows():
                
                # attempt to enter a buy position
                if(self.state == 0):
                    
                    buy_thresh = (((round(row['low'], self.tick_precision) - round(row['boll_low_close'], self.tick_precision)) / round(row['low'], self.tick_precision)) * 100)
                    df.at[index, 'buy_thresh'] = buy_thresh
                    
                    if(self.check_scan_row(df, i, self.state, 0, 0) == True):
                       
                        if(i > 0):
                            signal_row = df.iloc[ i - 1 ]
                        else:
                            signal_row = row
                        
                        
                        sma_eval = self.eval_row_for_sma(row, i)
                        boll_eval = self.eval_row_for_bollinger(signal_row, buy_thresh, sma_eval)
                        stoch_rsi_eval = self.eval_row_for_stoch_rsi(signal_row)
                        #range_eval = self.eval_range(row)
                        
                        
                        if(i > 0):
                            self.ema_8_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8')
                            self.ema_13_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_13')
                            self.ema_spread_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8_13_diff')
                            
                        ema4_eval = self.eval_ema4(row)
                        
                        #if(boll_eval and stoch_rsi_eval and range_eval):
                        if(ema4_eval):
                            
                            
                            logger.info(" buy condition met ")
                            
                            
                            ## DEBUG
                            self.ema_8_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8')
                            self.ema_13_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_13')
                            self.ema_spread_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8_13_diff')
                            ema4_eval = self.eval_ema4(row)
                            ## 
                            
                            
                            
                            # register buy signal for showing historically
                            if(row['open_time_str'] in self.historic_buy_signal_dates):
                                self.historic_buy_signal_dates[row['open_time_str']] = index
                    
                            
                            # count off a cycle 
                            self.cycle_count += 1
                    
                            # register buy signals        
                            df.at[index, 'buy_signal'] = row['close']
                            df.at[index, 'buy_signal_date'] = row['open_time_str']
                            self.historic_buy_signals[row['open_time_str']] = row['close']
                            self.historic_buy_signal_dates[row['open_time_str']] = index
                            logger.info(" storing a buy signal: row['open_time_str'] = %s %s %s %s %s ", str(row['open_time_str']), "; row['close'] = ", str(row['close']), "; index = ", str(index))
                            
                            avg_coef = 1
                            if(self.cycle_count > 1):
                                avg_coef = 2
                                
                            # register entry price
                            self.entry_price = row['close']
                            self.avg_entry_price += self.entry_price
                            self.avg_entry_price /= avg_coef
                            logger.info("entry price is %s", str(self.entry_price))
                                        
            
                            self.target_units_bought = float(round(float(self.trading_amount) / float(self.entry_price), self.precision))
                            self.avg_target_units_bought += self.target_units_bought
                            self.avg_target_units_bought /= avg_coef
                            logger.info(" target_units_bought  %s ", str(self.target_units_bought))
                         
                            self.amount_spent = float(self.target_units_bought) * float(self.entry_price)
                            logger.info(" self.amount_spent = %s ", str(self.amount_spent))
                            
                            
                            self.register_cycle_duration()
                            
                            if(self.insufficient_funds_condition):
                                logger.info(" INSUFFICIENT FUNDS: trading amount = " + str(self.trading_amount) + "; min amount = " + str(self.min_trading_amount))
                                continue
                            
                        
                            # implement a buy call here 
                            if(self.enable_transactions):
                            
                                logger.info(" transactions are enabled ")
                                try:
                                
                                    logger.info(" trying to submit a buy order ")
                                    logger.info(" precision " + str(self.precision))
                                    logger.info(" rounded target units bought = %s", round(self.target_units_bought, self.precision))
                                    logger.info(" rounded purchase price is " + str(round(self.entry_price, self.tick_precision)))
                                
                                    
                                    self.buy_order = self.client.create_order(
                                        symbol=self.str_symbol,
                                        side='BUY',
                                        type='LIMIT',
                                        timeInForce='GTC',
                                        quantity=round(self.target_units_bought, self.precision),
                                        price=round(self.entry_price, self.tick_precision)
                                    )
                                
                                    logger.info(" after buy order")
                                    logger.info(self.buy_order)
                                    
                                    
                                
                                except BinanceAPIException as e:
                                
                                    self.error = "an error occurred while placing a buy order"
                                    self.error += str(e)
                                    self.error += "rounded quantity (used in order) = " + str(round(self.target_units_bought, self.precision))
                                    self.error += "price = " + str(round(self.entry_price, self.precision))
                                    
                                    # error handling goes here
                                    logger.error(" BinanceAPIException while placing a buy order ")
                                    logger.error(e)
                                    logger.error("precision = " + str(self.precision))
                                    logger.error("non-rounded quantity (not used in order) = " + str(self.target_units_bought))
                                    logger.error("rounded quantity (used in order) = " + str(round(self.target_units_bought, self.precision)))
                                    logger.error("non-rounded price (not used in order) = " + str(round(self.entry_price, self.precision)))
                                    logger.error("rounded price (used in order) = " + str(round(self.entry_price, self.precision)))
                                    self.state = -1
                                    break
                                
                                except BinanceOrderException as e:
                                    # error handling goes here
                                    logger.error("BinanceOrderException while placing a buy order ")
                                    logger.error(e)
                                    self.state = -1
                                    self.error = "BinanceOrderException while placing a buy order; " + str(e)
                                    break
                            
                                if("orderId" in self.buy_order):
                                    self.state = 1
                                else:
                                    self.state = -1
                                    self.error = " incomplete buy order. investigate. exiting ";
                                    break
                                
                            else:
                                self.state = 2
            
    
                # wait for the buy position to complete
                elif(self.state == 1):
                    
                    if(self.buy_order != None and self.buy_order):
                        
                        self.register_cycle_duration()
                        
                        # we need to sleep in order to not disturb the API
                        time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                        
                        logger.info(" obtaining order status for order %s", str(self.buy_order['orderId']))
                        order_status = self.client.get_order(
                            symbol = self.str_symbol,
                            orderId = self.buy_order['orderId']
                        )
                        
                        logger.info(" order status = %s", order_status)
                        if("status" in order_status):
                            if(order_status['status'] == "NEW"):
                                logger.info(" buy order %s has not been filled yet ", self.buy_order['orderId'])
                                
                            elif(order_status['status'] == "PARTIALLY_FILLED"):
                                logger.info(" buy order %s has been partially filled ", self.buy_order['orderId'])
                                
                            elif(order_status['status'] == "FILLED"):
                                logger.info(" buy order %s has been filled ", self.buy_order['orderId'])
                                self.state = 2
                                
                                time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                                self.buy_fee, self.buy_fee_currency = self.calculate_fee(
                                    self.state, 
                                    float(self.trading_amount), 
                                    round(self.entry_price, self.tick_precision), 
                                    self.base_asset, 
                                    self.quote_asset
                                )
                        #else:
                            
                            
                        
                                
                    else:
                        logger.error(" buy order details were not available, exiting process to investigate ")
                        self.state = -1
                        self.error = "buy order details were not available, exiting process to investigate" 
                        break
                    
                elif(self.state == 2):
                    
                    self.register_cycle_duration()
                    
                    
                    # gets latest buy signal time
                    historic_time = sorted(list(self.historic_buy_signal_dates.keys()))[-1:][0]
                    row_open_time_str = row['open_time_str']
                    #logger.info(" timestamps of the last buy signal was: historic_time = %s %s %s ", str(historic_time), "; row_open_time_str = ", str(row_open_time_str))
                    
                    # check if this row['open_time_str'] matches any time_str in historic signal
                    # if it does then set the index to the current index
                    if(row['open_time_str'] in self.historic_sell_signal_dates):
                        self.historic_sell_signal_dates[row['open_time_str']] = index
                    
                    #logger.info(" check whether the row can be evaluated for sell entry ...")
                    if(self.check_scan_row(df, i, self.state, historic_time, row_open_time_str)):  
                        
                        # get previous closed row for signal eval
                        if(i > 0):
                            signal_row = df.iloc[ i - 1 ]
                        else:
                            signal_row = row
                        
                        # signal evaluation
                        
                        
                        
                        #sma_eval = self.eval_row_for_sma(row, i)
                        #boll_eval = self.eval_row_for_bollinger(signal_row, 0.0, sma_eval)
                        #stoch_rsi_eval = self.eval_row_for_stoch_rsi(signal_row)
                            
                        #logger.info(" compare current close value and target price to evaluate sell positions ....")
                        
                        """
                        evalz = False
                        if(sma_eval):
                            evalz = stoch_rsi_eval and self.sell_bollinger_touched
                            logger.info(" in state 2 and sma true evalz evalled to " + str(evalz) + " from stoch_rsi_eval = " + str(stoch_rsi_eval) + " and sell_bollinger_touched = " + str(self.sell_bollinger_touched))
                        else:
                            evalz = (stoch_rsi_eval or self.sell_bollinger_touched) and (row['close'] > self.entry_price)
                            logger.info(" in state 2 and sma false evalz evalled " + str(evalz) + " from (stoch_rsi_eval = " + str(stoch_rsi_eval) + " or sell_bollinger_touched = " + str(self.sell_bollinger_touched) + ") and ( " + str(row['close']) + " > " + str(self.entry_price) + ")")
                        """
                        
                        if(i > 0):
                            self.ema_8_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8')
                            self.ema_13_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_13')
                            self.ema_spread_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8_13_diff')
                            
                        
                        ema4_eval = self.eval_ema4(row)
                        
                        
                        #if(boll_eval and stoch_rsi_eval):
                        if(ema4_eval): # and (row['close'] > (self.entry_price * 1.002))):
                        
                        
                        
                        #if(stoch_rsi_eval or self.sell_bollinger_touched):       
                            
                                                             
                            logger.info(" sell condition was met ")
                            
                            ## DEBUG
                            self.ema_8_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8')
                            self.ema_13_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_13')
                            self.ema_spread_direction = self.eval_ema_direction(df.iloc[ i - 1 ], df.iloc[i], 'ema_8_13_diff')
                            ema4_eval = self.eval_ema4(row)
                            ## 
                            
                            
            
                            self.sales_count += 1
                            logger.info(" self.sales_count = %s ", str(self.sales_count))
                            
                            # store signal
                            logger.info(" storing sell historic signals ")
                            signal_field = 'sell_signal'
                            signal_date_field = 'sell_signal_date'
                            df.at[index, signal_field] = row['close']
                            df.at[index, signal_date_field] = row['open_time_str']
                            self.historic_sell_signals[row['open_time_str']] = row['close']
                            self.historic_sell_signal_dates[row['open_time_str']] = index
                            logger.info(" row['close'] = %s ", str(row['close']))
                            logger.info(" row['open_time_str'] = %s ", str(row['open_time_str']))
                            logger.info(" index = %s ", str(index))
                    
                            avg_coef = 1
                            if(self.cycle_count > 1):
                                avg_coef = 2
                                
                            # calculate average sales price
                            # TODO: what should be the exit price
                            self.exit_price = row['close'] 
                            self.avg_exit_price += self.exit_price
                            self.avg_exit_price /= avg_coef
                            logger.info(" calculated self.avg_exit_price = %s ", str(self.exit_price))
                            
                            # calculate profit
                            self.target_units_sold = round(self.target_units_bought * self.exit_price, self.precision)
                            self.avg_units_sold += self.target_units_sold
                            self.avg_units_sold /= avg_coef 
                            logger.info(" calculated self.target_units_sold = %s ", str(self.target_units_sold))
                            
                            self.cycle_profit = self.target_units_sold - self.amount_spent
                            logger.info(" calculated self.cycle_profit = %s ", str(self.cycle_profit))
                            
                            self.total_profit += self.cycle_profit
                            self.average_gain = self.total_profit / self.sales_count
                            logger.info(" calculated self.average_gain = %s ", str(self.average_gain))
                            
                            # place sell order here 
                            if(self.enable_transactions):
                                try:
                                    self.sell_order = self.client.create_order(
                                        symbol=self.str_symbol,
                                        side='SELL',
                                        type='LIMIT',
                                        timeInForce='GTC',
                                        quantity=round(self.target_units_bought, self.precision),
                                        price=round(self.exit_price, self.tick_precision)
                                    )
                                    
                                except BinanceAPIException as e:
                            
                                    self.error = "an error occurred while placing a sell order"
                                    self.error += str(e)
                                    self.error += "quantity = " + str(round(self.target_units_bought, self.precision))
                                    self.error += "price = " + str(round(self.exit_price, self.precision))
                                    
                                    logger.error(" an error occurred while placing a sell order")  
                                    logger.error(e)
                                    logger.erro("symbol = %s", self.str_symbol)
                                    logger.error("side = %s", 'SELL')
                                    logger.error("type = %s", 'LIMIT')
                                    logger.error("timeInForce = %s", 'GTC')
                                    logger.error("quantity = %s", str(round(self.target_units_bought, self.precision)))
                                    logger.error("price = %s", str(round(self.exit_price, self.precision)))
                                                       
                                    exception_handled = False
                                    estr = str(e)
                                    if(self.INSUFFICIENT in estr):
                                        
                                        logger.error(" insufficient funds exception detected. attempting to correct ...")
                                        time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                                        
                                        if(self.pairs_positions_dict != None):
                                            
                                            try:
                                                base_asset = self.pairs_positions_dict[self.str_symbol]['baseAsset']
                                                logger.info(" base asset is " + base_asset)
                                                
                                                live_asset_balance = self.client.get_asset_balance(base_asset)
                                                logger.info(" asset live balance is %s", str(live_asset_balance))
                                                
                                                free = float(live_asset_balance['free'])
                                                logger.info(" free is %s", str(free))
                                                
                                                locked = float(live_asset_balance['locked'])
                                                logger.info(" locked is %s", str(locked))
                                                
                                                if(locked == 0.00 and self.target_units_bought > free):
                                                    
                                                    try:
                                                        self.sell_order = self.client.create_order(
                                                            symbol=self.str_symbol,
                                                            side='SELL',
                                                            type='LIMIT',
                                                            timeInForce='GTC',
                                                            quantity=round(free, self.precision),
                                                            price=round(self.exit_price, self.tick_precision)
                                                        )
                                                        
                                                        exception_handled = True
                                                        
                                                    except BinanceAPIException as e3:
                                                        
                                                        self.error = "an error occurred while placing a correcting sell order"
                                                        self.error += str(e)
                                                        self.error += "quantity = " + str(round(self.target_units_bought, self.precision))
                                                        self.error += "price = " + str(round(self.exit_price, self.precision))
                                    
                                                        logger.error(" attempt to sell adjusted base asset amount failed in API ")
                                                        logger.error(e3)
                                                        logger.error("quantity = " + str(round(self.target_units_bought, self.precision)))
                                                        logger.error("price = " + str(round(self.exit_price, self.precision)))
                                                        self.state = -1
                                                        
                                                    except BinanceOrderException as e3:
                                                        logger.error(" attempt to sell adjusted base asset amount failed in Order ")
                                                        logger.error(e3)
                                                        self.state = -1
                                                        self.error = " attempt to sell adjusted base asset amount failed in Order " 
                                                
                                                else:
                                                    
                                                    logger.error(" not attempting to sell because some asset amount is locked and funds are insufficient ")
                                                    self.state = -1
                                                    self.error = "not attempting to sell because some asset amount is locked and funds are insufficient"
                                                     
                                            except Exception as e2:
                                                logger.error(" attempted to resubmit a sell order and encountered setup errors ")
                                                logger.error(e2)
                                                self.state = -1 
                                                self.error = " attempted to resubmit a sell order and encountered setup errors "
                                        
                                        else:
                                            logger.error(" pair information is not available")
                                            self.state = -1
                                            self.error = "pair information is not available"
                                        
                                    if(exception_handled == False):
                                        # error handling goes here
                                        logger.error(" BinanceAPIException while placing a sell order ")
                                        logger.error(e)
                                        self.state = -1
                                        self.erro = "BinanceAPIException while placing a sell order; " + str(e)
                                        
                                        
                                    
                                except BinanceOrderException as e:
                                    # error handling goes here
                                    logger.error("BinanceOrderException while placing a sell order ")
                                    logger.error(e)
                                    self.state = -1
                                    self.error = "BinanceOrderException while placing a sell order; " + str(e)
                                    
                                if("orderId" in self.sell_order):
                                    logger.info(" placed sell order and will now await its completion ")
                                    self.state = 3
                                    
                                else:
                                    
                                    logger.error(" orderid was not available in the sell_order ")
                                    logger.error(" manually investigate. exiting the market  ")
                                    self.state = -1    
                                    self.error = "sell order may be incomplete ";
                                    
                                    
                            else:
                                self.clear_cycle()
                                self.state = 0
                                
                        
                                    
                
                elif(self.state == 3):
                    
                    if(self.sell_order != None and self.sell_order != {}):
                        
                        self.register_cycle_duration()
                        
                        logger.info(" waiting for the sell order to complete ")
                        time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                        
                        logger.info(" obtaining order status for sell order %s", str(self.sell_order['orderId']))
                        order_status = self.client.get_order(
                            symbol = self.str_symbol,
                            orderId = self.sell_order['orderId']
                        )
                        
                        if("status" in order_status):
                            if(order_status['status'] == "NEW"):
                                logger.info(" sell order %s has not been filled yet ", self.sell_order['orderId'])
                            
                            elif(order_status['status'] == "PARTIALLY_FILLED"):
                                logger.info(" sell order %s has been partially filled ", self.sell_order['orderId'])
                                
                            elif(order_status['status'] == "FILLED"):
                                logger.info(" sell order %s has been filled ", self.buy_order['orderId'])
                                
                                time.sleep(self.SLEEP_PERIOD_FOR_ORDER_HANDLING)
                                self.sell_fee, self.sell_fee_currency = self.calculate_fee(
                                    self.state,
                                    float(self.trading_amount), 
                                    round(self.exit_price, self.tick_precision), 
                                    self.base_asset, 
                                    self.quote_asset
                                )
                            
                                self.clear_cycle()
                                self.state = 0
                
                    else:
                        logging.error(" there is an issue with the sell order. abandoning this cycle and exiting ")
                        self.state = -1
                        self.error = " there is an issue with the sell order. abandoning this cycle and exiting "; 
                        break
                    
                        
                i += 1
                
            logger.info(" exited scan loop ...")
            logger.info(" cleaning up signals ")
            logger.info(" now self state is this ")
            logger.info(self.state)
            
            # fix signals
            df['buy_signal'] = pd.to_numeric(df['buy_signal'])
            df['buy_signal'] = df['buy_signal'].fillna(0)
            
            try:
                df['buy_signal_date'] = df['buy_signal_date'].fillna(0)
            except:
                pass
                        
            # fix signals
            df['sell_signal'] = pd.to_numeric(df['sell_signal'])
            df['sell_signal'] = df['sell_signal'].fillna(0)
            
            try:
                df['sell_signal_date'] = df['sell_signal_date'].fillna(0)
            except:
                pass
            logger.info(" cleaned up signals ")
                        
            # ensure that dataframe does not grow
            logger.info(" prevent df from growing ")
            df_size_dif = len(df.index) - self.number_of_periods
            if df_size_dif != 0:
                if df_size_dif < 0:
                    df_size_dif *= -1
                df = df[df_size_dif:]

            #time_boundary_timestamp_numpy = df['open_time'].values[0]
            time_boundary_str = df['open_time_str'].values[0]
            time_boundary_timestamp = self._get_timestamp_from_str(time_boundary_str, "%Y-%m-%d %H:%M:%S")
            self.utx_time_boundary = time_boundary_str
            self.str_time_boundary = time_boundary_timestamp
            #logger.info(" calculated time boundaries ")
            #logger.info(" self.utx_time_boundary = %s ", str(self.utx_time_boundary))
            #logger.info(" self.str_time_boundary = %s ", str(self.str_time_boundary))
            
            
            if(self.call_count > 1):
                logger.info(" applying signals to df ... ")           
                
                df = self.load_historic_signals(
                    df, 
                    'buy_signal',
                    'buy_signal_date',
                    self.historic_buy_signals, 
                    self.historic_buy_signal_dates, 
                    time_boundary_timestamp
                )
                
                df = self.load_historic_signals(
                    df,
                    'sell_signal',
                    'sell_signal_date', 
                    self.historic_sell_signals, 
                    self.historic_sell_signal_dates, 
                    time_boundary_timestamp
                )
                
            self.df = df    
            del df
       
        except Exception as ex:
            """
            handle all other exceptions 
            """
            
            logging.info(" exception occurred " + traceback.print_exc())
            
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            
            if("connection".lower() in message.lower()):
                self.state = -2
                
                logging.info(" connection exception ")
                
            else:
                self.state = -1    
                self.error = " unable to reconnect. exiting ... " + traceback.format_exc()
                
                logging.info("state exception")
                
            traceback.print_exc()
            
            
            
        logger.info(" df has been processed. returning state %s ", str(self.state))
        return self.state
    
    #@profile 
    def clear_cycle(self):
        """
        clear cycle state
        """
        logger.info(" resetting state after sell order completion ")        
       
        self.entry_price = 0.00
        
        self.cycle_duration = 0
        self.target_units_bought = 0.00
        self.target_units_sold = 0.00

        self.trading_amount = float(self.starting_amount * 1)
        self.amount_spent = 0.0000
        
        self.buy_order = {}
        self.sell_order = {}
        
        self.exit_price = 0.0
        self.cycle_profit = 0.0
        
        self.error = ""
        
        self.buy_fee = 0.00
        
        self.sell_fee = 0.00
        
        self.buy_fee_currency = ""
        
        self.sell_fee_currency = ""
        
        self.position_open_date = None
        
        
        self.entered_with_bollinger = -1
        
        #self.bollinger_had_entry = False
        #self.rsi_had_entry = False
        
        

    #@profile 
    def check_scan_row(self, df, i, state, historic_time, row_open_time_str):
        """
        check if the row can be scanned
        """
        #logger.info(" scanning the row for entry conditions .... ")
        scan_row = False
        if(self.enable_live_data):
            scan_row = (i >= len(df.index) - 1)
        else:
            if(state == 0):
                scan_row = (((i >= len(df.index) - 1) or self.call_count == 1))        
            else:
                scan_row = (((i >= len(df.index) - 1) or self.call_count == 1) and (historic_time < row_open_time_str))
            
        #logger.info(" row at %s %s %s ", str(i), " scan result is ", str(scan_row))
        
        return scan_row
    
    #@profile            
    def get_clear_value_set(self, df, field):
        """
        gets cleared value set
        """
        try:
            s = df[field]
            l = s.to_list()
            ll = [i for i in l if i != 0 and i != "\"NaN\"" and i != "NaN" and i != ""] 
            cleared_signal_series = pd.Series(ll)
            return cleared_signal_series
        except: 
            return pd.Series.empty
    
    #@profile 
    def load_historic_signals(self, df, signal_label, signal_date_label, signal_history, signal_index_history, time_boundary_timestamp):
        """
        load signals and return the updated df
        """
        #logger.info(" signal_label = %s ", str(signal_label))
        #logger.info(" signal_date_label = %s ", str(signal_date_label))
        #logger.info(" time_boundary_timestamp = %s ", str(time_boundary_timestamp))
        try:  
            for historic_signal_date, historic_signal_price in signal_history.items():
                # 2020-05-06 22:31:00 - %Y-%m-%d %H:%M:%s
                # 1588802760000 <class 'numpy.int64'>
                # 2020-05-06 22:31:00 <class 'str'>
                historic_timestamp = self._get_timestamp_from_str(historic_signal_date, "%Y-%m-%d %H:%M:%S")
                index = signal_index_history[historic_signal_date]
                if(historic_timestamp >= time_boundary_timestamp):
                    df.at[index, signal_label] = historic_signal_price
                    df.at[index, signal_date_label] = historic_signal_date
                    #logger.info(" historic_signal_price = %s ", str(historic_signal_price))
                    #logger.info(" historic_signal_date = %s ", str(historic_signal_date))
                    #logger.info(" index = %s ", str(index))
                    
        except Exception as e:
            logger.error(" exception occured while updating DF with historic signals ")
            logger.error(e)
        
        return df
    
    #@profile     
    def is_threshold_used(self):
        """
        returns bool if threshold is used
        """
        rtn = False
        if(self.limit_threshhold > 0.00):
            rtn = True
        return rtn
    
    #@profile     
    def compare(self, value1, value2):
        """
        value1 is the close
        value2 is the bol
        """
        rtn = False
        decrease = value1 - value2
        if(decrease <= 0):
            rtn = True
        else:
            pct = (value1 / decrease) * 100
            if(pct > self.LIMIT_THRESHOLD):
                rtn = True
        return rtn
    
    #@profile 
    def get_df_compose_time(self):
        return self.df_compose_time
    
    #@profile 
    def get_klines_exec_time(self):
        return self.klines_exec_time
    
    #@profile 
    def get_dataframe(self):
        """
        return data frame
        """
        return self.df
    
    #@profile 
    def set_data_frame(self, df):
        """
        reset
        """
        self.df = df
        self.reset_historic_signals()
        self._reset_ticker()
        self.state = 0
    
    #@profile 
    def get_call_count(self):
        """
        get call count
        """
        return self.call_count
    
    #@profile 
    def get_direction(self):
        """
        ets direction: deprecated
        """
        return self.simple_direction
    
    #@profile 
    def get_pofit(self):
        """
        returns profit
        """    
        return self.profit
    
    #@profile 
    def get_cycle_profit(self):
        """
        last profit
        """
        return self.cycle_profit
    
    #@profile 
    def get_average_trade_duration(self):
        """
        returns average trade duration
        """
        return self.average_cycle_time
    
    #@profile 
    def get_average_gain(self):
        """
        returns average gain/loss (pos/neg)
        """
        return self.average_gain
    
    #@profile 
    def get_cycle_count(self):
        """
        returns the number of threads
        """
        return self.cycle_count
    
    #@profile 
    def get_cycle_duration(self):
        """
        get cycle duration
        """
        return self.cycle_duration
    
    #@profile 
    def get_static_df_file_name(self):
        """
        returns the name of the last used CSV file
        """
        return self.next_df_filename
        
    #@profile 
    def get_dfs_time_boundary_utx(self):
        """
        returns unix timestamp timeboundary
        """ 
        return self.utx_time_boundary
    
    #@profile 
    def get_dfs_timeboundary_str(self):
        """
        returns string time boundary
        """
        return self.str_time_boundary
    
    #@profile 
    def get_total_cycle_time(self):
        """
        get total cycle time
        """
        return float(self.total_cycle_time)
    
    #@profile 
    def get_target_entry_price(self):
        """
        get target entry price
        """
        return float(self.entry_price)
        
    #@profile 
    def get_target_units_bought(self):
        """
        get get_target_units_bought
        """
        return float(self.target_units_bought)
    
    
    #@profile 
    def get_target_units_sold(self):
        """
        get target_units_sold
        """
        return float(self.target_units_sold)
    
    #@profile 
    def get_evg_units_sold(self):
        """
        get level_average_units_sold
        """
        return float(self.avg_units_sold)
    
    #@profile 
    def get_exit_price(self):
        """
        get exit_price
        """
        return float(self.exit_price)
    
    #@profile 
    def get_buy_order_details(self):
        """
        return buy order details
        """
        return self.buy_order
    
    #@profile 
    def get_sell_order_details(self):
        """
        return sell order details
        """
        return self.sell_order
    
    #@profile 
    def get_bids_total(self):
        """
        bids total
        """
        return self.bids_total
    
    #@profile 
    def get_bids_avg_price(self):
        """
        bids avg price
        """
        return self.bids_avg_price
    
    #@profile 
    def get_asks_total(self):
        """
        asks total
        """
        return self.asks_total
    
    #@profile 
    def get_asks_avg_price(self):
        """
        asks avg price
        """
        return self.asks_avg_price
    
    #@profile 
    def get_price_sma7_delta_sum(self):
        """
        get price sma 7
        """
        return self.delta_sma7_sum
    
    #@profile 
    def get_price_sma25_delta_sum(self):
        """
        get price sma 25
        """
        return self.delta_sma25_sum
    
    #@profile 
    def get_price_smactrl_delta_sum(self):
        """
        get price sma ctrl
        """
        return self.delta_smactrl_sum
    
    def get_price_sma_back_ctrl_delta_sum(self):
        """
        gets back sma delta sum
        """
        return self.delta_sma_back_ctrl_sum
    
    def get_error(self):
        """
        get error
        """
        return self.error
    
    def get_range_score(self):
        """
        get range score
        """
        return self.range_score
    

    def get_average_purchase_price(self):
        """
        get average purchase price
        """
        return self.avg_entry_price
    
    
    def get_avg_units_bought(self):
        """
        get avg units bought
        """
        return self.avg_target_units_bought
        
        
    def get_avg_exit_price(self):
        """
        get avg exit price
        """        
        return self.avg_exit_price

    
    def get_buy_fee(self):
        """
        get fee
        """
        return self.buy_fee
    
    
    def get_sell_fee(self):
        """
        get fee
        """
        return self.sell_fee
    
    
    def get_buy_fee_currency(self):
        """
        fee currency
        """
        
        return self.buy_fee_currency
    
    
    def get_sell_fee_currency(self):
        """
        fee currency
        """
        
        return self.sell_fee_currency
    
    