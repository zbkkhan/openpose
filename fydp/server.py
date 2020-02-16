import serverConfig
import handler_op
import socket
import helper
import time
import datetime
import threading
import boto3
import awscredentials
import s3config
import uuid
import queue as Queue
from socket import error as SocketError

BUF_SIZE = 15
q = Queue.Queue(BUF_SIZE)
#setup the S3 bucket
s3_client = boto3.client('s3')

def generate_object_key():
    return ''.join([str(uuid.uuid4().hex[:6]), str(datetime.datetime.now())])

class ReceivingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,conn=None):
        super(ReceivingThread,self).__init__()
        self.target = target
        self.name = name

    def run(self):
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind((serverConfig.hostname, serverConfig.receiving_port))
        s1.listen()
        print("listening on " + serverConfig.hostname + ":" + str(serverConfig.receiving_port))
        while True:
            try:
                conn1, addr1 = s1.accept()
                print("Connected to client!")
                with conn1:
                    while True:
                        if not q.full():
                            image_buffer = helper.receievePayload(conn1)
                            q.put(image_buffer)

                return
            except SocketError as e:
                pass


class ProcessingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,conn=None):
        super(ProcessingThread,self).__init__()
        self.target = target
        self.name = name
        self.frame_count = 0
        self.frame_limit_s3 = 100
        self.file_content = b''

    def run(self):
        print("Trying to connect to server...")
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((serverConfig.hostname, serverConfig.sending_port))
        s2.listen()
        print("requesting on " + serverConfig.hostname + ":" + str(serverConfig.sending_port))
        while True:
            try:
                conn2, addr2 = s2.accept()
                print("Connected to server!")
                with conn2:
                    while True:
                        try:
                            if not q.empty():
                                image_buffer = q.get()
                                # Magic
                                image_data = handler_op.process(image_buffer)
                                # Upload every frame_limit_s3 frames as new S3 object to S3 bucket
                                if self.frame_count < self.frame_limit_s3:
                                    self.file_content += helper.generatePayloadInBytes(image_data['imageWithKeypoints'])
                                    self.file_content += b','
                                    self.frame_count += 1
                                if self.frame_count == self.frame_limit_s3:
                                    # Write series of frames to S3 bucket
                                    s3_client.put_object(Body=self.file_content, Bucket=s3config.bucket_name, Key=generate_object_key())
                                    print("Wrote frames to S3 bucket!")
                                    self.file_content = b''
                                    self.frame_count = 0
                                    # print("Sending payload")
                                helper.sendPayloadPickled(conn2, image_data)
                                # helper.sendImagePayload(conn2, image_data_serialized)
                                # print("Sent payload successfully")
                        except Exception as e:
                            print("Exception while processing")
                            print(e)
                            break
            except SocketError as e:
                pass

def serve():
    try:
        rthread = ReceivingThread(name="receiver")
        rthread.start()
        
        pthread = ProcessingThread(name="processor")
        pthread.start()
        
        rthread.join()
        pthread.join()

    except Exception as e:
        print(e)

serve()
