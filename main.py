import numpy as np
import cv2
from argparse import ArgumentParser
from src.utils.images import Image, get_images
from src.stitcher import Stitcher


import os



if __name__ == "__main__":
    parser = ArgumentParser("Panorama Stitching")
    parser.add_argument(dest="input_dir", help="directory of input images")
    # parser.add_argument()

    args = parser.parse_args()
    args.output_dir = os.path.join(args.input_dir, "result")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    
    stitcher = Stitcher(args)

    ### load images
    stitcher.load_images()

    ### compute sift features
    stitcher.compute_SIFT()

    ## image matching and finding components
    stitcher.compute_matches()

    
    
    ## matching image

