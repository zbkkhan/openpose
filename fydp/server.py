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
import sys
import cv2
import os
import queue as Queue
import numpy as np
from socket import error as SocketError
from corrector import SquatCorrector, DeadliftCorrector

BUF_SIZE = 15
q = Queue.Queue(BUF_SIZE)
#setup the S3 bucket
s3 = boto3.resource('s3')

def generate_object_key():
    return ''.join([str(uuid.uuid4().hex[:6]), str(datetime.datetime.now())])

class ReceivingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,conn=None):
        super(ReceivingThread,self).__init__()
        self.target = target
        self.name = name
        self.socketref = None

    def run(self):
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind((serverConfig.hostname, serverConfig.receiving_port))
        s1.listen()
        self.socketref = s1
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
            except Exception as e:
                print("Caught exception in ReceivingThread-----------")
                print(e)
                s1.close()
                sys.exit()

class ProcessingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,conn=None):
        super(ProcessingThread,self).__init__()
        self.target = target
        self.name = name
        self.frame_count = 0
        self.frame_limit_s3 = 100
        self.frames = []

    def run(self):
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((serverConfig.hostname, serverConfig.sending_port))
        s2.listen()
        print("requesting on " + serverConfig.hostname + ":" + str(serverConfig.sending_port))
        while True:
            try:
                conn2, addr2 = s2.accept()
                print("Connected to server!")
                with conn2:
                    squatCorrector = None
                    initializedCorrector = False
                    while True:
                        try:
                            if not q.empty():
                                image_buffer = q.get()
                                # Run openpose keypoint detection
                                image_data = handler_op.process(image_buffer)

                                multi_person_keypoints = image_data['poseKeypoints']
                                if multi_person_keypoints.size < 2:
                                    #not enough keypoints detected
                                    continue
                                
                                keypoints = multi_person_keypoints[0]

                                # Run core trAIner form correction algorithm
                                if initializedCorrector == False:
                                    print("Successfully set new base values")
                                    squatCorrector = SquatCorrector(keypoints)
                                    initializedCorrector = True
                                else:
                                    errors = squatCorrector.corrector(keypoints)
                                    print(errors)
                                    # add errors to image_data
                                    image_data['formErrors'] = errors

                                # Accumulate frames to save to video later
                                if self.frame_count < self.frame_limit_s3:
                                    self.frames.append(image_data['imageWithKeypoints'])
                                    self.frame_count += 1
                                # Upload video with frame_limit_s3 frames as new S3 object to S3 bucket
                                if self.frame_count == self.frame_limit_s3:
                                    filename = generate_object_key() + '.mp4'
                                    # Initialize CV2 Video Writer
                                    img_height, img_width, img_layers = self.frames[0].shape
                                    frame_size = (img_width, img_height)
                                    video = cv2.VideoWriter(filename , cv2.VideoWriter_fourcc(*'mp4v'), 10.0, frame_size)
                                    # Compose video from frames array
                                    for img in self.frames:
                                        video.write(img)
                                    # Write video to file
                                    video.release()
                                    # Write video to S3 bucket
                                    s3.meta.client.upload_file(filename, s3config.bucket_name, filename)
                                    print("Wrote video to S3 Bucket!")
                                    # Delete video from filesystem
                                    os.remove(filename)
                                    # Cleanup state variables
                                    self.frames = []
                                    self.frame_count = 0

                                # print("Sending payload")
                                helper.sendPayloadPickled(conn2, image_data)
                        except Exception as e:
                            raise e
            except Exception as e:
                print("Caught exception in ProcessingThread-------------------")
                print(e)
                s2.close()
                sys.exit()

def serve():
    while True:
        try:
            print("Trying to connect to client...")
            rthread = ReceivingThread(name="receiver")
            rthread.start()
            
            pthread = ProcessingThread(name="processor")
            pthread.start()
            
            rthread.join()
            pthread.join()
        except SystemExit as e1:
            print("Socked connections with client terminated...")
        except KeyboardInterrupt as e2:
            print("Shutting down server...")
            break

serve()
