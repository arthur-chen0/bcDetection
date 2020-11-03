from __future__ import print_function
from __future__ import division
from shutil import copyfile
import os
import cv2 as cv
import numpy as np
import datetime
import sys
import smtplib
import argparse
# ==============================================================================================
parser = argparse.ArgumentParser(description='Code for black screen detection.')
parser.add_argument('-d','--debug', help='Debug message',action='store_true')
parser.add_argument('-dl','--debugLevel', help='Debug message level',type=int, default='1')
parser.add_argument('-p','--path', help='Image path' )
args = parser.parse_args()
# ==============================================================================================
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
# ==============================================================================================
mailListFile = open("/home/jhtrd/auto_test/blackScreen/mailList")
mailList = mailListFile.readlines()
receiver = ""
for user in mailList:
    if "#" not in user:
        receiver += user.replace("\n"," ")

filePath = os.path.abspath('/home/jhtrd/auto_test/blackScreen/600e/')
mailTitle = ["To: " + receiver + "\n", "From: jhtrd01@gmail.com\n", "Subject: Black Screen Test Result\n\n", "Hi All, \n\n"]
def createMailText(msg):
    date = datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
    fileName = filePath + "/result/600E_blackScreenResult_" + date + ".txt"
    result = open(fileName, "w")
    result.writelines(mailTitle)
    result.writelines(msg)
    result.close()
    # os.system("sudo ssmtp arthurchen@johnsonfitness.com < " + fileName)
    # os.system("sudo ssmtp " + receiver + " < blackScreenResult.txt")
# ==============================================================================================
imagePath = os.path.abspath(args.path)
imageBase = ['black.jpg','black2.jpg','black3.jpg']
blackSrc = []
fileList = os.listdir(imagePath)
fileList.sort()

for image in imageBase:
        blacksrc = cv.imread(filePath + '/' + image)
        blackSrc.append(blacksrc) 
        if blacksrc is None:
            print(filePath + '/' +image + " could not open or find the images!")
            exit(0)

def comparison(file):

    src = cv.imread(imagePath + "/" + file)

    base_black = histogram_Comparison(blackSrc[0], src, 0)
    base_black2 = histogram_Comparison(blackSrc[1], src, 0)
    base_black3 = histogram_Comparison(blackSrc[2], src, 0)
    # base_black_logo = histogram_Comparison(blackSrc[2], src, 0)

    # print(file + " is " + str(base_black4))

    comparisonResult = None

    # if(base_black > 0.55 or base_black2 > 0.55 or base_black3 > 0.7):
    if(base_black > 0.55 or base_black2 > 0.55):
        comparisonResult = "black"
    else:
        comparisonResult = "white"

        # if(base_black_logo > 0.5):
        #     comparisonResult = "black"
        # elif(base_black < -0.0009):
        #     comparisonResult = "black"

    if(args.debug and args.debugLevel >= 2):
        print(colors.fg.lightgrey,file + " is " + comparisonResult + "  " + str(base_black) + " / " + str(base_black2))

    return comparisonResult
# ==============================================================================================
def histogram_Comparison(p1,p2,method):
    hsv_p1 = cv.cvtColor(p1, cv.COLOR_BGR2HSV)
    hsv_p2 = cv.cvtColor(p2, cv.COLOR_BGR2HSV)

    h_bins = 50
    s_bins = 60
    histSize = [h_bins, s_bins]
    # hue varies from 0 to 179, saturation from 0 to 255
    h_ranges = [0, 180]
    s_ranges = [0, 256]
    ranges = h_ranges + s_ranges # concat lists
    # Use the 0-th and 1-st channels
    channels = [0, 1]

    hist_p1 = cv.calcHist([hsv_p1], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist_p1, hist_p1, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    hist_p2 = cv.calcHist([hsv_p2], channels, None, histSize, ranges, accumulate=False)
    cv.normalize(hist_p2, hist_p2, alpha=0, beta=1, norm_type=cv.NORM_MINMAX)

    result = cv.compareHist(hist_p1, hist_p2, method)
    return result
# ==============================================================================================
def fileNameParse(file):
    timeStamp = str(file)[:14]
    timeStamp = timeStamp.split('_')
    timeStamp = datetime.datetime(datetime.datetime.today().year, int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]), int(timeStamp[3]), int(timeStamp[4]))
    return timeStamp
# ==============================================================================================
def copyErrorToFile(list, count):
    path = filePath + "/black_" + str(count)
    if not os.path.exists(path):
        os.makedirs(path)
    for i in range(len(list) - 1):
        copyfile(imagePath + "/" + list[i], path + "/" + list[i])
        # print(list[i])
        # os.remove(errorfileList[i])
# ======================================= Main =================================================        
preImage = 'a'
currentImage = 'b'
timeStamp1 = None
timeStamp2 = None
rebootCount = 0
errorCount = 0
errorfileList = []
mailMsg = ["600E Black Screen Detection Error List:\n"]
startTime = datetime.datetime.now()
for file in fileList:

    if(file.endswith('jpg')):
        preImage = currentImage
        currentImage = comparison(file)
        errorfileList.append(file)

        if(preImage == "white" and currentImage == 'black'):
            rebootCount += 1
            if(timeStamp1 == None):
                timeStamp1 = fileNameParse(file)
            else:
                timeStamp2 = fileNameParse(file)

            if(timeStamp1 != None and timeStamp2 != None):
                count = (timeStamp2 - timeStamp1).seconds
                
                if(count > 65 or count < 10):
                    errorCount += 1
                    print(colors.fg.lightgrey, str(timeStamp1) + " --- " + str(timeStamp2), colors.fg.orange, " Accumulated time: " + str(count), colors.fg.lightred, "-----Something worng, please check with file black_" + str(errorCount))
                    mailMsg.append(str(timeStamp1) + " --- " + str(timeStamp2) + " Accumulated time: " + str(count) + "\n")
                    #copyErrorToFile(errorfileList, errorCount)
                    errorfileList = []
                else:
                    if(args.debug):
                        print(colors.fg.lightgrey, str(timeStamp1) + " --- " + str(timeStamp2), colors.fg.orange, " Accumulated time: " + str(count) )
                
                timeStamp1 = timeStamp2
                timeStamp2 = None

                
                
endTime = datetime.datetime.now()
serviceTime = ((endTime - startTime).seconds)
print(colors.fg.lightblue, "Total File: " + str(len(fileList)))
print(colors.fg.lightblue, "Service Time: " + str(serviceTime) + " Sec")
print(colors.fg.lightred, "Error happened " + str(errorCount) + " times")
print(colors.fg.lightred, "Reboot " + str(rebootCount) + " times.")
print(colors.reset)
mailMsg.extend(["\nError happened " + str(errorCount) + " times\n", "Total reboot " + str(rebootCount) + " times.\n\n"])
mailMsg.extend(["This is daily mail for black screen test.\n", str(endTime.strftime("%Y-%m-%d %H:%M:%S")), "\n"])
createMailText(mailMsg)

                

        