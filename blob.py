import sys
import cv2
import numpy as np
from enum import Enum
import math
import Tkinter
import tkSimpleDialog
from tkFileDialog import askopenfilename
import matplotlib.pyplot as plt
import pickle

# True if a key is still drawn
drawing = False

# Initial x and y coordinates when keys are drawn, updated on left buttondown
ix,iy = -1,-1

# Passwords file to use to find the closest match to the pressed keys found on the thermal image
PASSWORD_FILE = "passwords.txt"

# File name extension to save the labels (labels can be loaded later)
FILE_TO_SAVE_LABELS = "labels.pickle"

# File name to save found blobs on the image
FILE_TO_SAVE_BLOBS = "blobs.bmp"

# Used to display the results of the password finding process
root = Tkinter.Tk()
root.withdraw()

# Used to represent the current mode
class Mode(Enum):
	DRAW_KEYS = 0
	ENTER_LABELS = 1
	FIND_PASSWORDS = 2

# Initial mode is DRAW_KEYS, updated in each mode change
currMode = Mode.DRAW_KEYS


# Keys (cv2.KeyPoint's) and labels are stored
labels = {}

def mark_keys(event,x,y,flags,param):
	""" Function that handles actions (i.e., drawing keys, marking labels) on the image. """
	global ix,iy,drawing,currMode,keypoints,labels
	# Handles key drawing: A circle is drawn and saved to represent a key on the image.
	# The point when LBUTTONDOWN is the center of the circle, distance between this point
	# and the point when LBUTTONUP is the radius of the circle.
	if currMode == Mode.DRAW_KEYS:
		if event == cv2.EVENT_LBUTTONDOWN:
			drawing = True
			ix,iy = x,y
		elif event == cv2.EVENT_LBUTTONUP:
			drawing = False
			r = math.hypot(ix - x, iy - y)
			if (r != 0.0): # No need to draw a circle with r = 0
				cv2.circle(im_with_keypoints,(ix,iy), int(r),(0,255,0),1)
				keypoints.append(cv2.KeyPoint(ix, iy, r))
	elif currMode == Mode.ENTER_LABELS:
		if event == cv2.EVENT_LBUTTONDOWN:
			for kp in keypoints:
				if math.hypot(kp.pt[0] - x, kp.pt[1] - y) < kp.size:
					label = tkSimpleDialog.askstring("Label Entry", "Enter the Label:", parent=root)
					labels[kp] = label
					# put the text on the image
					shift = int(kp.size / 4)
					cv2.putText(im_with_keypoints, label, (int(kp.pt[0] - shift), int(kp.pt[1] + shift)), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0)) 
					print label
					break

def getDistance(str1, str2):
	""" Used to calculate the distance between two strings. """
	dist = 0
	charSet = set()
	for c in str1:
		charSet.add(c)

	for c in str2:
		if not c in charSet:
			dist = dist + 1
	return dist

def searchForPasswords(fileName, pressedKeys):
	""" Used to calculate distances between passwords in a dictionary and pressed keys. 
	A sorted password list (according to distances) is returned. """
	
	# fine if the passwords file is small, otherwise we need to read it line by line
	passwordFile = open(fileName,"r")
	lines = passwordFile.read().splitlines()
	passwordFile.close()


	distances = []
	# each line is a password
	for line in lines:
		line = line.strip()
		distances.append((line, getDistance(pressedKeys, line)))

	print "Distances: ", distances

	# sort according to distances
	distances.sort(key = lambda tup: tup[1])

	return distances

def findPasswordsOnThermalPicture(x):
	""" Finds keys pressed on the thermal image using blob detection and labels entered by the user.
	A password is used to find the best (i.e., passwords with the lowest distance to the pressed keys) matches. 
	Also, a window with the information regarding this process is displayed. """
	global keypoints
	if x != 1:
		return
	fileName = askopenfilename()
	print fileName
	# get the pressed keys and do analysis
	imageNew = cv2.imread(fileName)
	# filter image according to the color value (yellow -> r (0th index of rgb) is close to 0)
	for i in range(len(imageNew)):
		for j in range(len(imageNew[i])):
			if imageNew[i][j][0] > 30:
				imageNew[i][j] = [0, 0, 0]
	grayNew = cv2.cvtColor(imageNew, cv2.COLOR_BGR2GRAY)
	blurredNew = cv2.blur(grayNew,(10, 10))
	# mask = cv2.inRange(grayNew, 150, 255)
	# res = cv2.bitwise_and(imageNew, imageNew, mask= mask)\
	params = cv2.SimpleBlobDetector_Params()

	# Example params that can be used, might depend on the image.
	# params.filterByCircularity = True
	# params.minCircularity = 0.9
	# params.filterByConvexity = True
	# params.minConvexity = 0.5
	# params.filterByArea = True
	# params.minArea = 150\
	
	# Filter by light color.
	params.filterByColor = True
	params.blobColor = 255

	# Find blobs on the image
	detector = cv2.SimpleBlobDetector_create(params)
	keypointsNew = detector.detect(blurredNew)
	print keypointsNew

	# Save the found blobs (i.e., pressed keys) on the image.
	imgWithNewKeypoints = cv2.drawKeypoints(grayNew, keypointsNew, np.array([]), (0,255,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
	cv2.imwrite(FILE_TO_SAVE_BLOBS, imgWithNewKeypoints)

	# plt.imshow(imgWithNewKeypoints)
	text = "Finding Keys\n"

	foundKeys = []
	print labels

	unlabeled = 0
	# find to which key these keys belong to
	for i in range(len(keypointsNew)):
		for j in range(len(keypoints)):
			kpFromImage = keypointsNew[i]
			kpFromReferenceFrame = keypoints[j]
			# If the blob and the key overlap, a pressed key is found.
			if cv2.KeyPoint.overlap(kpFromReferenceFrame, kpFromImage) > 0:
				if kpFromReferenceFrame in labels.keys():
					foundKeys.append(labels[kpFromReferenceFrame].lower())
					text += "Found key: " + str(labels[kpFromReferenceFrame]) + "\n"
				else:
					text += "Found key: " + "No label" + "\n"
					unlabeled = unlabeled + 1
					# foundKeys.append('No Label')
				break

	text += "Pressed keys:" + str(foundKeys) + "\n"
	text += "Pressed but unlabeled: " + str(unlabeled) + "\n"
	print 'Found keys: ', foundKeys

	text += "Searching for possible passwords\n"

	passwords = searchForPasswords(PASSWORD_FILE, ''.join(foundKeys))

	text += str(passwords) + "\n"
	text += "Best match: " + passwords[0][0] + "\n"


	# display info on a new window
	root = Tkinter.Tk()
	S = Tkinter.Scrollbar(root)
	T = Tkinter.Text(root, height=30, width=100)
	S.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
	T.pack(side=Tkinter.LEFT, fill=Tkinter.Y)
	S.config(command=T.yview())
	T.config(yscrollcommand=S.set)
	T.insert(Tkinter.END, text)
	T.pack()
	T.mainloop()

	# set track bar 0, so that it can be used again with the same layout defined
	# NOT DONE YET
 
def getKeypoints(fileName):
	""" Gets the keypoints using a blob detector on an image."""
	image = cv2.imread(fileName)
	gray = image #cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blurred = cv2.blur(gray,(7, 8)) # cv2.GaussianBlur(gray, (5, 5), 0)
	params = cv2.SimpleBlobDetector_Params()
	params.filterByConvexity = True
	params.minConvexity = 0.87
	detector = cv2.SimpleBlobDetector_create(params)
	return gray, blurred, detector.detect(blurred)

def loadDumpedLabels(fileName):
	""" Loads the dumped labels into a dictionary which means labels can be entered only once and be used for also other thermal images. """
	labels = {}
	dumpedPointsAndLabels = pickle.load(open(fileName, "rb"))
	print dumpedPointsAndLabels
	for point in dumpedPointsAndLabels:
		keypoint = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1], _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
		label = point[6]
		labels[keypoint] = label
	return labels

def doneEnteringLabels(x):
	""" Updates the current mode to FIND_PASSWORDS and adds another trackbar to represent the current mode change. 
	Also, sets the handler for the new trackbar. In addition, dumps the labels entered by the user """
	global currMode
	currMode = Mode.FIND_PASSWORDS

	# Save labels and matching keypoints
	print 'Labels before dumping: ', labels
	labelsToDump = []
	for point in labels:
		print labels[point]
		temp = (point.pt, point.size, point.angle, point.response, point.octave, point.class_id, labels[point])
		labelsToDump.append(temp)
	print labelsToDump

	# Dump labels for later use
	pickle.dump(labelsToDump, open(FILE_TO_SAVE_LABELS, "wb"))
	cv2.createTrackbar('Open a Thermal Picture', 'Keys', 0, 1, findPasswordsOnThermalPicture)
        
def doneDrawingKeys(x):
	""" Updates the current mode to ENTER_LABELS and adds another trackbar to represent the current mode change. 
	Also, sets the handler for the new trackbar """
	global currMode
	cv2.createTrackbar('Enter Labels', 'Keys', 0, 1, doneEnteringLabels)
	currMode = Mode.ENTER_LABELS


if len(sys.argv) != 2:
	print 'A reference image should be provided.'
	print 'Example: python blob.py SEQ3709/SEQ_3709_58.bmp'
	exit()

# Reference image should be given to the program
referenceImage = sys.argv[1]
gray, blurred, keypoints = getKeypoints(referenceImage)
# Draw the keypoints on the image
im_with_keypoints = cv2.drawKeypoints(gray, keypoints, np.array([]), (0,255,0), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Create the window
cv2.namedWindow('Keys')

# Set up the handler
cv2.setMouseCallback('Keys', mark_keys)

# Add the trackbar to the window and set the handler when it is slided
cv2.createTrackbar('Draw if Keys are Missing (Slide when Done)', 'Keys', 0, 1, doneDrawingKeys)

while 1:
	cv2.imshow('Keys',im_with_keypoints)
	k = cv2.waitKey(1) & 0xFF
	if k == 27: # escape key
		break

cv2.destroyAllWindows()
