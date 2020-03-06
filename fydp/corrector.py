import numpy as np
from enum import Enum
'''
Corrector class to help determine the validity and satefy of poses during various exercises
Deadlift:
    Ideal if done with SIDE VIEW
    key postures: 
    - hips should be vertically between knees and head not too low or too high 
      otherwise they create unfavorable leverages, can decrease amount of weight youre pulling
    - bar should be directly under shoulder blade
    - should try to keep bar close as possible to body throughout exercise 
'''

class Direction(Enum):
    UP = 1
    DOWN = 2

class _Corrector:
    #set base values to deviate from for all the keypoints required for this exercise
    bodyMap = {0:  "Nose", 1:  "Neck" , 2:  "RShoulder", 3:  "RElbow", 4:  "RWrist", 5:  "LShoulder", 6:  "LElbow", 7:  "LWrist",
               8:  "MidHip", 9:  "RHip", 10: "RKnee", 11: "RAnkle", 12: "LHip", 13: "LKnee", 14: "LAnkle", 15: "REye", 16: "LEye", 17: "REar",
               18: "LEar", 19: "LBigToe", 20: "LSmallToe", 21: "LHeel", 22: "RBigToe", 23: "RSmallToe", 24: "RHeel", 25: "Background"}

    baseValues = {}
    
    def __init__(self, baseValues):
        self.baseValues = baseValues

    '''
        Returns mapped values of body points 
    '''
    def mapValues(self, keyPoints):
        keyPointMap = {}
        for i in range(0, len(keyPoints)):
            keyPointMap[self.bodyMap[i]] = keyPoints[i]
        return keyPointMap


class SquatCorrector(_Corrector):
  
    previousDirection = Direction.DOWN
    # False error state means form is good, True error state means form is erroneous
    errorState = {
        "leg": False,
        "knee": False,
        "back": False,
        "hip": False
    } 
    errorCodes = {
        1 : "Caution: Legs are straight, Bend Knees Slightly",
        2 : "Caution: Leaning too forward, please align knees with toes", 
        3 : "Caution: Back is not straight, please look straight and align your back",
        4 : "Caution: Squat did not have enough depth, please lower hips next rep"
    }
    # Set tracking all current errors to be displayed
    messagesToDisplay = set()
    previousMessagesToDisplay = set()

    def __init__(self, baseValues):
        _Corrector.__init__(self, self.mapValues(baseValues))
        self.previousFrameKeyPoints = self.mapValues(baseValues)
        # print(baseValues)

    def filter(self, keyPoints):
        # {24, "RHeel"}, {10, "RKnee"}, {9,  "RHip"},  {1,  "Neck"}, {2,  "RShoulder"}
        return {self.bodyMap[24]: keyPoints[24],
                self.bodyMap[10]: keyPoints[10],
                self.bodyMap[9]: keyPoints[9],
                self.bodyMap[1]: keyPoints[1],
                self.bodyMap[2]: keyPoints[2]
                }


    def legForm(self, keyPoints):
        errorMessage = 1
        kneeHeelDelta = abs(keyPoints['RHeel'][0] - keyPoints['RKnee'][0])
        # DG - kneeHeelDelta limit of 10 works better for me
        if (kneeHeelDelta) < 10:
            if self.errorState["leg"] == False:
                self.messagesToDisplay.add(errorMessage)
            self.errorState["leg"] = True
            return False
        else:
            self.messagesToDisplay.discard(errorMessage)
            self.errorState["leg"] = False
            return True

    # Not using this right not due to lack of utility
    def kneeForm(self, keyPoints):
        errorMessage = 2
        toeKneeDelta = abs(keyPoints['RBigToe'][0] - keyPoints['RKnee'][0])
        if toeKneeDelta > 15:
            if self.errorState["knee"] == False:
                self.messagesToDisplay.add(errorMessage)
            self.errorState["knee"] = True
            return False
        else:
            self.messagesToDisplay.discard(errorMessage)
            self.errorState["knee"] = False
            return True

    #Unused right now
    def cosine(self, a, b, c):
        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)

        return np.degrees(angle)

    def backForm(self, keyPoints):
        errorMessage = 3
        rEar = keyPoints['REar']
        rEye = keyPoints['REye']
        rHip = keyPoints['RHip']
        rShoulder = keyPoints['RShoulder']

        # print("Right Ear: " + str(rEar))
        # print("Right Eye: " + str(rEye))

        earEyeDelta = abs(rEar[1] - rEye[1])
        if(earEyeDelta > 5):
            # Only print out error when going from good to bad
            if self.errorState["back"] == False:
                self.messagesToDisplay.add(errorMessage)
            self.errorState["back"] = True
            return False
        else:
            self.messagesToDisplay.discard(errorMessage)
            self.errorState["back"] = False
            return True
          
    # Hip form
    # Goal: Ensure that hips go below knees on every rep. Need to maintain state keeping track of
    # whether the user is going up or down.
    def hipForm(self, keyPoints):
        errorMessage = 4
        result = True
        hipVerticalPosition = keyPoints['RHip'][1]
        kneeVerticalPosition = keyPoints['RKnee'][1]
      
        # Detect change in direction
        lastHipVerticalPosition = self.previousFrameKeyPoints['RHip'][1]
        # If lower than last hip vertical position, means the direction is down
        if hipVerticalPosition > (lastHipVerticalPosition + 5):
            currentDirection = Direction.DOWN
        else:
            currentDirection = Direction.UP

        # Check if direction changing from down to up
        if self.previousDirection == Direction.DOWN and currentDirection == Direction.UP:
            # Check if hip dipped below knees
            if hipVerticalPosition + 10 >= kneeVerticalPosition:
                self.messagesToDisplay.discard(errorMessage)
                self.errorState["hip"] = False
                result = True
            else:
                if self.errorState["hip"] == False:
                    self.messagesToDisplay.add(errorMessage)
                self.errorState["hip"] = True
                result = False
      
        self.previousDirection = currentDirection
        return result

    def corrector(self, keyPoints):
        currKeyPointMap = self.mapValues(keyPoints)

        isLegFormGood = self.legForm(currKeyPointMap)
        isBackFormGood = self.backForm(currKeyPointMap)
        isHipFormGood = self.hipForm(currKeyPointMap)
        # isKneeFormGood = self.kneeForm(currKeyPointMap)
        # self.printErrors()

        # Update previous frame
        self.previousFrameKeyPoints = currKeyPointMap
        self.previousMessagesToDisplay = self.messagesToDisplay.copy()

        # Return current form's errors
        return self.getErrorsFromCodes()
    
    def getErrorsFromCodes(self):
        errorTexts = ""
        for error in self.messagesToDisplay:
            errorTexts += self.errorCodes[error] 
            errorTexts += " || "
        return errorTexts

    # Function to help debugging, only prints form errors if they differ from last frame
    def printErrors(self):
        if self.previousMessagesToDisplay != self.messagesToDisplay:
            print("NEW ERROR MESSAGES---------")
            for error in self.messagesToDisplay:
                print(self.errorCodes[error], end = ' || ')
        else:
            pass
        print("")
        


class DeadliftCorrector(_Corrector):

    def __init__(self, baseValues):
        _Corrector.__init__(self, self.mapValues(baseValues))
        print(baseValues)

    def filter(self, keyPoints):
        # {24, "RHeel"}, {10, "RKnee"}, {9,  "RHip"},  {1,  "Neck"}, {2,  "RShoulder"}
        return {self.bodyMap[24]: keyPoints[24],
                self.bodyMap[10]: keyPoints[10],
                self.bodyMap[9]: keyPoints[9],
                self.bodyMap[1]: keyPoints[1],
                self.bodyMap[2]: keyPoints[2]
                }


    def hipForm(self, keyPoints):
        # Hips should always be above knees, higher y value means lower down in the frame
        hipKneeDelta = keyPoints['RKnee'][1] - keyPoints['RHip'][1] 
        
        # print("hip knee delta")
        # print(hipKneeDelta)
        if hipKneeDelta < 20:
            return False, "CAUTION!! HIPS are too low, please raise them to avoide bad posture"
        else:
            return True, "Hips dont lie babayyy"


    def shoulderForm(self, keyPoints):
        #Shoulder and wrist should always be horizontally close to each other
        rShoulder = keyPoints['RShoulder']
        rWrist = keyPoints['RWrist']

        shoulderWristDelta = abs(rShoulder[0] - rWrist[0])
        # print("Shoulder-wrist delta")
        # print(shoulderWristDelta)
        if(shoulderWristDelta > 30):
            return False, "CAUTION!! SHOULDER not aligned with bar"
        else:
            return True, "Shoulder is Good"

    def corrector(self, keyPoints):
        currKeyPointMap = self.mapValues(keyPoints)

        isHipFormGood , hipCorrectionString = self.hipForm(currKeyPointMap)
        print(hipCorrectionString)

        isShoulderFormGood , shoulderCorrectionString = self.shoulderForm(currKeyPointMap)
        print(shoulderCorrectionString)

