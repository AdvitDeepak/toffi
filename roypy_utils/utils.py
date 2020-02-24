"""
This is utils
"""

import argparse, sys, os
import roypy_utils.roypy as roypy
import time
import queue
from collections import deque
#from sample_camera_info import print_camera_info
from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import cv2
from skimage.io import imread
import imutils
import pyautogui

class MyListener(roypy.IDepthDataListener):
    def __init__(self, q):
        super(MyListener, self).__init__()
        #self.queue = q
        self.deque = q

    def onNewData(self, data):
        zvalues = []
        for i in range(data.getNumPoints()):
            zvalues.append(data.getZ(i))
        zarray = np.asarray(zvalues)

        """
        Reshapes zarray so that its 2nd dim has a size of data.width + tells it
        to calculate the correct size of the first dimension based on that val
        """

        p = zarray.reshape (-1, data.width)
        #self.queue.put(p)
        self.deque.append(p)

    def paint (self, data):
        """
        Called in the main thread, with data containing one of the items
        that was added to the queue in onNewData.
        """
        # create a figure and show the raw data
        plt.figure(1)
        plt.imshow(data)

        plt.show(block = False)
        plt.draw()

        # this pause ensures the drawing for some backends
        plt.pause(0.001)


def saveBmp(item):
    # Saves the data in the array to image.bmp
    plt.imshow(item)
    plt.savefig("images/00_original.png")

    rescaled = (255.0 / item.max() * (item - item.min())).astype(np.uint8)
    im = Image.fromarray(rescaled)
    im.save("images/01_myFile.BMP")
    return rescaled
    #return im

def removeBackground(arr):
    #im = imread("images/01_myFile.BMP")
    im = arr
    imMin = np.amin(im)
    imMax = np.amax(im)
    imAvg = np.average(im)
    arr = np.zeros(shape = (171, 224))
    for x in range(0,171):
        for y in range(0,224):
            if (im[x][y] > (imAvg)) or (im[x][y]==0):
                arr[x][y] = 0
            else:
                arr[x][y] = 255
    rescaled = arr.astype(np.uint8)
    im = Image.fromarray(rescaled)
    im.save("images/02_removedFile.BMP")
    return rescaled

def objectDetect(arr):
    im = cv2.imread("images/02_removedFile.BMP")
    #blur = cv2.GaussianBlur(im,(3,3),0)
    blur = cv2.GaussianBlur(arr,(3,3),0)
    edges = cv2.Canny(blur,0,255)
    imEdges = Image.fromarray(edges)
    imEdges.save("images/03_edges.BMP")
    return edges

def findHand(arr):
    im = cv2.imread("images/03_edges.BMP")
    #print(arr.shape)
    #im = arr.astype(np.uint32)
    #print(printArrInfo(im))
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(imgray,127,255,0)
    #ret,thresh = cv2.threshold(im,127,255,0)

    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    maxCnt = 0
    for cnt in contours:
        if (cv2.arcLength(cnt,True) > maxCnt):
            maxCnt = cv2.arcLength(cnt,True) + cv2.contourArea(cnt)
    lst_intensities = []
    for cnt in contours:
        if (cv2.arcLength(cnt,True) + cv2.contourArea(cnt) == maxCnt):
            hull = cv2.convexHull(cnt)
            cv2.drawContours(im,[cnt],0,(0,255,0),2)
            cv2.drawContours(im,[hull],0,(0,0,255),2)

    im = Image.fromarray(im)
    im.save("images/04_contours.BMP")
    im = cv2.imread("images/04_contours.BMP")
    im = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    noWhite = np.zeros(shape = (171, 224))
    for x in range(0,171):
        for y in range(0,224):
            if (im[x][y] != 29):
                noWhite[x][y] = 0
            else:
                noWhite[x][y] = 255

    rescaled = noWhite.astype(np.uint8)

    im = Image.fromarray(rescaled)
    im.save("images/05_noWhite.BMP")
    im = cv2.imread("images/05_noWhite.BMP")
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    corners = cv2.goodFeaturesToTrack(gray, 3, 0.1, 10)

    try:
        corners = np.int0(corners)
    except:
        return None
    points = []
    for corner in corners:
        x,y = corner.ravel()
        if ((x <= 5) or (y <= 5) or (x >= 218) or (y >= 165)):
            pass
        else:
            points.append((x,y))
            cv2.circle(im,(x,y),3,255,-1)

    if (len(points) == 0):
        return None
    elif (len(points) > 1):
        highestX = 0
        currHigh = points[0]
        for pair in points:
            if (pair[0] > highestX):
                highestX = pair[0]
                currHigh = pair

        coordinates = currHigh
    else:
        coordinates = points[0]

    cv2.circle(im,(coordinates[0],coordinates[1]),3,(0, 255,0),-1)
    im = Image.fromarray(im)
    im.save("images/06_corners.BMP")
    return coordinates

def findZ(coordinates, arr):
    return round(arr[coordinates[1]][coordinates[0]], 3)

def findDeltaXYZ():
    fhandle = open("outputCoordinates.txt", "r")
    lineList = fhandle.readlines()
    fhandle.close()

    secondLast = lineList[len(lineList)-2]
    lastLine = lineList[len(lineList)-1]

    secondSplit = secondLast.split(',')
    lastSplit = lastLine.split(',')

    secondX = int(secondSplit[0])
    secondY = int(secondSplit[1])
    secondZ = float(secondSplit[2])

    lastX = int(lastSplit[0])
    lastY = int(lastSplit[1])
    lastZ = float(lastSplit[2])

    deltaX = lastX - secondX
    deltaY = lastY - secondY

    if (lastZ - secondZ > .3):
        return deltaX, deltaY, True
    return deltaX, deltaY, False

def updateMouse(dX, dY, buttonPressed):

    if(buttonPressed):
        pyautogui.click()
        return

    screenDim = pyautogui.size()
    #xMultiplier = (screenDim[0] / 224)
    #yMultiplier = (screenDim[1] / 171)
    xMultiplier = 0.5 * ((screenDim[1] / 171) + (screenDim[0] / 224))
    yMultiplier = xMultiplier

    if (dX * xMultiplier > screenDim[0]) or (dY * yMultiplier > screenDim[1]):
        return

    x, y = pyautogui.position()

    if not (pyautogui.onScreen(x + dX * xMultiplier, y + dY * yMultiplier)):
        return

    pyautogui.move(dX * xMultiplier, dY * yMultiplier)
