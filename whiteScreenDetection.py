from __future__ import print_function
from __future__ import division
import os
import cv2 as cv
import numpy as np
import datetime

preImage = 'a'
currentImage = 'b'

imagePath = os.path.abspath('/home/jhtrd/auto_test/photo')

fileList = os.listdir(imagePath)
fileList.sort()

def comparison(file):
    src_black = cv.imread('/home/jhtrd/auto_test/blackScreen/white.jpg')
    src = cv.imread('/home/jhtrd/auto_test/photo/' + file)


    # if src_black is None or src is None:
    #     print('Could not open or find the images!')
    #     exit(0)

    hsv_white = cv.cvtColor(src_black, cv.COLOR_BGR2HSV)
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

    hist_white = cv.calcHist([hsv_white], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist_white, hist_white, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)
        
    hist = cv.calcHist([hsv], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist, hist, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    base_white = cv.compareHist(hist_white, hist, 0)
    print(file + " is " + str(base_white))

    if(base_white > 0.65):
        return "white"
    else:
        return "black"

timeStamp1 = None
timeStamp2 = None

for file in fileList:

    if(file.endswith('jpg')):
        preImage = currentImage
        currentImage = comparison(file)
        # print(file + " is " + currentImage)

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
                # print(str(count))
                if(count > 160):
                    print("Something worng-------------------------------------------------------")
                    print("TimeStamp 1 : " + str(timeStamp1) + "  TimeStamp 2 :" + str(timeStamp2))
                timeStamp1 = timeStamp2
                timeStamp2 = None
                

        