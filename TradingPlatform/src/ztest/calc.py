'''
Created on Jul 31, 2020

@author: leaz
'''
import pandas as pd
import numpy as np
from pandas_datareader import data


numbers = {
    "one": [17,  5,  1,  4,  1, 11,  4,  2,  1,  3,  5,  2,  1,  7,  1,  6,  2,  2,  5,  9, 11,  4,  2,  1, 13,  6,  9,  2, 11,  4, 11,  7],   
    "two": [19,  7,  5, 13,  2, 17,  7, 20,  2, 17,  9,  9,  3,  9,  2,  9,  4,  5, 13, 26, 15,  6, 11,  4, 14,  8, 11,  9, 15,  6, 20, 10],
    "three": [26, 11,  6, 23,  3, 18, 29, 25, 18, 19, 12, 23, 16, 24,  5, 16, 11, 27, 20, 28, 25, 10, 12, 11, 19, 12, 23, 18, 17, 20, 23, 11],
    "four": [29, 40, 32, 28, 17, 20, 35, 36, 36, 20, 18, 29, 33, 30, 10, 19, 19, 32, 37, 32, 36, 20, 25, 17, 26, 19, 33, 33, 20, 15, 24, 24],
    "five": [34, 41, 36, 32, 24, 22, 39, 46, 27, 34, 24, 30, 34, 35, 11, 20, 28, 35, 39, 37, 39, 40, 33, 27, 27, 20, 35, 36, 24, 24, 26, 39],
    "six": [35, 47, 38, 40, 35, 29, 43, 47, 39, 35, 35, 34, 30, 42, 25, 24, 29, 42, 40, 40, 47, 46, 45, 36, 36, 25, 36, 40, 25, 40, 41, 43],
    "seven": [38, 48, 44, 42, 36, 45, 44, 48, 42, 43, 42, 43, 42, 43, 34, 30, 38, 46, 41, 45, 49, 47, 47, 37, 37, 49, 42, 49, 50, 43, 44, 48]
}


"""

one to decrease below 6

two is likely to decrease below 10
    
three to increase below 24
    
four will increase above 30 
 
5, 6, 7 slight increase 

bonus: common middle, common high or common low


1    9    
2    6
5    7

"""


#df = pd.DataFrame(numbers.items(), columns=['1', '2', '3', '4', '5', '6', '7'])

df = pd.DataFrame(numbers)


strat_limit = {
    "one":      ["lt",   6],
    "two":      ["lt",  10],
    "three":    ["gtl", 24],
    "four":     ["gt",  30],
    "five":     ["e",   39],
    "six":      ["e",   43],
    "seven":    ["e",   48]
}
for col in df:
    
    print(col)
    
    highest_counts = 3
    high_counts = df[col].value_counts()
    
    i = 0
    for item in high_counts.iteritems():
        if(i <= highest_counts): 
            likley_number = int(item[0])
            
            print(likley_number)
            
            rule = strat_limit[col]
            if(likley_number )
            
        i += 1





