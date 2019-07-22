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
        fps_time = 0
        while True:
            try:
                time.sleep(0.05)
                ret_val, image = cam.read()
                resized = helper.resizeImage(image,30)
                helper.sendPayload(self.socket,resized)
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
        recv_index=0
        while True:
            try:
                processed_img = helper.receievePayloadPickled(self.socket)
                # processed_img = helper.resizeImage(processed_img)
                q.put(processed_img)
            except Exception as e:
                print(e)
                break

def processImage():
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
        
        print("Rendering processed images....")
        while True:
            if not q.empty():
                processed_img = q.get()
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
