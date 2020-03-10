import cv2
import serverConfig
import time
import helper
import socket
import threading
import queue as Queue

#initialize output queue
BUF_SIZE = 300
q = Queue.Queue(BUF_SIZE)

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
                image_data = helper.receievePayloadPickled(self.socket)
                # processed_img = helper.resizeImage(processed_img)
                q.put(image_data)
            except Exception as e:
                print(e)
                break

def processImage():
    try:
        print("Trying to connect to client...")
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect(("eceubuntu4.uwaterloo.ca", serverConfig.sending_port))
        print("Connected to client!")
        rthread = ReceivingThread(name="receiver",socket=s2)
        rthread.start()

        time.sleep(1)

        while True:
            if not q.empty():
                image_data = q.get()
                cv2.namedWindow('OPENPOSE estimation result',cv2.WINDOW_NORMAL)
                cv2.resizeWindow('OPENPOSE estimation result', 600,600)
                cv2.imshow('OPENPOSE estimation result', image_data['imageWithKeypoints'])
                if cv2.waitKey(1) == 27:
                    break
        
        cv2.destroyAllWindows()
        
        rthread.join()

    except Exception as e:
        print(e)

if __name__ == "__main__":
    setNewBaseValues = False
    processImage()
