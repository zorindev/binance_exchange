
from datetime import datetime, timedelta
import time

from binance.client import Client

import pandas as pd



def get_start_time(sma_size, period):
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
    

client = Client("l2ortiH8RTYzQNZsprkygTgbFg7Q7W1aZ3k8rX5IL0lC3NaEbnFI5chQOHCqhB86", "qbvaOxtXTjyVIteO5jHAdxoYHYaIma5Ez8SRkGISnpy0o3V7Li0OYzfBexnMom8h")


start_time = int(str(get_start_time(10, "1m")) + "000")

print start_time

history_klines = client.get_klines(
    symbol = "BNBBTC",
    interval = "3m",
    startTime = start_time
)

# create data frame
labels = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', '1', '2', '3', '4','5']
df = pd.DataFrame(history_klines, columns=labels)
df.to_csv("df.csv")