#!/usr/bin/env python

# WS client example

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
import asyncio
import websockets
import json
import cv2
import av
import PIL
import numpy

BYE = object()

class WebRTCVideoClient:

    def __init__(self, signalingClientURI="ws://localhost:8080"):
        self.uri = signalingClientURI  # example: "ws://10.36.112.207:8080"

    """
    The callback here is utilized for sending the received video frames from the remote device to the caller
    The video frames are numpy arrays of pixels
    These video frames are sent by as the first argument in the callback
    callback(img: Numpy[]) 
    
    **Usage**
        client = WebRTCVideoClient("ws://172.16.42.196:8080")
        def videoRetrieval(img):
            print("vidret: ", img)
        client.startReceiveVideo(videoRetrieval)
    """

    def startReceiveVideo(self, callback):
        pc = RTCPeerConnection()

        coro = self.__run_answer(pc, callback)
        # run event loop
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(coro)
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(pc.close())

    def __channel_log(self, channel, t, message):
        print("channel(%s) %s %s" % (channel.label, t, message))

    def __channel_send(self, channel, message):
        self.__channel_log(channel, ">", message)
        channel.send(message)

    async def __consume_signaling(self, pc):
        async with websockets.connect(self.uri) as websocket:
            while True:
                obj = await websocket.recv()
                # print("offer type: ", type(obj))
                obj = self.__decodeObject(obj)

                if isinstance(obj, RTCSessionDescription):
                    # print(obj)
                    await pc.setRemoteDescription(obj)

                    if obj.type == "offer":
                        # send answer
                        await pc.setLocalDescription(await pc.createAnswer())

                        print("answer type: ", type(self.__encodeObject(pc.localDescription)))
                        await websocket.send(self.__encodeObject(pc.localDescription))
                elif isinstance(obj, RTCIceCandidate):
                    # print(obj)
                    pc.addIceCandidate(obj)
                elif obj is BYE:
                    print("Exiting")
                    break

    def __encodeObject(self, obj):
        if isinstance(obj, RTCSessionDescription):
            x = {"payload": {"sdp": obj.sdp, "type": obj.type}, "type": "SessionDescription"}
            return str.encode(json.dumps(x))
        else:
            print("ERROR: Invalid object being encoded")

    def __decodeObject(self, obj):
        data = json.loads(obj)
        # print(data["type"])
        if data["type"] == "SessionDescription":
            return RTCSessionDescription(sdp=data["payload"]["sdp"], type=data["payload"]['type'])
        if data["type"] == "IceCandidate":
            # sdp data
            sdp = data["payload"]["sdp"]
            sdp = sdp.split(" ")
            component = int(sdp[1])
            foundation = sdp[0].split(":")[1]
            ip = sdp[4]
            port = int(sdp[5])
            priority = int(sdp[3])
            protocol = sdp[2]
            type_val = sdp[7]

            # misc data
            sdpMLineIndex = int(data["payload"]["sdpMLineIndex"])
            sdpMid = data["payload"]["sdpMid"]
            return RTCIceCandidate(component=component,
                                   foundation=foundation,
                                   ip=ip,
                                   port=port,
                                   priority=priority,
                                   protocol=protocol,
                                   type=type_val,
                                   sdpMLineIndex=sdpMLineIndex,
                                   sdpMid=sdpMid)



        else:
            print("ERROR: Invalid object being decoded")

    async def __run_answer(self, pc, callback):

        @pc.on("datachannel")
        def on_datachannel(channel):
            self.__channel_log(channel, "-", "created by remote party")

            @channel.on("message")
            def on_message(message):
                print(type(message))

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print("ICE connection state is %s", pc.iceConnectionState)
            if pc.iceConnectionState == "failed":
                await pc.close()

        @pc.on("addstream")
        def on_add_stream(stream):
            print("stream", type(stream))

        @pc.on("track")
        def on_track(track):
            print("Receiving %s" % track.kind)
            # Only tracking the video frames
            if track.kind == "video":
                asyncio.ensure_future(self.__run_track(track, callback))

            @track.on("ended")
            async def on_ended():
                print("ended")

        await self.__consume_signaling(pc)

    def __convert_pil_image_to_opencv_image(self, pil_image):
        open_cv_image = numpy.array(pil_image)
        # Convert RGB to BGR
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        return open_cv_image

    async def __run_track(self, track, callback):
        while True:
            frame = await track.recv()
            if isinstance(frame, av.video.frame.VideoFrame):
                img = self.__convert_pil_image_to_opencv_image(frame.to_image())
                # cv2.imshow("Video track", img)
                callback(img)