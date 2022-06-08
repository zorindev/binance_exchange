

import sys
import requests
import time
import datetime


def run(args):
    """
    run
    """
    
    sleep_period_small = 3
    sleep_period_large = 120
    urls = ['https://thefirstglance.ca/meet-our-medical-aesthetics-team/', 'https://thefirstglance.ca/', 'https://thefirstglance.ca/breast-augmentation/']
    
    zexit = False
    while(zexit == False):
        for url in urls:
            
            response = requests.get(url)
            
            if(response.status_code != 200):
                
                print(datetime.datetime.now())
                print("SCREAM")
                zexit = True
                break
            
            else:
                print(datetime.datetime.now())
                print(" 200 ")
                print(response.elapsed.total_seconds())
                
            print(" ... ")
            time.sleep(sleep_period_small)
            
        print("done cycle")
        time.sleep(sleep_period_large)




if __name__ == "__main__":
    """
    main
    """
    run(sys.argv)