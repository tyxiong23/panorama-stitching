import numpy as np
import cv2
import os
import logging

from src.utils.images import Image, get_images
from src.matching.matcher import Matcher
from src.matching.pair_match import PairMatch
from src.utils.draw_simple_blending import draw_simple_blending
from src.utils.draw_no_blending import draw_no_blending
from src.utils.draw_multi_band_blending import draw_multi_band_blending
from src.optimizations.gain_compensation import gain_compensation
from typing import List


class Stitcher:
    def __init__(self, args) -> None:
        self.input_dir = args["input_dir"]
        self.output_dir = args["output_dir"]
        self.images = []
        logging.getLogger().setLevel(logging.INFO)
        self.matcher = None
        self.panorama_components = None
        self.components_matches = None
        self.blending = args["blending"]
        self.gain_comp = args["gain_compensation"] == "yes"
        self.n = args["gain_sigma_n"]
        self.g = args["gain_sigma_g"]

    def load_images(self):
        logging.info(f"Load images for {self.input_dir}")
        self.images = get_images(self.input_dir)
        logging.info(f"Find {len(self.images)} images")

    def get_image(self, idx: int):
        assert 0 <= idx < len(self.images)
        return self.images[idx]

    def compute_SIFT(self):
        logging.info(f"Computing SIFT features")
        for image in self.images:
            image.get_sift_feats()

    def compute_matches(self):
        logging.info(f"Computing matches for each pair of images")
        # print(self.images[0].features.shape, len(self.images[0].keypoints))
        self.matcher = Matcher(self.images)
        self.matcher.match()
        self.panorama_components, self.components_matches = self.matcher.connect_components()

    def build_homographies(self):
        # 计算homography矩阵，合并结果
        for pano_id, pair_matches in enumerate(self.components_matches):
            logging.info(f"Computing homography matrices for panorama {pano_id}")
            pair_matches_copy: List[PairMatch] = pair_matches.copy()
            tmp_match = pair_matches_copy.pop(0)
            imgA, imgB = self.get_image(tmp_match.idA), self.get_image(tmp_match.idB)
            imgA.H = np.eye(3)
            imgB.H = tmp_match.homography
            added_images = set([tmp_match.idA, tmp_match.idB])
            while len(pair_matches_copy) > 0:
                print("add_images", added_images)
                for i, pair_match in enumerate(pair_matches_copy):
                    idA, idB = pair_match.idA, pair_match.idB
                    imgA, imgB = self.get_image(idA), self.get_image(idB)
                    if idB not in added_images and idA not in added_images:
                        continue
                    elif idB not in added_images:
                        imgB.H = imgA.H @ pair_match.homography
                        added_images.add(idB)
                        pair_matches_copy.pop(i)
                        break
                    elif idA not in added_images:
                        imgA.H = imgB.H @ np.linalg.inv(pair_match.homography)
                        added_images.add(idA)
                        pair_matches_copy.pop(i)
                        break
                    else:
                        return NotImplementedError

    def compute_gain_compensation(self):
        logging.info(f"Computing gain compensation")
        for component_id in range(len(self.matcher.connected_components)):
            curr_component = self.matcher.connected_components[component_id]
            curr_images = []
            for c in curr_component:
                curr_images.append(self.images[c])
            curr_matches = [
                pair_match for pair_match in self.matcher.pair_matches
                if pair_match.imageA in curr_images
            ]
            gain_compensation(curr_images, curr_matches, sigma_n=self.n, sigma_g=self.g)
        for image in self.images:
            image.image = (image.image * image.gain[np.newaxis, np.newaxis, :]).astype(np.uint8)
        return

    def draw_homography(self):
        for pano_id, panorama_component in enumerate(self.panorama_components):
            logging.info(f"Draw panorama {pano_id} with {self.blending} blending...")
            images = [self.images[i] for i in panorama_component]
            if self.blending == "no":
                draw_no_blending(self.output_dir, images, pano_id, gain_comp=self.gain_comp)
            if self.blending == "simple":
                draw_simple_blending(self.output_dir, images, pano_id, gain_comp=self.gain_comp)
            if self.blending == "mbb":
                draw_multi_band_blending(self.output_dir, images, pano_id, gain_comp=self.gain_comp)
        # for component_id
        # if simple_blending:
