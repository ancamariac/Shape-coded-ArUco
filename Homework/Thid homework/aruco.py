#!/usr/bin/env python
# coding: utf-8

import numpy as np
import time
from pymediainfo import MediaInfo
import cv2
from cv2 import aruco

# Incarcare imagine 
obj = cv2.imread("image.png")
h1, w1, c1 = obj.shape

aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
parameters =  aruco.DetectorParameters_create()
referenceImage = cv2.imread("marker_capture2.jpg")
w = referenceImage.shape[1]
h = referenceImage.shape[0]

camera_parameters = np.array([[1000, 0, 320], [0, 1000, 240], [0, 0, 1]])

cap = cv2.VideoCapture(0)
print("Opened Camera")

fourcc = cv2.VideoWriter_fourcc(*'RGBA')

fps = 35.0
duration = 4 
dimensions = (640,  480)

out = cv2.VideoWriter('aruco.mp4', fourcc, fps, dimensions)
if(cap.isOpened()):
    t = time.time()
    while( (time.time() - t) < duration ):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if( len(corners) != 0 ):
            # Copiere colturi pentru primul marker detectat
            crn = np.array(corners)[0,0]
            # Extragere index aruco pentru fiecare marker detectat
            marker_id = ids[0,0]
            # Merkeri
            frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
            c = [np.array(corners)[0,0,:, 0].mean(), np.array(corners)[0,0,:, 1].mean()]

            frame_points = frame.copy()
            radius = 30
            thickness = 60
            # Desenare punct de centru marker
            frame_points = cv2.circle(frame_points, (int(c[0]), int(c[1])), radius, (200, 200, 0), thickness)
            # Desenare punct stanga sus marker
            frame_points = cv2.circle(frame_points, (int(np.array(corners)[0,0,0,0]), int(np.array(corners)[0,0,0,1])), radius, (0, 255, 0), thickness)
            # Desenare punct dreapa jos marker
            frame_points = cv2.circle(frame_points, (int(np.array(corners)[0,0,2,0]), int(np.array(corners)[0,0,2,1])), radius, (0, 0, 255), thickness)

            sourcePoints = np.float32([(0,0),(0,w1),(h1,w1),(h1,0)]).reshape(-1, 1, 2)
            destinationPoints = np.float32([(crn[0,0], crn[0,1]), (crn[1,0], crn[1,1]), (crn[2,0], crn[2,1]), (crn[3,0], crn[3,1])]).reshape(-1, 1, 2)

            # Obtinere matrice de homografie
            homography, mask = cv2.findHomography(sourcePoints, destinationPoints)
            frame_final = cv2.warpPerspective(obj, homography, (frame.shape[1], frame.shape[0]))
            cv2.fillConvexPoly(frame, destinationPoints.astype(int), (0, 0, 0))

            if ( marker_id == 2 ):
                frame_final +=  frame

            else:
                frame_final = frame

        else:
            frame_final = frame
        
        out.write(frame_final)

        if not ret:
            break
        
cap.release()
out.release()
print("Video Saved")
