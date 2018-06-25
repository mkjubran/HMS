import scenedetect
import cv2
scene_list = []		# Modified by detect_scenes(...) below.
    
cap = cv2.VideoCapture('../../vid/Video3_h1080p.mp4')	
# Make sure to check cap.isOpened() before continuing!

# Usually use one detector, but multiple can be used.
detector_list = [scenedetect.ContentDetector()]

print(detector_list)

frames_read = scenedetect.detect_scenes(cap, scene_list, detector_list)

# scene_list now contains the frame numbers of scene boundaries.
print scene_list

# Ensure we release the VideoCapture object.
cap.release()
