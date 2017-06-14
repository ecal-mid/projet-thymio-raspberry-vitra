# Thymio Vitra RaspberryPi v1
# Handle SocketServer, GPIO and Logfile

import socket
import threading
import SocketServer
import time
import RPi.GPIO as GPIO
import logging
import datetime
host = '10.11.11.35'  # ip of raspberry pi
port = 4500

# Relay
mode = 1
chargingTime = 0  # 60 in sec
offTime = 0  # relay_pin0
running = 1
relay_pin = 7
GPIO.setmode(GPIO.BOARD)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.HIGH)
charging = 0
elapsed = 0
running = 1
remaining = 0

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global mode
        global charging
        global chargingTime
        global offTime
        global remaining

        data = self.request.recv(1024)
        data = data[:-1]
        #cur_thread = threading.current_thread()
        #response = "{}: {}".format(cur_thread.name, data)
        response = data+"OK\r"
        print (data)
        logging.debug(getTime() + "DATA | "+data)
        if data == 'STOP':
            mode = 0
            print "MODE is now 0 NIGHT"
            logging.debug(getTime()+"DATA | MODE is now 0 NIGHT")
            resetMode()
        elif data == 'NORMAL':
            mode = 1
            print "MODE is now 1 DAY NORMAL"
            logging.debug(getTime()+"DATA | MODE is now 1 DAY NORMAL")
            resetMode()
        elif data == 'LOW':
            mode = 2
            print "MODE is now 2 DAY LOW"
            logging.debug(getTime()+"DATA | MODE is now 2 DAY LOW")
            resetMode()

        elif data == 'HIGH':
            mode = 3
            print "MODE is now 3 DAY HIGH"
            logging.debug(getTime()+"DATA | MODE is now 3 DAY HIGH")
            resetMode()
        elif data == 'STAT':
            print "STAT"
            response = data + "| Charging " + str(charging)+ "| Remaining " + str(remaining)+" | Mode " + str(mode) +" | chargingTime = "+str(chargingTime)+" | offTime = "+str(offTime)+" | OK\r"
            logging.debug(getTime()+"DATA | STAT SENT")

        else:
            print "UNKNOWN COMMAND"
            logging.debug(getTime()+"DATA | UNKNOWN COMMAND")
        self.request.sendall(response)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def getTime():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return str(st)+"   "

def getDay():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return str(st)


def resetMode():
    global elapsed
    global charging
    global chargingTime
    global offTime
    global mode
    global remaining
    print "MODE HAS CHANGED TO MODE "+str(mode)

    if mode == 0: #NIGHT
        chargingTime = 2000 #200
        offTime = 0
    elif mode == 1: #NORMAL
        chargingTime = 240
        offTime = 200
    elif mode == 2: #LOW
        chargingTime = 500 #500
        offTime = 200
    elif mode == 3: #HIGH
        chargingTime = 200
        offTime = 480 #300
    print "chargingTime = "+str(chargingTime)
    print "offTime = " + str(offTime)
    logging.debug(getTime() + "MODE | CHANGED TO MODE " + str(mode) +" | chargingTime = "+str(chargingTime)+" | offTime = "+str(offTime))
    elapsed = 0
    charging = 0
    remaining = 0
    GPIO.output(relay_pin, GPIO.HIGH)
    print "LOOP RESTARTED"



def client(ip, port, message):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024)
        print "Received: {}".format(response)
    finally:
        sock.close()


if __name__ == "__main__":

    LOG_FILENAME = 'ThymioDebug_'+getDay()+'.log'
    logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
    logging.debug(getTime() + "---------------------------------------------------------")
    logging.debug(getTime()+"Thymio Vitra Exhibition Session Started")
    logging.debug(getTime() + "---------------------------------------------------------")

    #hostname = socket.gethostname()


    server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name
    logging.debug(getTime()+"SERV | Server loop running in thread:" + str(server_thread.name))



    resetMode()

    while running == 1:

        try :


            if charging == 1:
                if elapsed < chargingTime:
                    print "POWE  "+str(chargingTime - elapsed)
                    remaining = chargingTime - elapsed

                    time.sleep(1)
                else:
                    if (offTime > 0):
                        elapsed = 0
                        charging = 0
                        GPIO.output(relay_pin, GPIO.HIGH)
                        print "OFF"
                        logging.debug(getTime() + "POWE | CHARGING OFF")
                    else:
                        logging.debug(getTime() + "POWE | ONLY CHARGING NOW")
                        print "ONLY CHARGING NOW"
                        elapsed = 0

            elif charging == 0:
                if(offTime  > 0):
                    if elapsed < offTime:
                        print "OFF  "+str(offTime - elapsed)
                        remaining = offTime - elapsed
                        time.sleep(1)
                    else:
                        elapsed = 0
                        charging = 1
                        GPIO.output(relay_pin, GPIO.LOW)
                        print "CHARGE"
                        logging.debug(getTime() + "POWE | CHARGING ON")
                else :
                    logging.debug(getTime() + "POWE | ONLY CHARGING NOW")
                    print "ONLY CHARGING NOW"
                    charging = 1
                    GPIO.output(relay_pin, GPIO.LOW)
                    print "CHARGE"
                    logging.debug(getTime() + "POWE | CHARGING ON")
            elapsed += 1
        except KeyboardInterrupt:
            running = 0
            print " QUIT"
            logging.debug(getTime() + "QUIT | Session ended because of KeyboardInterrupt")
            logging.debug(getTime() + "---------------------------------------------------------")
            GPIO.cleanup()
            server.shutdown()
            server.server_close()




