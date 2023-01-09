from typing import List, Tuple
import cv2
import numpy as np
import os

from src.utils.images import Image
from src.utils.panorama_utils import get_best_panorama_parameters, get_weight_matrix


def add_image(panorama: np.ndarray, image: Image, weight: np.ndarray, offset: np.ndarray, pano_mask: np.ndarray,
              idX: int, total_num: int):
    assert idX <= 25, "maximum 25 images in a panorama"
    pano_size = (panorama.shape[1], panorama.shape[0])
    image_H = offset @ image.H
    img_weight = get_weight_matrix(image.image.shape)
    img_mask = np.ones_like(image.image, dtype=np.uint8)
    warped_img = cv2.warpPerspective(image.image, image_H, pano_size)
    warped_mask = cv2.warpPerspective(img_mask, image_H, pano_size)
    warped_weight = cv2.warpPerspective(img_weight, image_H, pano_size)
    img_weight = np.expand_dims(warped_weight, axis=2).repeat(3, axis=2)
    # norm_img_weight = np.zeros_like(weight)

    norm_img_weight = np.divide(img_weight, (img_weight + weight), where=(img_weight + weight) != 0)

    panorama = np.where(
        warped_mask + pano_mask == 0,
        0,
        norm_img_weight * warped_img + (1 - norm_img_weight) * panorama
    )
    pano_mask = np.where(
        warped_mask + pano_mask == 0,
        0,
        norm_img_weight * warped_mask * (idX + 1) * (240 // total_num) + (1 - norm_img_weight) * pano_mask
    )

    weight = (weight + img_weight) / (weight + img_weight).max()
    return panorama, weight, pano_mask


def draw_simple_blending(output_dir: str, images: List[Image], pano_id: int, gain_comp: bool = False):
    assert len(images) >= 2, "len(images) < 2"

    shapes_Hs = [(i.image.shape, i.H) for i in images]
    added_offset, pano_size = get_best_panorama_parameters(shapes_Hs)
    # print("added_offsets", added_offset)
    # print("pano_size", pano_size)
    panorama = np.zeros((pano_size[1], pano_size[0], 3), dtype=np.uint8)
    pano_mask = np.zeros_like(panorama, dtype=np.uint8)
    weight = np.zeros_like(panorama, dtype=float)
    for i, image in enumerate(images):
        panorama, weight, pano_mask = add_image(panorama, image, weight, added_offset, pano_mask, i, len(images))
        # mask_path = os.path.join(output_dir, f"panorama_{pano_id}_{i}.png")
        # cv2.imwrite(mask_path, panorama)
    gain_comp_str = "gain_comp" if gain_comp else "no_gain"

    mask_path = os.path.join(output_dir, f"mask_{pano_id}_simple_blending_{gain_comp_str}.png")
    cv2.imwrite(mask_path, pano_mask)
    out_path = os.path.join(output_dir, f"panorama_{pano_id}_simple_blending_{gain_comp_str}.png")
    cv2.imwrite(out_path, panorama)
