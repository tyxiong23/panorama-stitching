from typing import List, Tuple
import cv2
import numpy as np
import os

from src.utils.images import Image
from src.utils.panorama_utils import get_best_panorama_parameters

def add_image(panorama: np.ndarray, image: Image, offset: np.ndarray, pano_mask: np.ndarray, idX: int, total_num: int):
    pano_size = (panorama.shape[1], panorama.shape[0])
    image_H = offset @ image.H
    img_mask = np.ones_like(image.image, dtype=np.uint8)
    warped_img = cv2.warpPerspective(image.image, image_H, pano_size)
    warped_mask = cv2.warpPerspective(img_mask, image_H, pano_size)
    pano_mask = np.where(warped_mask != 0, (idX+1) * (240 // total_num), pano_mask) # mask 图
    panorama = np.where(warped_mask != 0, warped_img, panorama) # 全景图
    return panorama, pano_mask
    

def draw_no_blending(output_dir: str, images: List[Image], pano_id: int):
    assert len(images) >= 2, "len(images) < 2"
    
    shapes_Hs = [(i.image.shape, i.H) for i in images]
    added_offset, pano_size = get_best_panorama_parameters(shapes_Hs)
    # print("added_offsets", added_offset)
    # print("pano_size", pano_size)
    panorama = np.zeros((pano_size[1], pano_size[0], 3), dtype=np.uint8)
    pano_mask = np.zeros_like(panorama, dtype=np.uint8)
    for i, image in enumerate(images):
        panorama, pano_mask = add_image(panorama, image, added_offset, pano_mask, i, len(images))

    mask_path = os.path.join(output_dir, f"mask_{pano_id}_no_blending.png")
    cv2.imwrite(mask_path, pano_mask)
    out_path = os.path.join(output_dir, f"panorama_{pano_id}_no_blending.png")
    cv2.imwrite(out_path, panorama)
