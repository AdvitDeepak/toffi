from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper
import roypy_utils.roypy as roypy
import globals, time, queue
import pyautogui


def smoothMove(mouseCoords, options):
    globals.initialize()
    mouseCt = 0

    t_start = time.time()
    t_end = time.time() + options.seconds
    lastToLastC = mouseCoords.get(True, options.seconds)
    z = 0
    cZ = 0
    clickTimeout = False
    clickTime = time.time()
    lastDist = 0
    distDec = 0
    lastDiff = 0

    while time.time() < t_end:
        try:
            lastC = mouseCoords.get(True, options.seconds)
            #continue
        except queue.Empty:
            # this will be thrown when the timeout is hit
            #break
            continue
        else:
            # mouse
            if (time.time() - clickTime > .8): clickTimeout = False
            currX, currY = pyautogui.position()
            if lastC == (-1,-1,-1,-1,-1,-1):
                lastToLastC = (currX,currY,z,currX,currY,cZ)
                continue

            z = lastC[2]
            cZ = lastC[5]
            """
            print(z)
            if z - lastToLastC[2] > 0.
            """
            """
            dist = abs(lastC[0] - lastC[3]) + abs(lastC[1] - lastC[4])
            print("dist: " + str(dist) + " | lastDist: " + str(lastDist) + " | delta: " + str(dist - lastDist))
            """
            """
            dZ = round(lastC[2] - lastToLastC[2], 3)

            diff = round(z - cZ, 3)
            print(diff - lastDiff)
            #print(dZ)
            #print("dZ: " + str(dZ) +  " | dC: " + str(round(z - cZ, 3)))
            """
            """
            if (dZ > globals.clickTh):
                pyautogui.click()
                continue


            if round(z - cZ, 3) < 0.1 and not clickTimeout:
                print("we wanna click!")
                #distDec = 0
                clickTime = time.time()
                clickTimeout = True
                #pyautogui.click()
                continue
            """
            #zDiff = round((lastC[2] - lastC[3]) - (lastToLastC[2] - lastToLastC[3]), 3)
            #dist = (lastC[0] - lastC[3]) + (lastC[1] - lastC[4]) - (lastToLastC[0] - lastToLastC[3]) - (lastToLastC[1] - lastToLastC[4])
            #print("dz: " + str(dZ) + " | zDiff: " + str(zDiff))
            #print("delta dist: ", dist)
            """

            if distDec > 2 and not clickTimeout:
                #print("we wanna click!")
                distDec = 0
                clickTime = time.time()
                clickTimeout = True
                pyautogui.click()
                continue

            if (dist - lastDist < -70):
                #print(" incremented distDec")
                distDec += 1
                continue
            """

            # Mouse move
            dX = lastC[0] - lastToLastC[0]
            dY = lastC[1] - lastToLastC[1]

            if (abs(dX) > globals.dXMax or abs(dY) > globals.dYMax): continue
            if (abs(dX) < globals.dXMin or abs(dY) < globals.dYMin): continue
            pyautogui.move((lastC[0] - currX)/2, (lastC[1] - currY)/2)

            #print("dx:" + str(dX) + " dy:" + str(dY) + " dz:" + str(dZ))
            lastToLastC = lastC

            if (time.time() - t_start < globals.mouseUpdateRate):
                time.sleep(globals.mouseUpdateRate - (time.time() - t_start))
