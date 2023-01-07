import numpy as np

from typing import List
from src.matching.pair_match import PairMatch
from src.utils.images import Image


def gain_compensation(images: List[Image], pair_matches: List[PairMatch], sigma_n: 10.0, sigma_g: 0.1):
    ks = []
    rs = []
    for j, image in enumerate(images):
        k = [np.zeros(3) for img in range(len(images))]
        r = np.zeros(3)
        for pm in pair_matches:
            if image == pm.imageA:
                k[j] += ((2 * pm.Iab ** 2 / sigma_n ** 2) + (1 / sigma_g ** 2)) * pm.overlap_area
                i = images.index(pm.imageB)
                k[i] -= 2 * pm.Iab * pm.Iba * pm.overlap_area / sigma_n ** 2
                r += pm.overlap_area / sigma_g ** 2
            elif image == pm.imageB:
                k[j] += ((2 * pm.Iba ** 2 / sigma_n ** 2) + (1 / sigma_g ** 2)) * pm.overlap_area
                i = images.index(pm.imageA)
                k[i] -= 2 * pm.Iab * pm.Iba * pm.overlap_area / sigma_n ** 2
                r += pm.overlap_area / sigma_g ** 2
        ks.append(k)
        rs.append(r)

    ks = np.array(ks)
    rs = np.array(rs)
    gains = np.zeros_like(rs)

    for channel in range(ks.shape[2]):
        augmented_ks = ks[:, :, channel]
        augmented_rs = rs[:, channel]
        gains[:, channel] = np.linalg.solve(augmented_ks, augmented_rs)

    # if gain is too large
    max_pixel_value = np.max([img.image for img in images])
    if gains.max() * max_pixel_value > 255:
        gains = gains / (gains.max() * max_pixel_value) * 255

    for i, image in enumerate(images):
        image.gain = gains[i]
        print(gains[i])
    return
