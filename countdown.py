from time import sleep

from time import sleep

print('Starting...')
sleep(1)

for secs in range(10, 0, -1):
    # print(secs)
    print('Time remaining:', secs, end=' \r')
    sleep(1)

