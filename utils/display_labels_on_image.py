import pickle
import cv2
import numpy as np
import sys

def loadDumpedLabels(fileName):
	labels = {}
	dumpedPointsAndLabels = pickle.load(open(fileName, "rb"))
	print dumpedPointsAndLabels
	for point in dumpedPointsAndLabels:
		keypoint = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1], _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
		label = point[6]
		labels[keypoint] = label
	return labels


if len(sys.argv) != 3:
	print 'A labels.pickle file and a reference image should be provied.'
	print 'Example: python display_labels_on_image.py ../labels.pickle ../SEQ3709/SEQ_3709_59.bmp'
	exit()


labels = loadDumpedLabels(sys.argv[1])

image = cv2.imread(sys.argv[2])
# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

im_with_keypoints = cv2.drawKeypoints(image, labels.keys(), np.array([]), (0,255,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Display labels on the keypoints
for kp in labels:
	shift = int(kp.size / 4)
	cv2.putText(im_with_keypoints, labels[kp], (int(kp.pt[0] - shift), int(kp.pt[1] + shift)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0)) 



cv2.imshow('Keys',im_with_keypoints)
cv2.waitKey(0)
cv2.destroyAllWindows()
