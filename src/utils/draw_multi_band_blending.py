import cv2
from typing import List, Tuple
import numpy as np
import os

from src.utils.images import Image
from src.utils.panorama_utils import get_best_panorama_parameters, get_weight_matrix, get_weight_parameters


def add_weights(weights_matrix: np.ndarray, image: Image, offset: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    shape = image.image.shape
    H = offset @ image.H
    added_offset, pano_size = get_weight_parameters((shape, H), weights_matrix)

    img_weight = get_weight_matrix(shape)
    weights = cv2.warpPerspective(img_weight, added_offset @ H, pano_size)[:, :, np.newaxis]

    if weights_matrix is None:
        weights_matrix = weights
    else:
        weights_matrix = cv2.warpPerspective(weights_matrix, added_offset, pano_size)

        if len(weights_matrix.shape) == 2:
            weights_matrix = weights_matrix[:, :, np.newaxis]

        weights_matrix = np.concatenate([weights_matrix, weights], axis=2)

    return weights_matrix, added_offset @ offset


def get_max_weights_matrix(images: List[Image], offset=np.eye(3)) -> Tuple[np.ndarray, np.ndarray]:
    weights_matrix = None
    for image in images:
        weights_matrix, offset = add_weights(weights_matrix, image, offset)

    weights_maxes = np.max(weights_matrix, axis=2)[:, :, np.newaxis]
    max_weights_matrix = np.where(np.logical_and(weights_matrix == weights_maxes, weights_matrix > 0), 1.0, 0.0)
    return np.transpose(max_weights_matrix, (2, 0, 1)), offset


def get_band_panorama(panorama: np.ndarray, images: List[Image], weights: List[np.ndarray], bands: List[np.ndarray], offset: np.ndarray,
                      h: int, w: int):
    pano_weights = np.zeros((h, w))
    pano_bands = np.zeros((h, w, 3))

    for i, image in enumerate(images):
        weights_at_scale = cv2.warpPerspective(weights[i], offset @ image.H, (w, h))
        pano_weights += weights_at_scale
        pano_bands += weights_at_scale[:, :, np.newaxis] * cv2.warpPerspective(bands[i], offset @ image.H, (w, h))

    band_panaronma = np.divide(pano_bands, pano_weights[:, :, np.newaxis], where=pano_weights[:, :, np.newaxis] != 0)
    panorama += band_panaronma
    return panorama


def draw_multi_band_blending(output_dir: str, images: List[Image], pano_id: int, num_bands: int = 5,
                             mbb_sigma: float = 1.0, gain_comp: bool = False):
    assert len(images) >= 2, "len(images) < 2"

    max_weights_matrix, offset = get_max_weights_matrix(images)

    max_weights = [
        cv2.warpPerspective(max_weights_matrix[i], np.linalg.inv(offset @ image.H), image.image.shape[:2][::-1]) for
        i, image in enumerate(images)]

    weights = [[cv2.GaussianBlur(max_weights[i], (0, 0), 2 * mbb_sigma) for i in range(len(images))]]
    sigma_images = [cv2.GaussianBlur(image.image, (0, 0), mbb_sigma) for image in images]
    bands = [[np.where(images[i].image.astype(np.int64) - sigma_images[i].astype(np.int64) > 0,
                       images[i].image - sigma_images[i], 0)
              for i in range(len(images))]]

    for k in range(1, num_bands - 1):
        sigma_k = np.sqrt(2 * k + 1) * mbb_sigma
        weights.append([cv2.GaussianBlur(weights[-1][i], (0, 0), sigma_k) for i in range(len(images))])

        old_sigma_images = sigma_images

        sigma_images = [cv2.GaussianBlur(old_sigma_image, (0, 0), sigma_k) for old_sigma_image in old_sigma_images]
        bands.append([np.where(old_sigma_images[i].astype(np.int64) - sigma_images[i].astype(np.int64) > 0,
                               old_sigma_images[i] - sigma_images[i], 0)
                      for i in range(len(images))])

    weights.append([cv2.GaussianBlur(weights[-1][i], (0, 0), sigma_k) for i in range(len(images))])
    bands.append([sigma_images[i] for i in range(len(images))])

    panorama = np.zeros((*max_weights_matrix.shape[1:], 3))
    for i in range(0, num_bands):
        panorama = get_band_panorama(panorama, images, weights[i], bands[i], offset,
                                     max_weights_matrix.shape[1:][0], max_weights_matrix.shape[1:][1])

    gain_comp_str = "gain_comp" if gain_comp else "no_gain"
    out_path = os.path.join(output_dir, f"panorama_{pano_id}_multi_band_blending_{gain_comp_str}.png")
    cv2.imwrite(out_path, panorama)
