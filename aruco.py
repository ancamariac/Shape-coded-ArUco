#!/usr/bin/env python
# coding: utf-8

from objloader_simple import *
import numpy as np
import time
from pymediainfo import MediaInfo
import cv2
from cv2 import aruco
import math

# projection matrix for 3d models
def projection_matrix(camera_parameters, homography):
    
    homography = homography * (-1)
    rot_and_transl = np.dot(np.linalg.inv(camera_parameters), homography)
    col_1 = rot_and_transl[:, 0]
    col_2 = rot_and_transl[:, 1]
    col_3 = rot_and_transl[:, 2]
    
    # normalise vectors
    l = math.sqrt(np.linalg.norm(col_1, 2) * np.linalg.norm(col_2, 2))
    rot_1 = col_1 / l
    rot_2 = col_2 / l
    translation = col_3 / l
    
    # compute the orthonormal basis
    c = rot_1 + rot_2
    p = np.cross(rot_1, rot_2)
    d = np.cross(c, p)
    rot_1 = np.dot(c / np.linalg.norm(c, 2) + d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_2 = np.dot(c / np.linalg.norm(c, 2) - d / np.linalg.norm(d, 2), 1 / math.sqrt(2))
    rot_3 = np.cross(rot_1, rot_2)
    
    # finally, compute the 3D projection matrix from the model to the current frame
    projection = np.stack((rot_1, rot_2, rot_3, translation)).T
    
    return np.dot(camera_parameters, projection)

# project cube or model
def render(img, obj, projection, model, color=False):

    vertices = obj.vertices
    scale_matrix = np.eye(3) * 6
    h, w, c = model.shape

    for face in obj.faces:
        face_vertices = face[0]
        points = np.array([vertices[vertex - 1] for vertex in face_vertices])
        points = np.dot(points, scale_matrix)
        # render model in the middle of the reference surface. To do so,
        # model points must be displaced
        points = np.array([[p[0] + w / 2, p[1] + h / 2, p[2]] for p in points])
        dst = cv2.perspectiveTransform(points.reshape(-1, 1, 3), projection)
        imgpts = np.int32(dst)

        cv2.fillConvexPoly(img, imgpts, (80, 27, 211))
    return img

# Incarcare imagine 
image = cv2.imread("image.png")
obj = OBJ('fox.obj', swapyz=False)
h1, w1, c1 = image.shape

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
            #frame_final = cv2.warpPerspective(obj, homography, (frame.shape[1], frame.shape[0]))
            
            # Aplicare transformare de perspectiva pe imagine sursa cu markerul
            corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            transformedCorners = cv2.perspectiveTransform(corners, homography)
        
            # Incadrare marker in imagine
            frame_final = cv2.polylines(frame, [np.int32(transformedCorners)], True, 255, 10, cv2.LINE_AA)
            cv2.fillConvexPoly(frame, destinationPoints.astype(int), (0, 0, 0))

            if ( marker_id == 2 ):
                #frame_final += frame
                # Obtinere matrice de proiectie 3D, ce va fi folosita pentru desenarea modelului 3D la unghiul
                 # si perspectiva potrivita pe imaginea cu markerul ce contine id-ul 1
                projection = projection_matrix(camera_parameters, homography)  

                # Proiectare model 3D pe frame
                frame_final = render(frame_final, obj, projection, image, False)

            else:
                frame_final = frame

        else:
            frame_final = frame
        
        #frame_final = cv2.resize(frame_final, (frame_final.shape[1]//5, frame_final.shape[0]//5))
        
        out.write(frame_final)

        if not ret:
            break
    
cap.release()
out.release()
print("Video Saved")
