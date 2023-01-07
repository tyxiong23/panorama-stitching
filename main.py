import numpy as np
import cv2
from argparse import ArgumentParser
from src.utils.images import Image, get_images
from src.stitcher import Stitcher

import os

if __name__ == "__main__":
    parser = ArgumentParser("Panorama Stitching")
    parser.add_argument(dest="input_dir", help="directory of input images")
    parser.add_argument("--blending", type=str, choices=["no", "simple", "mbb"], default="no")
    parser.add_argument("--gain-compensation", type=str, choices=["no", "yes"], default="yes")
    parser.add_argument("--gain-sigma-n", type=float, default=10, help="sigma_n for gain compensation")
    parser.add_argument("--gain-sigma-g", type=float, default=0.1, help="sigma_g for gain compensation")
    # parser.add_argument()

    args = vars(parser.parse_args())
    args["output_dir"] = os.path.join(args["input_dir"], "result")
    if not os.path.exists(args["output_dir"]):
        os.makedirs(args["output_dir"])

    stitcher = Stitcher(args)

    # load images
    stitcher.load_images()

    # compute sift features
    stitcher.compute_SIFT()

    # image matching and finding connected components (panoramas)
    stitcher.compute_matches()

    # compute homography for each panorama component
    stitcher.build_homographies()

    # compute gain compensation
    if not args["gain_compensation"] == "no":
        stitcher.compute_gain_compensation()

    # generate panorama images with blending
    stitcher.draw_homography()
