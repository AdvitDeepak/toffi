from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper
import roypy_utils.roypy as roypy
import globals, time, queue
import pyautogui


def smoothMove(mouseCoords, options):
    globals.initialize()
    mouseCt = 0

    t_end = time.time() + options.seconds
    lastToLastC = mouseCoords.get(True, options.seconds)

    while time.time() < t_end:
        try:
            lastC = mouseCoords.get(True, options.seconds)
        except queue.Empty:
            # this will be thrown when the timeout is hit
            #break
            continue
        else:
            # mouse
            dX = lastC[0] - lastToLastC[0]
            dY = lastC[1] - lastToLastC[1]
            dZ = lastC[2] - lastToLastC[2]
            print(dZ)
            if (dZ > globals.clickTh):
                pyautogui.click()
                continue

            currX, currY = pyautogui.position()

            if (abs(dX) > globals.dXMax or abs(dY) > globals.dYMax): continue
            if (abs(dX) < globals.dXMin or abs(dY) < globals.dYMin): continue
            pyautogui.move(lastC[0] - currX, lastC[1] - currY)

            #print("dx:" + str(dX) + " dy:" + str(dY) + " dz:" + str(dZ))
            lastToLastC = lastC


    """
    t_end = time.time() + options.seconds

    lastToLastC = mouseCoords.get(True, options.seconds)

    while time.time() < t_end:
        start = time.time()
        lastC = mouseCoords.get(True, options.seconds)

        dX = lastC[0] - lastToLastC[0]
        dY = lastC[1] - lastToLastC[1]
        dZ = lastC[2] - lastToLastC[2]

        # Check for click
        if (dZ > globals.clickTh):
            #pyautogui.click()
            continue

        # If no click, move
        currX, currY = pyautogui.position()

        if (abs(dX) > globals.dXTh or abs(dY) > globals.dYTh): continue
        pyautogui.move(lastC[0] - currX, lastC[1] - currY)

        ct += 1
        lastToLastC = lastC

        if (time.time() - start < globals.wait):
            time.sleep(globals.wait - (time.time() - start))

    print("We did " + str(ct) + " frames in " + str(options.seconds))
    """
