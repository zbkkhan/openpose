# Set of helper functions for trAIner
import cv2
import base64
import numpy as np
import serverConfig
import matplotlib.pyplot as plt
import pickle

def generatePayload(img):
    '''
    img: numpy array (input from cv2)
    returns serialized utf-8 string of base64 encoded image to send over HTTP
    '''
    # create jpg image buffer
    buffer = cv2.imencode('.jpg', img)[1]

    # encode image buffer as base64
    img_encoded = base64.b64encode(buffer)

    # serialized binary into string for json payload over HTTP
    payload = img_encoded.decode("utf-8")
    return payload

def generatePayloadInBytes(img):
    '''
    img: numpy array (input from cv2)
    returns base64 encoded image in binary to send over HTTP
    '''
    # create jpg image buffer
    buffer = cv2.imencode('.jpg', img)[1]

    # encode image buffer as base64
    img_encoded = base64.b64encode(buffer)

    return img_encoded


def decodeBinaryData(binarydata):
    '''
    response: base64 binary data representing final jpg image
    returns numpy array of processed image with estimation
    '''
    # decode base64 image data into regular binary data
    jpg_decoded = base64.b64decode(binarydata)

    # extract jpg array from binary image data
    jpg_as_np = np.frombuffer(jpg_decoded, dtype=np.uint8); 

    # decode jpg array 
    processed_img = cv2.imdecode(jpg_as_np,-1)
    return processed_img

def showImage(img,heading="Result"):
    '''
    displays input image (numpy array) on matlab plot
    '''
    fig = plt.figure()
    a = fig.add_subplot(2, 2, 1)
    a.set_title(heading)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.show()


def sendPayloadPickled(s, payload):
    '''
    sends the pickled payload over the socket connection s after synchronizing and packing
    '''

    payload['imageWithKeypoints'] = generatePayloadInBytes(payload['imageWithKeypoints'])
    payload = pickle.dumps(payload)
    payload_size = len(payload)
    # print("Payload size:")
    # print(payload_size)

    initial_payload = bytes(str(payload_size),'utf-8')

    s.sendall(initial_payload)
    res = s.recv(serverConfig.buffer_size)
    # print("PAYLOAD SIZE ACK:")
    # print(res)

    # print("payload sent:")
    # print(payload)
    s.sendall(payload)
    res2 = s.recv(serverConfig.buffer_size)
    # print("PAYLOAD RECEIVED ACK:")
    # print(res2)


def sendPayload(s,img):
    '''
    sends the image (img) payload over the socket connection s after synchronizing and packing
    '''
    payload = generatePayloadInBytes(img)
    payload_size = len(payload)
    # print("Payload size:")
    # print(payload_size)

    initial_payload = bytes(str(payload_size),'utf-8')
    
    s.sendall(initial_payload)
    res = s.recv(serverConfig.buffer_size)
    # print("PAYLOAD SIZE ACK:")
    # print(res)

    # print("payload sent:")
    # print(payload)
    s.sendall(payload)
    res2 = s.recv(serverConfig.buffer_size)
    # print("PAYLOAD RECEIVED ACK:")
    # print(res2)


def resizeImage(image,sc_percent=100):
    '''
    :param image:
    :param sc_percent: desired percentage to scale input image by
    :return: resized image
    '''
    # percent of original size
    scale_percent = sc_percent

    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return resized


def receievePayloadPickled(conn):
    '''
    returns binary data
    '''
    #get payload size
    size_b = conn.recv(serverConfig.buffer_size)
    payload_size = int(size_b.decode('utf-8'))
    # print("Input Payload size:")
    # print(payload_size)
    conn.sendall(bytes("Server received payload size",'utf-8'))

    #initialize receiving params
    curr_size = 0
    byte_data = b''

    while True:
        # print("building frame from chunks...")
        data = conn.recv(serverConfig.buffer_size)
        byte_data += data
        curr_size += len(data)

        if curr_size == payload_size:
            #receieved image successfully
            # Demistify request data
            conn.sendall(bytes("Server received image",'utf-8'))
            image_data = pickle.loads(byte_data)

            '''
            image_data contains keys 'imageWithKeypoints' and 'poseKeypoints'
            '''
            image_data['imageWithKeypoints'] = decodeBinaryData(image_data['imageWithKeypoints'])
            # print("payload received:")
            # print(image_buffer)

            return image_data['imageWithKeypoints']
        if curr_size > payload_size:
            print("ERROR PARSING DATA")



def receievePayload(conn):
    '''
    returns binary data
    '''
    #get payload size
    size_b = conn.recv(serverConfig.buffer_size)
    payload_size = int(size_b.decode('utf-8'))
    # print("Input Payload size:")
    # print(payload_size)
    conn.sendall(bytes("Server received payload size",'utf-8'))

    #initialize receiving params
    curr_size = 0
    img_data = b''

    while True:
        # print("building frame from chunks...")
        data = conn.recv(serverConfig.buffer_size)
        img_data+=data
        curr_size+=len(data)
        
        if curr_size == payload_size:
            #receieved image successfully
            # Demistify request data
            conn.sendall(bytes("Server received image",'utf-8'))
            binarydata = img_data
            image_buffer = decodeBinaryData(binarydata)
            # print("payload received:")
            # print(image_buffer)

            return image_buffer
        if curr_size > payload_size:
            print("ERROR PARSING DATA")




