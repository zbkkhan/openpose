
import numpy as np
'''

'''

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


    def legForm(self, keyPoints):
        kneeHeelDelta = abs(keyPoints['RHeel'][0] - keyPoints['RKnee'][0])
        # DG - kneeHeelDelta limit of 10 works better for me
        if (kneeHeelDelta) < 10:
            return False, "Caution: Legs are straight, Bend Knees Slightly"
        else:
            return True, "Legs are Good"



    #Unused right now
    def cosine(self, a, b, c):
        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(cosine_angle)

        return np.degrees(angle)

    def backForm(self, keyPoints):
        rEar = keyPoints['REar']
        rEye = keyPoints['REye']
        rHip = keyPoints['RHip']
        rShoulder = keyPoints['RShoulder']

        # print("Right Ear: " + str(rEar))
        # print("Right Eye: " + str(rEye))

        earEyeDelta = abs(rEar[1] - rEye[1])
        if(earEyeDelta > 5):
            return False, "Caution: back is not straight, look straight ahead to align your back"
        else:
            return True, "Back is Good"

    def corrector(self, keyPoints):
        currKeyPointMap = self.mapValues(keyPoints)
        isLegFormGood , correctionString = self.legForm(currKeyPointMap)

        print(correctionString)
        isBackFormGood , correctionString = self.backForm(currKeyPointMap)

        print(correctionString)
        # print(currKeyPointMap)

