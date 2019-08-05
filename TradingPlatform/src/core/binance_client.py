import os
import sys

from datetime import datetime, timedelta
import time

from client_interface import ExchangeClientInterface
from interface import implements
from binance.client import Client

import pandas as pd
import numpy as np
from pandas_datareader import data

from logging import Logger as logger

from pprint import pformat
from pip._internal.commands.search import highest_version

from decimal import Decimal
#from pandas.tests.io.test_parquet import df_compat


class binance_client(implements(ExchangeClientInterface)):
    
    
    LIMIT_THRESHOLD = 0.05
    
    df = None
    
    D_SMA_SIZE = 10
    
    STOCH_LOW_BNDR = 20
    STOCH_HIGH_BNDR = 80
    
    client = None
    
    ticker = None
    
    klines_exec_time = 0.0
    df_compose_time = 0.0
    
    call_count = 0
    
    
    
    def __init__(self, api_key, api_secret, number_of_periods, period, rolling_window):
        """
        """
        self.client = Client(api_key, api_secret)
        np.set_printoptions(suppress=True)
        
        self.number_of_periods = number_of_periods * 1
        self.rolling_window = rolling_window * 1
        self.period = period
        
        
        self.stored_signals = {}
        
        
    
    def get_server_time(self):
        """
        """
        server_time = self.client.get_server_time()
        server_time['str_server_time'] = self._get_str_time(server_time['serverTime'])
        return server_time 
    
    def _reset_ticker(self):
        """
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
    
    def get_current_price(self, str_symbol, str_period, int_number_of_records):
        
        self._reset_ticker()
        
        logger.info("getting current price for " + str_symbol)
        
        if(self.currennt_kline):
            self.one_kline = self.client.get_klines(
                symbol = str_symbol,
                interval = str_period,
                limit = int_number_of_records
            )
        
        logger.info(pformat(self.one_kline))
        
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
    
    
    def __get_start_time(self, sma_size, period):
        """
        returns unix timestamp of right now minus sma_size days ago
        """
        
        period_size = int((period[0]) * 1)
        period_type = period[1]
        
        if(period_type == "d"):
            d = datetime.today() - timedelta(days=(sma_size * period_size))
            return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            
        elif(period_type == "m"):
            d = datetime.today() - timedelta(minutes=(sma_size * period_size))
            return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            
        elif(period_type == "h"):
            d = datetime.today() - timedelta(hours=(sma_size * period_size))
            return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            
        elif(period_type == "w"):
            d = datetime.today() - timedelta(weeks=(sma_size * period_size))
            return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            
        elif(period_type == "M"):
            d = datetime.today() - timedelta(months=(sma_size * period_size))
            return int(time.mktime(datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S.%f").timetuple()))
            
        else:
            return None
        
        
    
    def compose_data_frame(self, str_symbol, given_state):
        """
        composes dataframe out of all records in the given period
        """
        
        state = given_state
        
        try:
            
            self.call_count += 1
            
            # get start time
            start_time = long(str(self.__get_start_time(self.number_of_periods, self.period)) + "000")
            
            
            # get historic klines
            exec_start = time.time()
            
                
            self.history_klines = self.client.get_klines(
                symbol = str_symbol,
                interval = self.period,
                startTime = start_time
            )
            
            exec_end = time.time()        
            self.klines_exec_time = (exec_end - exec_start)
            
            
            # set current kline
            exec_start = time.time()
            self.currennt_kline = self.history_klines[len(self.history_klines) - 1]
            exec_end = time.time()
            self.current_kline_creation_time = (exec_end - exec_start)
            
            
            # create data frame
            labels = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', '1', '2', '3', '4','5']
            df = pd.DataFrame(self.history_klines, columns=labels)
            
                
            # set str open time
            open_time_str = []
            for index, row in df.iterrows():
                ts = int(str(row['open_time'])[:-3])
                open_time_str.append(datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
                
            df['open_time_str'] = open_time_str
            
            df['signal'] = 0
            df['signal_date'] = ""
            
            
            # set df index    
            df = df.set_index(list(df)[0])
            
            # drop extra columns
            df = df.drop(['close_time', '1', '2', '3', '4', '5'], axis=1)
            
            # set df columns to numeric
            for col_name in ('open', 'high', 'low', 'close', 'volume'):
                df[col_name] = pd.to_numeric(df[col_name])
            
                
            # set stochastic oscilator
            df['stoch_low'] = df['low'].rolling(window = self.rolling_window).min()
            df['stoch_high'] = df['high'].rolling(window = self.rolling_window).max()
            df['%K'] = 100 * ((df['close'] - df['stoch_low']) / (df['stoch_high'] - df['stoch_low']))
            df['%D'] = df['%K'].rolling(window = self.rolling_window).mean()
            df.loc[df['%D'].isna(), '%D'] = df.loc[df['%D'].isna(), '%K'] 
            
            
            #set bollinger bands
            rolling_mean = df['close'].rolling(self.rolling_window).mean()
            rolling_std = df['close'].rolling(self.rolling_window).std()
            df['boll_high'] = rolling_mean + (rolling_std * 2)
            df['boll_low'] = rolling_mean - (rolling_std * 2)
            
            
            df.dropna(inplace=True)
            # clean none values
            df['stoch_high'] = df[['stoch_high']].convert_objects(convert_numeric=True).fillna(0)
            df['stoch_low'] = df[['stoch_low']].convert_objects(convert_numeric=True).fillna(0)
            
            df['%K'] = df[['%K']].convert_objects(convert_numeric=True).fillna(0)
            #df.loc[(df['%K'] == 0), '%K'] = df[df['%K'] != 0].min(axis=1)
            
            df['%D'] = df[['%D']].convert_objects(convert_numeric=True).fillna(0)
            #df.loc[(df['%D'] == 0), '%D'] = df[df['%D'] != 0].min(axis=1)
            
            df['boll_high'] = df[['boll_high']].convert_objects(convert_numeric=True).fillna(0)
            #df.loc[(df['boll_high'] == 0), 'boll_high'] = df[df['boll_high'] != 0].min(axis=1)
            
            df['boll_low'] = df[['boll_low']].convert_objects(convert_numeric=True).fillna(0)
            
            df['close'] = df[['close']].convert_objects(convert_numeric=True).fillna(0)
            #df.loc[(df['boll_low'] == 0), 'boll_low'] = df[df['boll_low'] != 0].min(axis=1)
            
            
            # set buy signals
            if(state == 0):
                df['buy_thresh'] = (((df['low'] - df['boll_low']) / df['low']) * 100) 
                df.loc[((  df['buy_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] < self.STOCH_LOW_BNDR) & (df['%K'] > df['%D'])), 'signal']      = df.loc[((  df['buy_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] <= self.STOCH_LOW_BNDR) & (df['%K'] > df['%D']) ), 'close']
                df.loc[((  df['buy_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] < self.STOCH_LOW_BNDR) & (df['%K'] > df['%D'])), 'signal_date'] = df.loc[((  df['buy_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] <= self.STOCH_LOW_BNDR) & (df['%K'] > df['%D']) ), 'open_time_str']
                
            # set sell signals
            elif(state == 2):
                df['sell_thresh'] = (((df['boll_high'] - df['high']) / df['boll_high']) * 100) 
                df.loc[((  df['sell_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] > self.STOCH_HIGH_BNDR) & (df['%K'] < df['%D'])), 'signal']      = df.loc[((  df['sell_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] > self.STOCH_HIGH_BNDR) & (df['%K'] < df['%D'])), 'close']
                df.loc[((  df['sell_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] > self.STOCH_HIGH_BNDR) & (df['%K'] < df['%D'])), 'signal_date'] = df.loc[((  df['sell_thresh'] <= self.LIMIT_THRESHOLD ) & (df['%K'] > self.STOCH_HIGH_BNDR) & (df['%K'] < df['%D'])), 'open_time_str']
                   
            
            
            # update the existing dataframe with stored signals
            for idx, signal_record in self.stored_signals.iteritems():
                df.loc[idx, 'signal'] = signal_record[0]
                df.loc[idx, 'signal_date'] = signal_record[1]
           
           
            # capture last signal 
            last_index = df.index.values[-1:][0]
            last_signal = df.loc[df.index[-1:][0], 'signal']
            last_signal_date = df.loc[df.index[-1:][0], 'signal_date']
            if(last_signal > 0):
                self.stored_signals[last_index] = [last_signal, last_signal_date]
                
                if(state == 0):
                    state = 2
                elif(state == 2):
                    state = 0
                

            
            # log the dataframe
            self.df = df
            exec_end = time.time()
            self.df_compose_time = (exec_end - exec_start)
            self.df.to_csv("df.csv")
            
            
            # ensure that dataframe does not grow
            df_size_dif = len(self.df.index) - self.number_of_periods
            if df_size_dif != 0:
                if df_size_dif < 0:
                    df_size_dif *= -1
                self.df = self.df[df_size_dif:]
            
            
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            
            state = -1
            
            
        return state
        
    
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
    
        
    def get_df_compose_time(self):
        return self.df_compose_time
    
    def get_klines_exec_time(self):
        return self.klines_exec_time
    
    
    def get_dataframe(self):
        """
        return data frame
        """
        
        return self.df
    
    def set_data_frame(self, df):
        """
        """
        
        self.stored_signals = {}
        self.df = df
    
    
    def get_from_df(self, df_col):
        """
        get raw python types from df
        """
        rtn = []
        
        
        # print "IDX MAX: ", self.df.max()
        
       
        #for index, row in self.df.head().iterrows():
        #    print row, index
            
            
        print self.df.head()
        print self.df.columns.values.tolist()
        
        return rtn
    
    def get_call_count(self):
        
        return self.call_count