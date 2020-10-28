from __future__ import print_function
from __future__ import division
import os
import cv2 as cv
import numpy as np
import datetime
import sys

class colors: 
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    class fg: 
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'
    class bg: 
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        orange='\033[43m'
        blue='\033[44m'
        purple='\033[45m'
        cyan='\033[46m'
        lightgrey='\033[47m'

preImage = 'a'
currentImage = 'b'

imagePath = os.path.abspath('/home/jhtrd/auto_test/photo')

fileList = os.listdir(imagePath)
fileList.sort()

def comparison(file):
    
    src_black = cv.imread('/home/jhtrd/auto_test/blackScreen/black2.jpg')
    src_black_logo = cv.imread('/home/jhtrd/auto_test/blackScreen/black_logo.jpg')
    src = cv.imread('/home/jhtrd/auto_test/photo/' + file)

    if src_black is None or src is None:
        print('Could not open or find the images!')
        exit(0)

    hsv_black = cv.cvtColor(src_black, cv.COLOR_BGR2HSV)
    hsv_black_logo = cv.cvtColor(src_black_logo, cv.COLOR_BGR2HSV)
    hsv = cv.cvtColor(src, cv.COLOR_BGR2HSV)

    h_bins = 50
    s_bins = 60
    histSize = [h_bins, s_bins]
    # hue varies from 0 to 179, saturation from 0 to 255
    h_ranges = [0, 180]
    s_ranges = [0, 256]
    ranges = h_ranges + s_ranges # concat lists
    # Use the 0-th and 1-st channels
    channels = [0, 1]

    hist_black = cv.calcHist([hsv_black], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist_black, hist_black, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    hist_black_logo = cv.calcHist([hsv_black_logo], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist_black_logo, hist_black_logo, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
        
    hist = cv.calcHist([hsv], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist, hist, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    base_black = cv.compareHist(hist_black, hist, 0)
    base_black_logo = cv.compareHist(hist_black_logo, hist, 0)
    # print(file + " is " + str(base_black_logo))

    comparisonResult = None

    if(base_black > 0.6):
        comparisonResult = "black"
    else:
        comparisonResult = "white"
        if(base_black_logo > 0.5):
            comparisonResult = "black"
    # print(file + " is " + comparisonResult + "  " + str(base_black) + " / " + str(base_black_logo))

    return comparisonResult
        

timeStamp1 = None
timeStamp2 = None

for file in fileList:

    if(file.endswith('jpg')):
        preImage = currentImage
        currentImage = comparison(file)

        if(preImage == "white" and currentImage == 'black'):
            if(timeStamp1 == None):
                timeStamp1 = str(file)[:14]
                timeStamp1 = timeStamp1.split('_')
                timeStamp1 = datetime.datetime(2020, int(timeStamp1[0]), int(timeStamp1[1]), int(timeStamp1[2]), int(timeStamp1[3]), int(timeStamp1[4]))
            else:
                timeStamp2 = str(file)[:14]
                timeStamp2 = timeStamp2.split('_')
                timeStamp2 = datetime.datetime(2020, int(timeStamp2[0]), int(timeStamp2[1]), int(timeStamp2[2]), int(timeStamp2[3]), int(timeStamp2[4]))

            if(timeStamp1 != None and timeStamp2 != None):
                count = (timeStamp2 - timeStamp1).seconds
                print(colors.fg.lightgrey, str(timeStamp1) + " --- " + str(timeStamp2), colors.fg.orange, " Accumulated time: " + str(count) )
                if(count > 160):
                    print(colors.fg.red, "Something worng-------------------------------------------------------")
                timeStamp1 = timeStamp2
                timeStamp2 = None
print(colors.reset)

                

        