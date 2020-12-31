from __future__ import print_function
from __future__ import division
from shutil import copyfile
from tqdm import tqdm
from skimage.io import imread
from skimage.metrics import structural_similarity
from loggingConfig import LOGGING
from colors import colors
import os
import cv2 as cv
import datetime
import argparse
import fnmatch
import logging
import inspect
import math
import matplotlib.pyplot as plt 
# ==============================================================================================
parser = argparse.ArgumentParser(description='Code for black screen detection.')
parser.add_argument('-d','--debug', help='Debug message',action='store_true')
parser.add_argument('-dl','--debugLevel', help='Debug message level',type=int, default='1')
parser.add_argument('-p','--path', help='Image path' )
args = parser.parse_args()

filePath = os.path.abspath('/home/jhtrd/auto_test/blackScreen/chimera/')
imagePath = os.path.abspath("/home/jhtrd/auto_test/photo_web/" + args.path)

# currentFile = inspect.getfile(inspect.currentframe()).split(".")[0]
currentFile =  __file__.split('/')[-1].split('.')[0]

if not os.path.exists(filePath + "/log/"):
    os.makedirs(filePath + "/log/")
logFileDate = datetime.datetime.now()
LOGGING['handlers']['debug']['filename'] = logFileDate.strftime(filePath + '/log/' + currentFile + '_%m_%d_%H_%M_%S.log')
LOGGING['handlers']['error']['filename'] = logFileDate.strftime(filePath + '/log/' + currentFile + '_error_%m_%d_%H_%M_%S.log')

logging.config.dictConfig(config=LOGGING)
log_c = logging.getLogger('console')
log_d = logging.getLogger('DebugLogger')
log_e = logging.getLogger('ErrorLogger')

fileList = os.listdir(imagePath)
fileList.sort()

# ==============================================================================================

def logi(message):
    log_c.info(str(message))
    log_d.info(str(message))

def logd(message):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logMsg = calframe[1][3] + '(): ' + str(message)
    log_d.debug(logMsg)

def loge(message):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    logMsg = calframe[1][3] + '(): ' + str(message)
    # log_c.error(logMsg)
    log_d.error(logMsg)
    log_e.error(logMsg)
# ==============================================================================================

def getMailreceiver():
    mailListFile = open("/home/jhtrd/auto_test/blackScreen/mailList")
    mailList = mailListFile.readlines()
    receiver = ""
    for user in mailList:
        if "#" not in user:
            receiver += user.replace("\n"," ")
    return receiver
# ==============================================================================================
def createMailText(errorList, totalTimes, endTime):
    mailMsg = []
    mailTitle = ["To: " + getMailreceiver() + "\n", "From: jhtrd01@gmail.com\n", "Subject: Chimera Black Screen Test Result\n\n", "Hi All, \n\n"]
    if len(errorList) is not 0:
        mailMsg.append("Error List:\n")
        for error in errorList:
            mailMsg.append(error)
    else:
        mailMsg.append("No error happened.")

    mailMsg.append("\n\n" + str(fileNameParse(fileList[0])) + " ~ " + str(fileNameParse(fileList[-1])) + "   " + str(fileNameParse(fileList[-1]) - fileNameParse(fileList[0])) + "\n")
    mailMsg.extend(["Error happened " + str(len(errorList)) + " times.\n", "Total reboot " + totalTimes + " times.\n\n"])
    mailMsg.extend(["This is daily mail for chimera black screen test.\n", str(endTime.strftime("%Y-%m-%d %H:%M:%S")), "\n"])

    if not os.path.exists(filePath + "/result"):
        os.makedirs(filePath + "/result")
    date = datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
    fileName = filePath + "/result/chimera_blackScreenResult_" + date + ".txt"
    result = open(fileName, "w")
    result.writelines(mailTitle)
    result.writelines(mailMsg)
    result.close()
    os.system("sudo ssmtp " + getMailreceiver() + " < " + fileName)
# ==============================================================================================
def imageRead():
    imageBase = ['black.jpg', 'black2.jpg', 'black3.jpg', 'black_logo.jpg']
    blackSrc = []
    for image in imageBase:
            blacksrc = cv.imread(filePath + '/' + image)
            blackSrc.append(blacksrc) 
            if blacksrc is None:
                loge(filePath + '/' +image + " could not open or find the images!")
                exit(0)
    return blackSrc
# ==============================================================================================
def comparison(file):

    blackSrc = imageRead()
    src = cv.imread(imagePath + "/" + file)

    black = cv.cvtColor(blackSrc[0], cv.COLOR_BGR2GRAY)
    black2 = cv.cvtColor(blackSrc[1], cv.COLOR_BGR2GRAY)
    photoSrc = cv.cvtColor(src, cv.COLOR_BGR2GRAY)

    comparisonResult = None

    (score, diff) = structural_similarity(black, photoSrc, full=True)
    (score2, diff) = structural_similarity(black2, photoSrc, full=True)

    if score > 0.7 or score2 > 0.7:
        comparisonResult = "black"
    else:
        comparisonResult = "white"

    logd(str(file).split('.')[0] + " " + comparisonResult + " SSIM: " + format(score) + " / " + format(score2))

    return comparisonResult
# ==============================================================================================
def fileNameParse(file):
    timeStamp = str(file)[:14]
    timeStamp = timeStamp.split('_')
    timeStamp = datetime.datetime(datetime.datetime.today().year, int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]), int(timeStamp[3]), int(timeStamp[4]))
    return timeStamp
# ==============================================================================================
def copyErrorToPhoto(errorPhotoList):
    errorFilePath = filePath + "/error/" + logFileDate.strftime('_%Y_%m_%d_%H_%M_%S')
    col = 10
    row = math.ceil(len(errorPhotoList)/col)
    imageWidth = 0
    imageHeight = 0
    i = 1

    fig = plt.figure()

    for photo in errorPhotoList:

        img = cv.imread(imagePath + "/" + photo)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        imageWidth = img.shape[1]
        imageHeight = img.shape[0]

        plt.subplot(row,col,i)
        plt.title(str(photo), y=-0.3)
        plt.imshow(img)
        plt.xticks([])
        plt.yticks([])
        i +=1

    fig.tight_layout()
    fig.set_size_inches(imageWidth*col/200 + 5.5, imageHeight*row/200 + row * 0.5)

    if not os.path.exists(errorFilePath):
        os.makedirs(errorFilePath)

    plt.savefig(errorFilePath + "/" + str(errorPhotoList[0]), bbox_inches='tight',dpi=80)

# ==============================================================================================
def fileSort():
    photoList = []
    tempList = []
    for file in fileList:
        if(file.endswith('jpg')):
            if fnmatch.fnmatch(file, '*_on.jpg'):
                if len(tempList) is not 0:
                    photoList.append(tempList)
                    tempList = []
                tempList.append(file)
            else:
                tempList.append(file)
    if tempList is not 0:
        photoList.append(tempList)
        tempList = []
    return photoList
# ======================================= Main =================================================       
preImage = 'a'
currentImage = 'b'
firstTime = None
timeStamp = None
finalTime = None
errorList = []
count = None

if __name__ == '__main__':

    photoList = fileSort()
    startTime = datetime.datetime.now()
    
    for comparisonList in tqdm(photoList):

        firstTime = fileNameParse(comparisonList[0])
        finalTime = fileNameParse(comparisonList[-1])
        for photo in comparisonList:
            count = 0
            preImage = currentImage
            currentImage = comparison(photo)

            if(preImage == "black" and currentImage == 'white'):
                timeStamp = fileNameParse(photo)

            if(firstTime != None and timeStamp != None):
                count = (timeStamp - firstTime).seconds

                if(count > 60 or count < 40):
                    loge(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + " Error happened")
                    errorList.append(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + "\n")
                    copyErrorToPhoto(comparisonList)
                else:
                    logd(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count))
                
                timeStamp = None
                break;
        if count is 0:
            loge(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + " Error happened")
            errorList.append(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + "\n")

    for error in errorList:
        print(error) 

    endTime = datetime.datetime.now()
    serviceTime = ((endTime - startTime).seconds)
    print(colors.fg.lightblue, "Total File: " + str(len(fileList)))
    print(colors.fg.lightblue, "Service Time: " + str(serviceTime) + " Sec")
    print(colors.fg.lightred, "Error happened " + str(len(errorList)) + " times")
    print(colors.fg.lightred, "Reboot " + str(len(photoList)) + " times.")
    print(colors.reset)
    logd("Error happened " + str(len(errorList)) + " times.  " + "Total reboot " + str(len(photoList)) + " times.")
    createMailText(errorList, str(len(photoList)), endTime)

                

        