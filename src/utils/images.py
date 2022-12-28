import numpy as np
import cv2
from typing import List
from glob import glob
import os

IMAGE_SUFFIX = [".jpg", ".jpeg", ".bmp", ".png"]

class Image:
    def __init__(self, path) -> None:
        self.path = path
        self.image = cv2.imread(path)
        self.keypoints = None
        self.features = None
        self.components_id: int = -1 # 属于第几张图
        self.H: np.ndarray = np.eye(3)
        self.gain: np.ndarray = np.ones(3, dtype=float)
        # print(self.image.shape, self.path)

    def get_sift_feats(self):
        if (self.keypoints == None or self.features == None):
            descriptor = cv2.SIFT_create()
            self.keypoints, self.features = descriptor.detectAndCompute(self.image, None)
        return (self.keypoints, self.features)

def get_images(dir) -> List[Image]:
    paths, images = [], []
    for suffix in IMAGE_SUFFIX:
        paths += glob(os.path.join(dir, "*"+suffix), recursive=False)
    for pth in paths:
        images.append(Image(pth))
    return images



if __name__ == "__main__":
    pth = "inputs/dongcao"
    images = get_images(pth)
    kpts, features = images[0].get_sift_feats()
    print("kpts", len(kpts))