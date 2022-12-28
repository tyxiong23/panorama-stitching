from src.utils.images import Image

import cv2
import numpy as np


class PairMatch(object):
    def __init__(self, idA: int, idB: int, imageA: Image, imageB: Image, matches = None) -> None:
        self.idA = idA
        self.idB = idB
        self.imageA = imageA
        self.imageB = imageB
        self.matches = matches
        
        self.H: np.ndarray = None
        self.status = None
        self.matchedKpts_a = None # 匹配特征点在A中坐标
        self.matchedKpts_b = None # 匹配特征点在B中坐标
        self.overlap = None # 重合区域
        self.overlap_area = None # 重合面积
        self.MIN_OVERLAP_MATCHES = 3 # (xty:我设了一个在overlap区域最少的match数量，原来没有)
        pass

    def compute_homography(self, ransac_reproj_thr: float = 5, ransac_maxiters: int = 500):
        self.matchedKpts_a = np.float32([self.imageA.keypoints[match.queryIdx].pt for match in self.matches])
        self.matchedKpts_b = np.float32([self.imageB.keypoints[match.trainIdx].pt for match in self.matches])
        
        self.H, self.status = cv2.findHomography(
            self.matchedKpts_a, self.matchedKpts_b, cv2.RANSAC, 
            ransacReprojThreshold=ransac_reproj_thr,
            maxIters=ransac_maxiters
        )
        # print("HOMO", self.matchedKpts_a.shape, self.status.shape, self.matchedKpts_a[:5])
    
    def compute_overlap(self):
        if self.H is None:
            self.compute_homography()
        shapeA = self.imageA.image.shape
        # print("before overlap", shapeA[1::-1], self.H.shape, np.ones_like(self.imageB.image[..., 0], dtype=int).shape, np.uint8)
        self.overlap = cv2.warpPerspective(np.ones_like(self.imageB.image[..., 0], dtype=np.uint8), self.H, shapeA[1::-1])
        self.overlap_area = self.overlap.sum()


    
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
        print(f"NUM_match_overlap {self.idA} -> {self.idB}", num_matched_in_overlap)

        ### 对应于overlap的区域而言，有足够多的inlier, 同时重合区域有一定的特征点可以匹配上
        return self.status.sum() >= alpha + beta * num_matched_in_overlap and num_matched_in_overlap >= self.MIN_OVERLAP_MATCHES 

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
