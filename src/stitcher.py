import numpy as np
import cv2
import os
import logging

from src.utils.images import Image, get_images
from src.matching.matcher import Matcher




class Stitcher:
    def __init__(self, args) -> None:
        self.input_dir = args.input_dir
        self.output_dir = args.output_dir
        logging.getLogger().setLevel(logging.INFO)
    
    def load_images(self):
        logging.info(f"Load images for {self.input_dir}")
        self.images = get_images(self.input_dir)
        logging.info(f"Find {len(self.images)} images")

    def compute_SIFT(self):
        logging.info(f"Computing SIFT features")
        for image in self.images:
            image.get_sift_feats()

    def compute_matches(self):
        logging.info(f"Computing matches for each pair of images")
        # print(self.images[0].features.shape, len(self.images[0].keypoints))
        self.matcher = Matcher(self.images)
        self.matcher.match()
        self.matcher.connect_components()
        pass

