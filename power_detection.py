import serial
import os
import datetime
from database import db, time_now
from time import sleep

def update(msg):
    test_id = datetime.datetime.today().strftime("%Y%m%d%H%M%S")
    data = dict()

    # add some data
    data['test_id'] = str(test_id)
    data['time'] = time_now()
    data['status'] = msg
    # print(data)

    ret = db.table('powerstate').insert(data)
    # print(ret)
    assert ret['errors'] == 0
    return ret

def countdown(time, power):
    for secs in range(int(time), 0, -1):
        if power:
            print('power on:', secs, end=' \r')
        else:
            print('power off:', secs, end=' \r')
        sleep(1)

# ==============================Main=====================================
 
db.setup()
serial_port = '/dev/Arduino_relay'
serial_boudrate = 9600
ser = serial.Serial(serial_port, serial_boudrate)  

preState = False
currentState = False
is_set = False
count = 0
power_on_time = 0
power_off_time = 0
try:  
    while (True):
        data = ser.readline().decode('utf-8')
        data = data.replace('\r','').replace('\n','')
        # print(data)
        preState = currentState
        time = datetime.datetime.now()
        if 'power on' in data:
            # print(data + str(time))
            update('power on')
            countdown(power_on_time, True)
            currentState = True
        elif 'power off' in data:
            # print(data + str(time))
            update('power off')
            countdown(power_off_time, False)
            currentState = False
        elif "value_Time_On" in data:
            power_on_time = data.split()[1]
        elif "value_Time_Off" in data:
            power_off_time = data.split()[1]
        else:
            pass

        if(power_on_time is not 0 and power_off_time is not 0):
            if(not is_set):
                powerTime = dict()
                powerTime['power_on_time'] = power_on_time
                powerTime['power_off_time'] = power_off_time
                rec = db.table('cameraAlive').update(powerTime)
                # print(rec)
                is_set = True

        if(preState and not currentState):
            count += 1
            print("reboot times: " + str(count))
  
except KeyboardInterrupt: 
    ser.close()
