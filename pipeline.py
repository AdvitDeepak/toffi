import numpy as np
from PIL import Image
import cv2, imutils, pyautogui
from skimage.io import imread

import time, queue
import globals
import os
import multiprocessing
from multiprocessing import Pool
import matplotlib.pyplot as plt

def getBackground(frames, options, tmpImageDir):
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
    img.save(tmpImageDir + "00_background.BMP")

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

def pipeline(tmpImageDir, arr, backArrM, backVal, debug, ct, xM, yM):

    NoneTuple = (None, None, None)
    start = time.time()
    arrM = arr.copy()
    arrMax = arr.max()
    procId = os.getpid()
    arrM = (255.0 / arrMax * (arr - arr.min())).astype(np.uint8)

    if (debug):
        img = Image.fromarray(arrM)
        img.save(tmpImageDir + "00a_original.BMP")

    im = arrM - backArrM

    if (debug):
        img = Image.fromarray(im)
        img.save(tmpImageDir + "00b_subtracted.BMP")

    avg = np.average(arrM)
    if (avg < 10 or avg > 240):


    im = (im >= 10) & (im <= avg)
    im = 255 * im.astype(np.uint8)

    if (debug):
        img = Image.fromarray(im)
        img.save(tmpImageDir + "01_rescaled.BMP")

    contours, hierarchy = cv2.findContours(im,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    maxCnt = 500
    maxContour = None
    for cnt in contours:
        val = cv2.arcLength(cnt, True) + cv2.contourArea(cnt)
        if (val > maxCnt and val < 20000):
            maxCnt = val
            maxContour = cnt

    if (maxContour is None):
        return NoneTuple

    bIm = np.zeros((171,224))
    hull = cv2.convexHull(maxContour)
    bIM = cv2.drawContours(bIm,[hull],0,84,1)

    if (debug):
        cv2.drawContours(im,[maxContour],0,84,1)
        cv2.drawContours(im,[hull],0,168,1)
        cv2.imwrite(tmpImageDir + "03_convexHull.BMP", im)

    im = bIM.astype(np.uint8)

    M = cv2.moments(maxContour)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    cZ = round(arr[cY][cX], 3)
    if abs(arrMax - cZ) < 0.1:
        return NoneTuple

    corners = cv2.goodFeaturesToTrack(im,8,0.01,10)

    if corners is None:
        return NoneTuple
    if (len(corners) == 0):
        return NoneTuple

    corners = np.int0(corners)

    if (debug):
        for corner in corners:
            x, y = corner.ravel()
            cv2.circle(im,(x,y),3,100,-1)
        nIm = Image.fromarray(im)
        nIm.save(tmpImageDir + "05_corners.BMP")

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

    if not gotCorner:
        return NoneTuple

    if (highestVal == -1000):
        return NoneTuple

    x, y = highestCorner.ravel()
    zArea = arr[y:y+6,x-2:x+3].flatten()
    zArea[zArea > backVal] = 0
    z = max(zArea)

    if (debug):
        cv2.circle(im,(x,y),3,255,-1)
        img = Image.fromarray(im)
        name = tmpImageDir + "06_corners" + str(ct) + ".BMP"
        img.save(name)

    return (int(x * xM), int(y * yM), z)


def procPip(frames, mouseCoords, options):

    globals.initialize()

    # Setup processing directories for pool of processes
    # Setup tmp image dir
    try:
        if(not os.path.isdir(globals.tmpDir)):
            os.mkdir(globals.tmpDir)
    except OSError as error:
        print("Could not make: " + globals.tmpDir)

    # Setup temp dir for pool of processes
    tmpImageDir = [globals.tmpDir + "proc_" + str(i) + "/" for i in range(globals.threadPoolSize)]
    for i in range(globals.threadPoolSize):
        try:
            if(not os.path.isdir(tmpImageDir[i])):
                os.mkdir(tmpImageDir[i])
        except OSError as error:
            print("Could not make dir: " + tmpImageDir[i])


    #pPool = multiprocessing.Pool(globals.threadPoolSize)
    backArr, backgroundZValue = getBackground(frames, options, globals.tmpDir)
    backgroundZValue -= globals.zNoiseThr

    zChangeState = 0
    zMoveDownStart = 0
    zMoveDownEnd = 0
    zResetValue = backgroundZValue + 100
    lx, ly, lz = (0, 0, zResetValue)
    ct = 0

    t_end = time.time() + options.seconds
    while time.time() < t_end:
        #listOfArgs = []
        try:
            # try to retrieve an item from the queue.
            # this will block until an item can be retrieved
            # or the timeout of 1 second is hit
            item = frames.get(True)

            #for fId in range(globals.threadPoolSize):
            #    item = frames.get(True, 1)
            #    listOfArgs.append([tmpImageDir[fId], item, backArr, backgroundZValue, options.debug, ct+fId, globals.xM, globals.yM])

        except queue.Empty:
            # this will be thrown when the timeout is hit
            print("pipeline except")
            continue
        else:

            stTime = time.time()
            (x, y, z)  = pipeline(globals.tmpDir, item, backArr, backgroundZValue, options.debug, ct, globals.xM, globals.yM)

            #curMouseCArray = pPool.starmap(pipeline, listOfArgs)
            #for curMouseC in curMouseCArray:

            if x is not None:
                dX = x - lx
                dY = y - ly
                dZ = z - lz
                #print(dX, dY, dZ)

                if (dZ > globals.zMoveDownThr):
                    if (zChangeState == 0):
                        zChangeState = 1
                        zMoveDownStart = lz
                        zMoveDownEnd = lz

                    else:
                       # It is moving down, record last coordintates
                       zChangeState += 1
                       zMoveDownEnd = z
                    lz = z
                    continue #Do not move mouse to make it feel stable
                else:
                    if(zChangeState > 0):
                        # It was moving, but stopped now, this is a possible click

                        if((zMoveDownEnd - zMoveDownStart > globals.clickZThr) and (zChangeState < globals.clickZFrameThr)):
                            mouseCoords.put((x,y,True))
                            print ("Clicked. distance: " + str(zMoveDownEnd - zMoveDownStart) + " frames: " + str(zChangeState))
                            zChangeState = 0
                            lz = z
                            continue


                # Reset and tracking of downward movement
                zChangeState = 0

                # ignore jitter and out of range
                if (abs(dX) < globals.dXMin or abs(dY) < globals.dYMin or abs(dX) > globals.dXMax or abs(dY) > globals.dYMax):
                    continue

                if (z == 0) or (z > backgroundZValue) :
                    lx, ly = x, y
                else:
                    lx, ly, lz = x, y, z

                mouseCoords.put((x,y,False))

            #ct += globals.threadPoolSize
            ct += 1
