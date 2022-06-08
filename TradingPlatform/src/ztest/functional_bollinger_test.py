

from datetime import datetime, timedelta
import time
from datetime import timezone

from binance.client import Client
import pandas as pd
import numpy as np
from pandas_datareader import data


#client = Client("sK0b4AQOdbLup3PXtBhuPKbxwef6f8GJh6sJBx7bbs94wUgNsDmldByUYdvumIbe", "7nDSilhRy5uxSt5DuUz83gVRc7arJLUrohhxCUtgiOtN65JgYM8BdrUxgeGKMwSI")

# WTnjFhfITQIKCcvsb0p5MBAxYbq1OkCbpw6znlfUnmSdv2MfRnd02KEbflZOUtf3 :: hf7erl6Gh9CPTHFfGaW5p5FMM9k5Oqlv0ITBPZozfYAOTy4qlMnoq2S6TkNU2RHj

client = Client("WTnjFhfITQIKCcvsb0p5MBAxYbq1OkCbpw6znlfUnmSdv2MfRnd02KEbflZOUtf3", "hf7erl6Gh9CPTHFfGaW5p5FMM9k5Oqlv0ITBPZozfYAOTy4qlMnoq2S6TkNU2RHj")

klines = client.get_klines(
    symbol = "BTCUSDT",
    interval = "1m",
    startTime = 1608499560000,
    limit = 2
)

labels = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', '1', '2', '3', '4', '5']
df = pd.DataFrame(klines, columns=labels)

for j in range(0, (df.shape[0])):
    print(int(str(df.iloc[j]['open_time'])))          
    str_open_time = datetime.utcfromtimestamp(int(str(df.iloc[j]['open_time'])[:-3])).strftime('%Y-%m-%d %H:%M:%S')
    print("open time: " + str_open_time + "; open: " + str(df.iloc[j]['open']) + "; low: " + str(df.iloc[j]['low']) + "; high: " + str(df.iloc[j]['high']) + "; close: " + str(df.iloc[j]['close']))
    
