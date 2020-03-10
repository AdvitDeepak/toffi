from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper
import roypy_utils.roypy as roypy
import globals, time, queue
import pyautogui


def smoothMove(mouseCoords, options):
    globals.initialize()
    mouseCt = 0
    # 0: not moving down, 1: started to move down or moving down

    t_start = time.time()
    t_end = time.time() + options.seconds
    lastMouseCTime = time.time()


    while time.time() < t_end:
        try:
            curMouseCTime = time.time()
            curMouseC = mouseCoords.get(True, options.seconds)
        except queue.Empty:
            # this will be thrown when the timeout is hit
            print ("mouse except")
            continue
        else:
            # mouse
            if curMouseC[2]:
                pyautogui.click()
                continue

            cursorX, cursorY = pyautogui.position()

            # Mouse move
            pyautogui.move((curMouseC[0] - cursorX)/2, (curMouseC[1] - cursorY)/2)
