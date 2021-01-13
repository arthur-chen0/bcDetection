from __future__ import print_function
from __future__ import division
from tqdm import tqdm
from skimage.metrics import structural_similarity
from loggingConfig import LOGGING
from colors import colors
from cameraConfig import config
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from rethinkdb import RethinkDB
import smtplib
import glob
import os
import cv2 as cv
import socket
import datetime
import argparse
import fnmatch
import logging
import inspect
import math
import matplotlib.pyplot as plt

# ==============================================================================================
parser = argparse.ArgumentParser(description='Code for black screen detection.')
parser.add_argument('-m', '--mail', help='if mail the result after image recognition', action='store_true')
parser.add_argument('-r', help='delete the photo after image recognition', action='store_true')
parser.add_argument('-d', '--device', help='use which camera')
args = parser.parse_args()


filePath = os.path.abspath('/home/jhtrd/auto_test/blackScreen/athena/')
imagePath = os.path.abspath("/home/jhtrd/auto_test/photo_web/" + config[args.device]['folder'])

currentFile = __file__.split('/')[-1].split('.')[0]

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

r = RethinkDB()

conn = r.connect(host='localhost', port=28015, db='picamera')

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('google.com', 0))
ipaddr = s.getsockname()[0]

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
    receiver = []
    for user in mailList:
        if "#" not in user:
            receiver.append(user.replace("\n", " "))
    logd('Mail receiver: ' + str(receiver))
    return receiver
# ==============================================================================================

def mailResult(errorList, totalTimes, endTime):
    logd('Mail the result')
    send_user = 'jhtrd01@gmail.com'
    password = 'jhtrd1234'
    receive_users = getMailreceiver()
    subject = 'Chimera Black Screen Test Result'

    msg = MIMEMultipart()
    msg['Subject']=subject
    msg['From']=send_user
    msg['To']=",".join(receive_users)

    email_title = 'Hi All,\n\n'

    if len(errorList) is not 0:
        email_title += ("Error List:\n")
    else:
        email_title += ("No error happened.")

    msg.attach(MIMEText(email_title)) 

    errorPhotoPath = filePath + '/error/' + logFileDate.strftime('%Y_%m_%d_%H_%M_%S')

    errorPhotoList = glob.glob(errorPhotoPath + '/*.jpg')
    errorPhotoList.sort()
    i = 0
    for error in errorList:
        with open(errorPhotoList[i], 'rb') as f:
            msg.attach(MIMEText('\n' + error))
            img_data = f.read()
            img = MIMEImage(img_data)
            img.add_header('Content-ID', 'dns_config') 
            msg.attach(img)
            f.close()
            msg.attach(MIMEText('\n'))
        i += 1

    mailMsg = ""
    mailMsg += ("\n\n" + str(fileNameParse(fileList[0])) + " ~ " + str(fileNameParse(fileList[-1])) + "   " + str(fileNameParse(fileList[-1]) - fileNameParse(fileList[0])) + "\n")
    mailMsg += ("Error happened " + str(len(errorList)) + " times.\n" + "Total reboot " + totalTimes + " times.\n\n")
    mailMsg += ("This is daily mail for chimera black screen test.\n" + str(endTime.strftime("%Y-%m-%d %H:%M:%S")) + "\n")
    msg.attach(MIMEText(mailMsg))

    smtp=smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo() 
    smtp.starttls()
    smtp.login(send_user, password)
    status = smtp.sendmail(send_user, receive_users, msg.as_string())
    if status=={}:
        logd("Send mail success!")
    else:
        loge("Send mail fail!")
    smtp.quit()
# ==============================================================================================
def imageRead():
    imageBase = ['black.jpg', 'black2.jpg', 'black3.jpg', 'black_logo.jpg', 'matrix_logo.jpg']
    blackSrc = []
    for image in imageBase:
        blacksrc = cv.imread(filePath + '/' + image)
        blackSrc.append(blacksrc)
        if blacksrc is None:
            loge(filePath + '/' + image + " could not open or find the images!")
            exit(0)
    return blackSrc
# ==============================================================================================
def comparison(file):
    blackSrc = imageRead()
    src = cv.imread(imagePath + "/" + file)

    black = cv.cvtColor(blackSrc[0], cv.COLOR_BGR2GRAY)
    black2 = cv.cvtColor(blackSrc[1], cv.COLOR_BGR2GRAY)
    mLogo = cv.cvtColor(blackSrc[4],cv.COLOR_BGR2GRAY)
    photoSrc = cv.cvtColor(src, cv.COLOR_BGR2GRAY)

    comparisonResult = None

    (score, diff) = structural_similarity(black, photoSrc, full=True)
    (score2, diff) = structural_similarity(black2, photoSrc, full=True)
    (score3, diff) = structural_similarity(mLogo, photoSrc, full=True)

    if score > 0.7 or score2 > 0.7 or score3 > 0.7:
        comparisonResult = "black"
    else:
        comparisonResult = "white"

    logd(str(file).split('.')[0] + " " + comparisonResult + " SSIM: " + format(score) + " / " + format(score2) + ' / ' + format(score3))

    return comparisonResult
# ==============================================================================================
def fileNameParse(file):
    timeStamp = str(file)[:14]
    timeStamp = timeStamp.split('_')
    timeStamp = datetime.datetime(datetime.datetime.today().year, int(timeStamp[0]), int(timeStamp[1]), int(timeStamp[2]), int(timeStamp[3]), int(timeStamp[4]))
    return timeStamp
# ==============================================================================================
def copyErrorToPhoto(index):
    errorPhotoList = []
    for error in fileList[(index - 20):(index + 20)]:
        errorPhotoList.append(error)

    errorFilePath = filePath + "/error/" + logFileDate.strftime('%Y_%m_%d_%H_%M_%S')
    col = 10
    row = math.ceil(len(errorPhotoList) / col)
    imageWidth = 0
    imageHeight = 0
    i = 1

    fig = plt.figure()

    for photo in errorPhotoList:
        img = cv.imread(imagePath + "/" + photo)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

        imageWidth = img.shape[1]
        imageHeight = img.shape[0]

        plt.subplot(row, col, i)
        plt.title(str(photo).split('.')[0], y=-0.35)
        plt.imshow(img)
        plt.xticks([])
        plt.yticks([])
        i += 1

    fig.tight_layout()
    fig.set_size_inches(imageWidth * col / 500 + 10.5, imageHeight * row / 500 + row * 0.85)  # 10.5 and row * 0.8 is for filname displaying
    if not os.path.exists(errorFilePath):
        os.makedirs(errorFilePath)

    plt.savefig(errorFilePath + "/" + str(fileList[index]), bbox_inches='tight', dpi=40)


# ==============================================================================================
def fileSort():
    photoList = []
    tempList = []
    for file in fileList:
        if file.endswith('jpg'):
            if fnmatch.fnmatch(file, '*_on.jpg'):
                if len(tempList) is not 0:
                    photoList.append(tempList)
                    tempList = []
                tempList.append(file)
            else:
                tempList.append(file)
    # if tempList is not 0:
    #     photoList.append(tempList)
    #     tempList = []
    return photoList

# ==============================================================================================

def deletePhoto(list):
    logd('Delete Photo')
    if len(list) < 40:
        loge('list size is less than 40, return')
        return
    for f in list:
        os.remove(imagePath + "/" + f)
        rec = r.table("photo").filter((r.row['name'] == str(f).split('.')[0]) & (r.row['ip'] == config[args.device]['ip'])).delete().run(conn)
        # logd(rec)

# ======================================= Main =================================================       
preImage = 'a'
currentImage = 'b'
firstTime = None
timeStamp = None
finalTime = None
errorList = []
count = None

if __name__ == '__main__':

    logd(args.device + '  ip: ' + config[args.device]['ip'] + '  Photh folder: ' + str(imagePath))

    photoList = []
    startTime = datetime.datetime.now()

    # for comparisonList in tqdm(photoList):

    #     firstTime = fileNameParse(comparisonList[0])
    #     finalTime = fileNameParse(comparisonList[-1])
        
    #     for photo in comparisonList:
    #         count = 0
    #         preImage = currentImage
    #         currentImage = comparison(photo)

    #         if preImage is "black" and currentImage is 'white':
    #             timeStamp = fileNameParse(photo)

    #         if firstTime is not None and timeStamp is not None:
    #             count = (timeStamp - firstTime).seconds

    #             if count > 60 or count < 40:
    #                 loge(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + " Error happened")
    #                 errorList.append(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + "\n")
    #                 copyErrorToPhoto(comparisonList)
    #             else:
    #                 logd(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count))

    #             timeStamp = None
    #             break;
    #     if count is 0:
    #         loge(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + " Error happened")
    #         errorList.append(str(firstTime) + " - " + str(finalTime) + " Black screen accumulated time: " + str(count) + "\n")
    #         copyErrorToPhoto(comparisonList)
    #     if args.r:
    #         deletePhoto(comparisonList)

    # for error in errorList:
    #     print(error)

    i = 0
    for photo in tqdm(fileList):
        preImage = currentImage
        currentImage = comparison(photo)

        if preImage is "white" and currentImage is 'black':
            # print('error happened')
            errorList.append(photo)
            logd('error happened: ' + str(photo))
            copyErrorToPhoto(i)
        if i < (len(fileList)-1):
            i += 1
    if args.r:
        deletePhoto(fileList)

    for error in errorList:
        print(error)



    endTime = datetime.datetime.now()
    serviceTime = (endTime - startTime).seconds
    print(colors.fg.lightblue, "Total File: " + str(len(fileList)))
    print(colors.fg.lightblue, "Service Time: " + str(serviceTime) + " Sec")
    print(colors.fg.lightred, "Error happened " + str(len(errorList)) + " times")
    print(colors.fg.lightred, "Reboot " + str(len(photoList)) + " times.")
    print(colors.reset)
    logd("Error happened " + str(len(errorList)) + " times.  " + "Total reboot " + str(len(photoList)) + " times.")
    if args.mail:
        mailResult(errorList, str(len(photoList)), endTime)
