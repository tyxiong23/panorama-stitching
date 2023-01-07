from src.utils.images import Image

import cv2
import numpy as np


class PairMatch(object):
    def __init__(self, idA: int, idB: int, imageA: Image, imageB: Image, matches=None) -> None:
        self.idA = idA
        self.idB = idB
        self.imageA = imageA
        self.imageB = imageB
        self.matches = matches

        self.H: np.ndarray = None
        self.status = None
        self.matchedKpts_a = None  # 匹配特征点在A中坐标
        self.matchedKpts_b = None  # 匹配特征点在B中坐标
        self.overlap = None  # 重合区域
        self.overlap_area = None  # 重合面积
        self.MIN_OVERLAP_MATCHES = 3  # (xty:我设了一个在overlap区域最少的match数量，原来没有)
        self.Iab = None
        self.Iba = None
        pass

    def compute_homography(self, ransac_reproj_thr: float = 5, ransac_maxiters: int = 500):
        self.matchedKpts_a = np.float32([self.imageA.keypoints[match.queryIdx].pt for match in self.matches])
        self.matchedKpts_b = np.float32([self.imageB.keypoints[match.trainIdx].pt for match in self.matches])

        self.H, self.status = cv2.findHomography(
            self.matchedKpts_b, self.matchedKpts_a, cv2.RANSAC,
            ransacReprojThreshold=ransac_reproj_thr,
            maxIters=ransac_maxiters
        )
        # print("HOMO", self.matchedKpts_a.shape, self.status.shape, self.matchedKpts_a[:5])

    def compute_overlap(self):
        if self.H is None:
            self.compute_homography()
        shapeA = self.imageA.image.shape
        # print("before overlap", shapeA[1::-1], self.H.shape, np.ones_like(self.imageB.image[..., 0], dtype=int).shape, np.uint8)
        self.overlap = cv2.warpPerspective(np.ones_like(self.imageB.image[..., 0], dtype=np.uint8), self.H,
                                           shapeA[1::-1])
        self.overlap_area = self.overlap.sum()
        self.compute_intensity_within_match()

    @property
    def homography(self):
        if self.status is None:
            self.compute_homography()
        return self.H

    @property
    def is_valid(self, alpha: float = 8, beta: float = 0.3):

        # 至少4个match才可以计算Homography矩阵
        if len(self) <= 4:
            return False
        if self.H is None:
            self.compute_homography()
            if self.H is None:
                return False
        if self.overlap is None:
            self.compute_overlap()

        matched_in_overlap = self.matchedKpts_a[
            self.overlap[
                self.matchedKpts_a[:, 1].astype(int),
                self.matchedKpts_a[:, 0].astype(int)
            ] > 0
            ]
        num_matched_in_overlap = matched_in_overlap.shape[0]
        # print(f"NUM_match_overlap {self.idA} -> {self.idB}", num_matched_in_overlap)

        ### 对应于overlap的区域而言，有足够多的inlier, 同时重合区域有一定的特征点可以匹配上
        return self.status.sum() >= alpha + beta * num_matched_in_overlap and num_matched_in_overlap >= self.MIN_OVERLAP_MATCHES

    def compute_intensity_within_match(self):
        if self.overlap is None:
            self.compute_overlap()
        n = self.overlap_area
        if n < self.MIN_OVERLAP_MATCHES:
            print("not safe for gain compensation")
            return
        inverse_overlap = cv2.warpPerspective(self.overlap, np.linalg.inv(self.H), self.imageB.image.shape[1::-1])
        self.Iab = np.sum(self.imageA.image * np.repeat(self.overlap[:, :, np.newaxis], 3, axis=2), axis=(0, 1)) / n
        self.Iba = np.sum(self.imageB.image * np.repeat(inverse_overlap[:, :, np.newaxis], 3, axis=2), axis=(0, 1)) / inverse_overlap.sum()

    def __len__(self):
        return len(self.matches)

    # def __lt__(self, other):
    #     return len(self) < len(other)

    # def __gt__(self, other):
    #     return len(self) > len(other)

    # def __eq__(self, other):
    #     return len(self) == len(other)

    # def __ne__(self, other) -> bool:
    #     return len(self) != len(other)
