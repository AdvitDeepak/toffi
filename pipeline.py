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

    #print(arr, backArrM, backVal, debug, ct, xM, yM)
    start = time.time()
    arrM = arr.copy()
    arrMax = arr.max()
    procId = os.getpid()
    #print ("Running process with pid: " + str(procId) + " tmp image dir: " + tmpImageDir + " Avg of arr: " + str(np.average(arr)))
    arrM = (255.0 / arrMax * (arr - arr.min())).astype(np.uint8)

    if (debug):
        img = Image.fromarray(arrM)
        img.save(tmpImageDir + "00a_original.BMP")

    item = arrM - backArrM

    #itemM = (255.0 / itemM.max() * (item - item.min())).astype(np.uint8)

    if (debug):
        img = Image.fromarray(item)
        img.save(tmpImageDir + "00b_subtracted.BMP")

    avg = np.average(item)
    if (avg < 15 or avg > 240):
        #print("average not within range")
        return None

    #print("     before forLoop: ", (time.time() - start))
    #curTime = time.time()

    itemM = np.zeros((171,224))
    #num255 = 0

    for x in range(0, 170, 3): #171
        for y in range(0, 221, 3): #224
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
        img.save(tmpImageDir + "01_rescaled.BMP")


    #print(" subtracted")
    contours, hierarchy = cv2.findContours(im,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    maxCnt = 500
    maxContour = None
    for cnt in contours:
        val = cv2.arcLength(cnt, True) + cv2.contourArea(cnt)
        if (val > maxCnt and val < 20000):
            maxCnt = val
            maxContour = cnt

    if (maxContour is None):
        #print("maxContour is none")
        return None

    bIm = np.zeros((171,224))
    hull = cv2.convexHull(maxContour)
    bIM = cv2.drawContours(bIm,[hull],0,84,1)

    if (debug):
        cv2.drawContours(im,[maxContour],0,84,1)
        cv2.drawContours(im,[hull],0,168,1)
        cv2.imwrite(tmpImageDir + "03_convexHull.BMP", im)

    cv2.imwrite(tmpImageDir + "04_justHull.BMP", bIm)
    im = cv2.imread(tmpImageDir + "04_justHull.BMP", 0)

    #print("     found contours: ")
    #curTime = time.time()
    #print(" contours")


    M = cv2.moments(maxContour)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    cZ = round(arr[cY][cX], 3)
    if abs(arrMax - cZ) < 0.1:
        #print("abs less than 0.1")
        return None

    corners = cv2.goodFeaturesToTrack(im,8,0.01,10)

    if corners is None:
        #print("no corner")
        return None
    if (len(corners) == 0):
        #print("corner length zero")
        return None

    corners = np.int0(corners)
    #print(" found corners")

    if (debug):
        for corner in corners:
            x, y = corner.ravel()
            cv2.circle(im,(x,y),3,100,-1)
        nIm = Image.fromarray(im)
        nIm.save(tmpImageDir + "05_corners.BMP")

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

    if not gotCorner:
        #print("not gotCorner")
        return None

    if (highestVal == -1000):
        #print("highest value -1000")
        return None

    #print(" highest corner")

    x, y = highestCorner.ravel()
    #print("x: " + str(x) + "y: " + str(y))
    z = round(arr[y][x], 3)
    if (z <= 0.001 or z >= backVal ):
        z = round(arr[y+1][x], 3)
        if (z <= 0.001 or z >= backVal):
            z = round(arr[y-1][x], 3)
            if (z <= 0.001 or z >= backVal):
                z = round(arr[y][x+1], 3)
                if (z <= 0.001 or z >= backVal):
                    z = round(arr[y][x-1], 3)

    #print("       found x,y,z: ", (time.time() - curTime))
    #if (arr.max() - z < 0.1): return None

    if (debug):
        cv2.circle(im,(x,y),3,255,-1)
        img = Image.fromarray(im)
        name = tmpImageDir + "06_corners" + str(ct) + ".BMP"
        img.save(name)

    #print("we wanted to move")

    #print("x: " + str(x) + " y: " + str(y))
    #return (int(x * globals.xM), int(y * globals.yM), z, int(cX * globals.xM), int(cY * globals.yM), cZ)
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
        #print (tmpImageDir[i])
        try:
            if(not os.path.isdir(tmpImageDir[i])):
                os.mkdir(tmpImageDir[i])
        except OSError as error:
            print("Could not make dir: " + tmpImageDir[i])


    pPool = multiprocessing.Pool(globals.threadPoolSize)
    backArr, backgroundZValue = getBackground(frames, options, globals.tmpDir)

    zChangeState = 0
    zMoveDownStart = 0
    zMoveDownEnd = 0
    lastMouseC = (0,0,False)
    ct = 0

    t_end = time.time() + options.seconds
    while time.time() < t_end:
        listOfArgs = []
        try:
            # try to retrieve an item from the queue.
            # this will block until an item can be retrieved
            # or the timeout of 1 second is hit
            item = frames.get(True, 1)

            # for fId in range(globals.threadPoolSize):
            #     item = frames.get(True, 1)
            #     listOfArgs.append([tmpImageDir[fId], item, backArr, backgroundZValue, options.debug, ct+fId, globals.xM, globals.yM])

        except queue.Empty:
            # this will be thrown when the timeout is hit
            break
        else:

            #stTime = time.time()
            curMouseC = pipeline(globals.tmpDir, item, backArr, backgroundZValue, options.debug, ct, globals.xM, globals.yM)
            #curMouseCArray = pPool.starmap(pipeline, listOfArgs)
            #print ("curMouseCArray :", curMouseCArray)
            #print("Pip time: ", (time.time() - stTime))
            #for curMouseC in curMouseCArray:
            if curMouseC is not None:
                (x, y, z) = curMouseC
                click = False

                dX = curMouseC[0] - lastMouseC[0]
                dY = curMouseC[1] - lastMouseC[1]
                #print(dX, dY)
                if (abs(dX) > globals.dXMax or abs(dY) > globals.dYMax or abs(dX) < globals.dXMin or abs(dY) < globals.dYMin):
                    #print("dX and dY out of range")
                    continue

                if(curMouseC[2] == 0) or (curMouseC[2] > backgroundZValue) or ((backgroundZValue - curMouseC[2]) < globals.zNoiseThr):
                    #print("Put prematurely")
                    mouseCoords.put((x,y,click))
                    continue

                dZ = curMouseC[2] - lastMouseC[2]

                #print("(Last, Cur, Diff) Mouse Z: (" + str(lastMouseC[2]) + ", " + str(curMouseC[2]) + ", " + str(dZ) + ")")
                if (dZ > globals.zMoveDownThr):
                    print("Mouse moving down. frames: " + str(zChangeState) + " Z: ", str(curMouseC[2]) + " dZ: " + str(dZ))
                    if (zChangeState == 0):
                        zChangeState = 1
                        zMoveDownStart = lastMouseC[2]
                        print("Click down started. frames: " + str(zChangeState) + " start Z: " + str(zMoveDownStart))
                    else:
                       # It is moving down, record last coordintates
                       zChangeState += 1
                       zMoveDownEnd = curMouseC[2]
                       print("Click down continues at: " + str(zChangeState) + " End Z: " + str(zMoveDownEnd))

                else:
                    if(zChangeState > 0):
                        # It was moving, but stopped now, this is a possible click
                        print ("Check. distance: " + str(zMoveDownEnd - zMoveDownStart) + " frames: " + str(zChangeState))
                        if((zMoveDownEnd - zMoveDownStart > globals.clickZThr) and (zChangeState < globals.clickZFrameThr)):
                            click = True
                            print ("Clicked. distance: " + str(zMoveDownEnd - zMoveDownStart) + " frames: " + str(zChangeState))

                    # Reset and tracking of downward movement
                    zChangeState = 0

                mouseCoords.put((x,y,click))
                #print("Time: " + str(time.time()) + " | x: " + str(x) + " | y: " + str(y) + " | click: " + str(click))
                lastMouseC = curMouseC

            #ct += globals.threadPoolSize
            ct += 1
