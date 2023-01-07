from src.utils.images import Image, get_images
from typing import List
from src.matching.pair_match import PairMatch

import cv2
import logging

"""
1. find matchers for each image pairs
2. get connected components for each panorama
"""


class Matcher:
    def __init__(self, images: List[Image], dist_ratio: float = 0.75) -> None:
        self.images = images
        self.num_images = len(images)
        self.dist_ratio = dist_ratio
        self.pair_matches = None
        self.connected_components = None
        self.components_matches = None

    def match(self, max_images: int = 6) -> List[PairMatch]:
        self.pair_matches = []
        for i in range(self.num_images - 1):
            match_list = []
            for j in range(i + 1, self.num_images):
                match_list.append(self.compute_raw_match(i, j))
            match_list = sorted(match_list, key=lambda x: len(x), reverse=True)[:max_images]  # 按照 match 数量多少排序
            # print([len(i) for i in match_list])
            for match in match_list:
                if match.is_valid:
                    print(f"add_raw_match {match.idA} -> {match.idB}")
                    self.pair_matches.append(match)

    ### 划分不同的全景图
    def connect_components(self):
        self.connected_components, self.components_matches = [], []
        components_id = 0
        pair_matches = self.pair_matches.copy()
        pair_matches = sorted(pair_matches, key=lambda x: len(x), reverse=True)

        # 不考虑落单的照片单独放成一类
        while len(pair_matches) > 0:
            tmp_match: PairMatch = pair_matches.pop(0)
            connected_component = set([tmp_match.idA, tmp_match.idB])
            component_matches = [tmp_match]

            # 每一个component只需要遍历一次
            while True:
                iffind = False
                idx = 0
                while (idx < len(pair_matches)):
                    # print("idx - len", idx, len(pair_matches))
                    tmp_match = pair_matches[idx]
                    if (tmp_match.idA in connected_component) ^ (tmp_match.idB in connected_component):
                        connected_component.update([tmp_match.idA, tmp_match.idB])
                        pair_matches.pop(idx)
                        component_matches.append(tmp_match)
                        iffind = True
                    elif (tmp_match.idA in connected_component) and (tmp_match.idB in connected_component):
                        pair_matches.pop(idx)
                    else:
                        idx += 1
                if not iffind:
                    break

            self.connected_components.append(list(connected_component))
            self.components_matches.append(component_matches)
            for idx in connected_component:
                self.images[idx].components_id = components_id
            logging.info(f"find connected components {components_id}\t " + str(connected_component))
            components_id += 1

        return self.connected_components, self.components_matches

    # 计算第i,j个图像之间的matching
    def compute_raw_match(self, i: int, j: int) -> PairMatch:
        imgA, imgB = self.images[i], self.images[j]
        matcher = cv2.DescriptorMatcher_create("BruteForce")
        rawMatches = matcher.knnMatch(imgA.features, imgB.features, 2)

        matches = []
        for m, n in rawMatches:
            if m.distance < n.distance * self.dist_ratio:
                matches.append(m)

        return PairMatch(i, j, imgA, imgB, matches)
