# From Python
# It requires OpenCV installed for Python
import sys
import cv2
import os
import time
from sys import platform

# Import Openpose (Windows/Ubuntu/OSX)
dir_path = os.path.dirname(os.path.realpath(__file__))
try:
    # Change these variables to point to the correct folder (Release/x64 etc.) 
    sys.path.append('../../python');
    # If you run `make install` (default path is `/usr/local/python` for Ubuntu), you can also access the OpenPose/python module from there. This will install OpenPose and the python library at your desired installation path. Ensure that this is in your python path in order to use it.
    # sys.path.append('/usr/local/python')
    from openpose import pyopenpose as op
except ImportError as e:
    print('Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
    raise e

# Custom Params (refer to include/openpose/flags.hpp for more parameters)
params = dict()
params["model_folder"] = "../../../models/"

 # Starting OpenPose
opWrapper = op.WrapperPython()
opWrapper.configure(params)
opWrapper.start()

def process(imgsrc):
    try:
        datum = op.Datum()
        imageToProcess = imgsrc

        # Define input data
        datum.cvInputData = imageToProcess
        opWrapper.emplaceAndPop([datum])

        # Collect and return output
        output = {'imageWithKeypoints': datum.cvOutputData, 'poseKeypoints': datum.poseKeypoints}
        return output
    except Exception as e:
        print(e)
        sys.exit(-1)

# process("")
