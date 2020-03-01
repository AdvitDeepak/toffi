from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper
import roypy_utils.roypy as roypy
import globals, time, queue
import pyautogui


def smoothMove(mouseCoords, options):
    globals.initialize()
    mouseCt = 0
    # 0: not moving down, 1: started to move down or moving down
    zChangeState = 0
    zMoveDownStart = 0
    zMoveDownEnd = 0
    zMoveStartTime = 0
    zMoveEndTime = 0
    curMouseCTime = 0
    lastMouseCTime = 0
    downZMove = False
    backgroundZValue = mouseCoords.get(True, options.seconds)
    print("background:", backgroundZValue)

    t_start = time.time()
    t_end = time.time() + options.seconds
    lastMouseCTime = time.time()
    (x, y, z, cx, cy, cz) = mouseCoords.get(True, options.seconds)
    lastMouseC = (x, y, 1, cx, cy, cz)
    cursor = 0
    centerMouseZ = 1
    lastMouseZ = 1


    while time.time() < t_end:
        try:
            curMouseCTime = time.time()
            curMouseC = mouseCoords.get(True, options.seconds)
            #continue
        except queue.Empty:
            # this will be thrown when the timeout is hit
            #break
            #print ("queue empty")
            continue
        else:
            # mouse

            cursorX, cursorY = pyautogui.position()
            if curMouseC == (-1,-1,-1,-1,-1,-1):
                # No hand detected, set coordinate to current cursor position, use last mouse Z for depth
                lastMouseC = (cursorX, cursorY, lastMouseZ, cursorX, cursorY, centerMouseZ)
                continue

            #print("Z: ", curMouseC[2])
            # For black spots, or setecting far off back ground object, skip
            if(curMouseC[2] == 0) or (curMouseC[2] > backgroundZValue) or ((backgroundZValue - curMouseC[2]) < globals.zNoiseThr):
               continue

            dX = curMouseC[0] - lastMouseC[0]
            dY = curMouseC[1] - lastMouseC[1]
            dZ = curMouseC[2] - lastMouseC[2]
            lastMouseZ = curMouseC[2] # store current hand coordinate for case when no hand is seen
            #print("(Last, Cur, Diff) Mouse Z: (" + str(lastMouseC[2]) + ", " + str(curMouseC[2]) + ", " + str(dZ) + ")")
            if (dZ > globals.zMoveDownThr):
                #print("Mouse moving down at: " + str(curMouseCTime) + " Z: ", str(curMouseC[2]) + " dZ: " + str(dZ))
                if (zChangeState == 0):
                    zChangeState = 1
                    zMoveStartTime = lastMouseCTime
                    zMoveDownStart = lastMouseC[2]
                    zMoveEndTime = zMoveStartTime + globals.smallDelta;
                    #print("Click down started at: " + str(zMoveStartTime) + " start Z: " + str(zMoveDownStart))
                else:
                   # It is moving down, record last coordintates
                   zMoveDownEnd = curMouseC[2]
                   zMoveEndTime = curMouseCTime
                   #print("Click down continues at: " + str(zMoveEndTime) + " End Z: " + str(zMoveDownEnd))
            else:
                if(zChangeState > 0):
                    # It was moving, but stopped now, this is a possible click
                    downZMove = True
                    #print("click down ended at: " + str(zMoveEndTime) + " End Z: " + str(zMoveDownEnd))
                    #print("click down end detected at: " + str(curMouseCTime) + " Z: " + str(curMouseC[2]))
                # Reset and tracking of downward movement
                zChangeState = 0

            if(downZMove == True):
                downZMove = False
                clickZDistance = zMoveDownEnd - zMoveDownStart
                clickZTime = zMoveEndTime - zMoveStartTime
                #print ("Check. distance: " + str(clickZDistance) + " duration: " + str(clickZTime))
                if((clickZDistance > globals.clickZThr) and (clickZTime < globals.clickZTimeThr)):
                    pyautogui.click()
                    print ("Clicked. distance: " + str(clickZDistance) + " duration: " + str(clickZTime))

            lastMouseC = curMouseC
            lastMouseCTime = curMouseCTime

            # Mouse move
            if (abs(dX) > globals.dXMax or abs(dY) > globals.dYMax): continue
            if (abs(dX) < globals.dXMin or abs(dY) < globals.dYMin): continue
            pyautogui.move((curMouseC[0] - cursorX)/2, (curMouseC[1] - cursorY)/2)
            #print("dx:" + str(dX) + " dy:" + str(dY) + " dz:" + str(dZ))
