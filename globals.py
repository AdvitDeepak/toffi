import numpy as np
import pyautogui
import queue

def initialize():

    global xM
    global yM
    screenDim = pyautogui.size()
    xM = round(screenDim[0] / 224,3)
    yM = round(screenDim[1] / 171, 3)

    global dXMax
    global dYMax
    dXMax = xM * 150
    dYMax = yM * 150

    global dXMin
    global dYMin
    dXMin = xM * 1
    dYMin = yM * 1

    global smallDelta
    smallDelta = 0.00001

    global clickTh
    clickTh = 0.55

    global wait
    wait = 0.05

    global sampleRate
    sampleRate = 1

    global mouseUpdateRate
    mouseUpdateRate = 0

    global clickXThr
    clickXThr = xM * 5

    global clickYThr
    clickYThr = yM * 5

    global zNoiseThr
    zNoiseThr = 0.05

    global zMoveDownThr
    zMoveDownThr = 0.01 # meters

    global clickZThr
    clickZThr = 0.04 # meters

    global clickZTimeThr
    clickZTimeThr = .3 # seconds

    # Any duration less than this is rounded to 0.0 to instantly move the mouse.
    pyautogui.MINIMUM_DURATION = 0.05  # Default: 0.1
    # Minimal number of seconds to sleep between mouse moves.
    pyautogui.MINIMUM_SLEEP = 0  # Default: 0.05
    # The number of seconds to pause after EVERY public function call.
    pyautogui.PAUSE = 0  # Default: 0.1
