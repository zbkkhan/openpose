import cv2
import serverConfig
import time
import helper
import socket
import threading
import queue as Queue

#initialize output queue
BUF_SIZE = 100
q = Queue.Queue(BUF_SIZE)
recv_times=[]

# initialize input stream
cam = cv2.VideoCapture(0)

class SendingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,socket=None):
        super(SendingThread,self).__init__()
        self.target = target
        self.name = name
        self.socket = socket

    def run(self):
        global recv_time
        fps_time = 0
        while True:
            try:
                ret_val, image = cam.read()
                # image = cv2.resize(image, (0,0), fx=0.5, fy=0.5) 
                recv_times.append(time.time())
                helper.sendPayload(self.socket,image)
            except Exception as e:
                print("unable to send payload")
                print(e)
                break
        return

class ReceivingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,socket=None):
        super(ReceivingThread,self).__init__()
        self.target = target
        self.name = name
        self.socket = socket

    def run(self):
        global recv_times
        recv_index=0
        while True:
            try:
                processed_img = helper.receievePayload(self.socket)
                t1 = (time.time() - recv_times[recv_index])
                recv_index+=1
                # print("Time to process: " + str(t1))
                q.put(processed_img)
            except Exception as e:
                print(e)
                break

def processImage():
    # read in image to be processed
    # img = cv2.imread('images/squat1.jpg',cv2.IMREAD_COLOR)
    try:
        print("Trying to connect to server...")
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.connect(("eceubuntu4.uwaterloo.ca", serverConfig.receiving_port))
        print("Connected to server!")
        sthread = SendingThread(name="sender",socket=s1)
        sthread.start()

        time.sleep(3)

        print("Trying to connect to client...")
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect(("eceubuntu4.uwaterloo.ca", serverConfig.sending_port))
        print("Connected to client!")
        rthread = ReceivingThread(name="receiver",socket=s2)
        rthread.start()  
        
        global recv_times
        img_received=0
        print("rendering processed images")
        while True:
            if not q.empty():
                processed_img = q.get()
                height, width, layer = processed_img.shape
                # print((width,height))
                t2 = (time.time() - recv_times[img_received])
                img_received+=1
                if img_received > 200:
                    break
                # print("Rendering duration: " + str(t2))
                cv2.imshow('OPENPOSE estimation result', processed_img)
                if cv2.waitKey(1) == 27:
                    break
        
        cv2.destroyAllWindows()

        sthread.join()
        rthread.join()

    except Exception as e:
        print(e)

if __name__ == "__main__":
    processImage()
