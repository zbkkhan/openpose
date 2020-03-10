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
from webrtc_client import WebRTCVideoClient

# Initialize global variables
s3 = boto3.resource('s3')
BUF_SIZE = 300
q = Queue.Queue(BUF_SIZE)
initializedCorrector = False
squatCorrector = None
frames = []
frame_count = 0
frame_limit_s3 = 150
video_fps = 10
start_time = time.time()

def generate_object_key():
    return ''.join([str(uuid.uuid4().hex[:6]), str(datetime.datetime.now())])

class S3PublishingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None, filename=None):
        super(S3PublishingThread,self).__init__()
        self.target = target
        self.name = name
        self.filename = filename

    def run(self):
        try:
            # Write video to S3 bucket
            s3.meta.client.upload_file(self.filename, s3config.bucket_name, self.filename)
            print("Wrote video {} to S3 Bucket!".format(self.filename))
            # Delete video from filesystem
            os.remove(self.filename)
        except Exception as e:
            print("Error while publishing to S3!")
            print(e)

class SendingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None,conn=None):
        super(SendingThread,self).__init__()
        self.target = target
        self.name = name

    def run(self):
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((serverConfig.hostname, serverConfig.sending_port))
        s2.listen()
        print("requesting on " + serverConfig.hostname + ":" + str(serverConfig.sending_port))
        while True:
            try:
                conn2, addr2 = s2.accept()
                print("Connected to client!")
                with conn2:
                    while True:
                        try:
                            if not q.empty():
                                image_data = q.get()
                                helper.sendPayloadPickled(conn2, image_data)
                        except Exception as e:
                            raise e
            except Exception as e:
                print("Caught exception in SendingThread-------------------")
                print(e)
                s2.close()
                sys.exit()

def receiveVideo(img):
    global initializedCorrector
    global squatCorrector
    global frames
    global frame_count
    global frame_limit_s3
    global video_fps
    global start_time
    # Run openpose keypoint detection
    image_data = handler_op.process(img)
    multi_person_keypoints = image_data['poseKeypoints']
    if multi_person_keypoints.size < 2:
        # Not enough keypoints detected
        return
    
    keypoints = multi_person_keypoints[0]
    print(frame_count)
    # Run core trAIner form correction algorithm
    if initializedCorrector == False:
        print("Successfully set new base values")
        squatCorrector = SquatCorrector(keypoints)
        initializedCorrector = True
    else:
        errors = squatCorrector.corrector(keypoints)
        # add errors to image_data
        image_data['formErrors'] = errors

    # Accumulate frames to save to video later
    if frame_count < frame_limit_s3:
        frames.append(image_data['imageWithKeypoints'])
        frame_count += 1
    # Upload video with frame_limit_s3 frames as new S3 object to S3 bucket
    if frame_count == frame_limit_s3:
        end_time = time.time()
        print("Time taken to gather {} frames: {}s".format(frame_limit_s3, end_time-start_time))
        filename = generate_object_key() + '.mp4'
        # Initialize CV2 Video Writer
        img_height, img_width, img_layers = frames[0].shape
        frame_size = (img_width, img_height)
        video = cv2.VideoWriter(filename , cv2.VideoWriter_fourcc(*'mp4v'), video_fps, frame_size)
        # Compose video from frames array
        for img in frames:
            video.write(img)
        
        # Save video and push to S3 in separate thread
        video.release()
        s3publisher = S3PublishingThread(name="s3publisher", filename=filename)
        s3publisher.start()

        # Cleanup state variables
        frames = []
        frame_count = 0
        start_time = time.time()
    
    q.put(image_data)


def serve():
    global start_time
    try:
        pthread = SendingThread(name="sender")
        pthread.start()

        client = WebRTCVideoClient("ws://eceubuntu4.uwaterloo.ca:10800")
        time.time()
        client.startReceiveVideo(receiveVideo)

        pthread.join()
        
    except KeyboardInterrupt as e2:
        print("Shutting down server...")
    except Exception as e:
        print(e)

serve()
