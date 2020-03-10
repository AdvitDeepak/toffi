import argparse
from roypy_utils import roypy
import time
import queue
from roypy_utils.roypy_sample_utils import CameraOpener, add_camera_opener_options
from roypy_utils.roypy_platform_utils import PlatformHelper

import numpy as np
import matplotlib.pyplot as plt

import multiprocessing
from pipeline import procPip
from mouse import smoothMove

class MyListener(roypy.IDepthDataListener):
    def __init__(self, q):
        super(MyListener, self).__init__()
        self.queue = q

    def onNewData(self, data):
        zvalues = []
        for i in range(data.getNumPoints()):
            zvalues.append(data.getZ(i))
        zarray = np.asarray(zvalues)
        p = zarray.reshape (-1, data.width)
        self.queue.put(p)

def main ():
    platformhelper = PlatformHelper()
    parser = argparse.ArgumentParser (usage = __doc__)
    add_camera_opener_options (parser)
    parser.add_argument ("--seconds", type=int, default=600, help="duration to capture data")
    parser.add_argument ("--debug", type=bool, default=False, help="save intermediate images")
    options = parser.parse_args()
    opener = CameraOpener (options)
    cam = opener.open_camera ()
    cam.setUseCase("MODE_5_45FPS_500")

    print("isConnected", cam.isConnected())
    print("getFrameRate", cam.getFrameRate())
    print("getUseCase: ", cam.getCurrentUseCase())

    frames = multiprocessing.Queue()
    mouseCoords = multiprocessing.Queue()


    pPipeline = multiprocessing.Process(target=procPip, args=(frames,mouseCoords,options,))
    pMouse = multiprocessing.Process(target=smoothMove, args=(mouseCoords,options,))

    pMouse.start()
    pPipeline.start()

    # we will use this queue to synchronize the callback with the main
    # thread, as drawing should happen in the main thread
    q = queue.Queue()
    l = MyListener(q)
    cam.registerDataListener(l)
    cam.startCapture()
    # create a loop that will run for a time (default 15 seconds)
    process_event_queue (q, l, frames, options.seconds)
    cam.stopCapture()

def process_event_queue (q, painter, frames, seconds):
    # create a loop that will run for the given amount of time
    t_end = time.time() + seconds
    while time.time() < t_end:
        try:
            # try to retrieve an item from the queue.
            # this will block until an item can be retrieved
            # or the timeout of 1 second is hit
            item = q.get(True)
        except queue.Empty:
            # this will be thrown when the timeout is hit
            continue
        else:
            frames.put(item, True)

if (__name__ == "__main__"):
    main()
