import numpy as np
from PIL import Image
import cv2, imutils, pyautogui
from skimage.io import imread

import time, queue
import globals
import multiprocessing
from multiprocessing import Pool
import matplotlib.pyplot as plt

def getBackground(frames, options):
    print("Getting background")
    backArr = frames.get(True, options.seconds)
    max = backArr.max()

    while (max == 0):
        print("max was 0")
        backArr = frames.get(True, options.seconds)
        max = backArr.max()
        time.sleep(0.05)

    backgroundZValue = np.average(backArr)

    backArr = (255.0 / max * (backArr - backArr.min())).astype(np.uint8)
    img = Image.fromarray(backArr)
    img.save("images/00_background.BMP")

    print()
    print("Capture taken.")
    time.sleep(0.5)
    print("3")
    time.sleep(0.5)
    print("2")
    time.sleep(0.5)
    print("1")
    print()

    return backArr, backgroundZValue

def pipeline(arr, backArrM, debug, ct):

    start = time.time()
    arrM = arr.copy()
    arrMax = arr.max()
    arrM = (255.0 / arrMax * (arr - arr.min())).astype(np.uint8)

    if (debug):
        img = Image.fromarray(arrM)
        img.save("images/00a_original.BMP")

    item = arrM - backArrM

    #itemM = (255.0 / itemM.max() * (item - item.min())).astype(np.uint8)

    if (debug):
        img = Image.fromarray(item)
        img.save("images/00b_subtracted.BMP")

    avg = np.average(item)
    if (avg < 15 or avg > 240): return None

    #print("     before forLoop: ", (time.time() - start))
    #curTime = time.time()

    itemM = np.zeros((171,224))
    #num255 = 0

    for x in range(0, 170,3): #171
        for y in range(0, 221,3): #224
            val = item[x][y]
            if (val >= 15 and val <= avg):
                itemM[x][y] = 255
                itemM[x][y+1] = 255
                itemM[x+1][y] = 255
                itemM[x+1][y+1] = 255

                itemM[x][y+2] = 255
                itemM[x+1][y+2] = 255
                itemM[x+2][y+2] = 255
                itemM[x+2][y+1] = 255
                itemM[x+2][y] = 255

            #else:
            #    itemM[x][y] = 255
                #num255 += 1

    #print("     We did the forLoop: ", (time.time() - curTime))
    #curTime = time.time()

    #if (num255 < 300): return None

    im = itemM.astype(np.uint8)
    if (debug):
        img = Image.fromarray(im)
        img.save("images/01_rescaled.BMP")


    #print(" subtracted")
    contours, hierarchy = cv2.findContours(im,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    maxCnt = 500
    maxContour = None
    for cnt in contours:
        val = cv2.arcLength(cnt, True) + cv2.contourArea(cnt)
        if (val > maxCnt and val < 20000):
            maxCnt = val
            maxContour = cnt

    if (maxContour is None): return None

    bIm = np.zeros((171,224))
    hull = cv2.convexHull(maxContour)
    bIM = cv2.drawContours(bIm,[hull],0,84,1)

    if (debug):
        cv2.drawContours(im,[maxContour],0,84,1)
        cv2.drawContours(im,[hull],0,168,1)
        cv2.imwrite("images/03_convexHull.BMP", im)

    cv2.imwrite("images/04_justHull.BMP", bIm)
    im = cv2.imread("images/04_justHull.BMP", 0)

    #print("     found contours: ", (time.time() - curTime))
    #curTime = time.time()
    #print(" contours")


    M = cv2.moments(maxContour)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    cZ = round(arr[cY][cX], 3)
    if abs(arrMax - cZ) < 0.1: return None

    corners = cv2.goodFeaturesToTrack(im,8,0.01,10)
    corners = np.int0(corners)

    if corners is None: return None
    if (len(corners) == 0): return None

    #print(" found corners")

    if (debug):
        for corner in corners:
            x, y = corner.ravel()
            cv2.circle(im,(x,y),3,100,-1)
        nIm = Image.fromarray(im)
        nIm.save("images/05_corners.BMP")

    #print("     found corners: ", (time.time() - curTime))
    #curTime = time.time()

    highestVal = -1000
    highestCorner = corners[0]

    gotCorner = False

    for corner in corners:
        x, y = corner.ravel()

        if (y >= 165):
            gotCorner = True
            continue

        if ((x <= 5) or (y <= 5) or (x >= 218)):
            continue


        currCenterDist = abs((x - cX) * (x - cX) + (y - cY) * (y - cY)) #absolute value of (x-centerx) plus absolute value of (y-centery)
        if (currCenterDist > highestVal and cY > y):
            highestVal = currCenterDist
            highestCorner = corner

    #print("     found highest corner: ", (time.time() - curTime))
    #curTime = time.time()

    if not gotCorner: return None

    if (highestVal == -1000): return None

    #print(" highest corner")

    x, y = highestCorner.ravel()
    #print("x: " + str(x) + "y: " + str(y))
    z = round(arr[y][x], 3)
    if (z <= 0.001):
        z = round(arr[y+1][x], 3)
        if (z <= 0.001):
            z = round(arr[y-1][x], 3)
            if (z <= 0.001):
                z = round(arr[y][x+1], 3)
                if (z <= 0.001):
                    z = round(arr[y][x-1], 3)

    #print("       found x,y,z: ", (time.time() - curTime))
    #if (arr.max() - z < 0.1): return None

    if (debug):
        cv2.circle(im,(x,y),3,255,-1)
        img = Image.fromarray(im)
        name = "images/06_corners" + str(ct) + ".BMP"
        img.save(name)

    #print("we wanted to move")

    #print("x: " + str(x) + " y: " + str(y))
    return (int(x * globals.xM), int(y * globals.yM), z, int(cX * globals.xM), int(cY * globals.yM), cZ)

def procPip(frames, mouseCoords, options):
    globals.initialize()
    backArr, backgroundZValue = getBackground(frames, options)
    mouseCoords.put(backgroundZValue, True, 1)
    ct = 0
    lclCt = 0
    t_end = time.time() + options.seconds
    while time.time() < t_end:
        try:
            # try to retrieve an item from the queue.
            # this will block until an item can be retrieved
            # or the timeout of 1 second is hit
            item = frames.get(True, 1)
            #print("Proc: ", np.average(item))
        except queue.Empty:
            # this will be thrown when the timeout is hit
            break
        else:
            if (lclCt == globals.sampleRate):
                #stTime = time.time()
                val = pipeline(item, backArr, options.debug, ct)
                #print("Pip time: ", (time.time() - stTime))
                lclCt = 0
                if val is not None:
                    mouseCoords.put(val)
                else:
                    mouseCoords.put((-1,-1,-1,-1, -1, -1))
                #print("c: " + str(ct) + " we added coords" + str(val))
                #print(mouseCoords.qsize())
            ct += 1
            lclCt += 1
            #continue
