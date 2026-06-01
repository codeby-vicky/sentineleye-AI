import mss
import time
import numpy as np

def test():
    print("Capturing in 2 seconds...")
    time.sleep(2)
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        
        # Check if the image contains the red color (the red window)
        # Red is [0, 0, 255] in BGR
        red_pixels = np.sum((img[:, :, 2] > 200) & (img[:, :, 1] < 50) & (img[:, :, 0] < 50))
        print(f"Red pixels found: {red_pixels}")

test()
