from typing import List, Tuple
import numpy as np



def get_warped_corners(original_shape, H):
    h, w = original_shape[:2]
    corners = np.array([0,0,0,h,w,0,w,h], dtype=float).reshape(4,2)
    corners_prime = np.concatenate([corners, np.ones((4, 1), dtype=float)], axis=1)
    # print("H", H)
    warped_corners_prime = (H @ corners_prime.T).T
    warped_corners = warped_corners_prime[:, :2] / warped_corners_prime[:, 2][:, np.newaxis]
    # print(warped_corners_prime)
    return warped_corners


def get_offset(corners):
    offx, offy = max(0, -float(min(corners[:3][0][0], corners[:3][2][0]))), max(0, -float(min(corners[:3][0][1], corners[:3][1][1])))
    return np.array([[1, 0, offx],[0, 1, offy],[0, 0, 1],],np.float32)


def get_weight_parameters(shape_H: Tuple, panorama: np.ndarray):
    corners = get_warped_corners(shape_H[0], shape_H[1])
    added_offset = get_offset(corners)
    corners = get_warped_corners(shape_H[0], added_offset @ shape_H[1])
    if panorama is None:
        corners_images = [corners]
    else:
        corners_panorama = get_warped_corners(panorama.shape, added_offset)
        corners_images = [corners, corners_panorama]
    corners_images = np.concatenate(corners_images, axis=0)
    deltaX = int(np.ceil(corners_images[:, 0].max()) - np.floor(corners_images[:, 0].min()))
    deltaY = int(np.ceil(corners_images[:, 1].max()) - np.floor(corners_images[:, 1].min()))
    panorama_size = (deltaX, deltaY)
    return added_offset, panorama_size

def get_panorama_parameters(shapes_Hs: List[Tuple], trans = np.eye(3, dtype=float)):
    warped_corners_list: List[np.ndarray] = [
        get_warped_corners(img_shape, trans @ H) for (img_shape, H) in shapes_Hs
    ]
    warped_corners = np.concatenate(warped_corners_list, axis=0)
    offx, offy = -warped_corners[:,0].min(), -warped_corners[:,1].min()
    offset = np.array([1,0,offx,0,1,offy,0,0,1], dtype=float).reshape((3,3)) @ trans # 保证新加入的图片的坐标非负
    deltaX = int(np.ceil(warped_corners[:,0].max()) - np.floor(warped_corners[:,0].min()))
    deltaY = int(np.ceil(warped_corners[:,1].max()) - np.floor(warped_corners[:,1].min()))
    panorama_size = (deltaX, deltaY)
    # print("warped_corners", warped_corners, panorama_size)
    # print("pano", panorama_size)

    return offset, panorama_size

def get_best_panorama_parameters(shape_Hs: List[Tuple]):
    offset, pano_size = get_panorama_parameters(shape_Hs)
    for _, offH in shape_Hs:
        tmp_offset, tmp_pano_size = get_panorama_parameters(shape_Hs, np.linalg.inv(offH))
        if tmp_pano_size[1] < pano_size[1]:
            offset = tmp_offset
            pano_size = tmp_pano_size
    for _, offH in shape_Hs:
        tmp_offset, tmp_pano_size = get_panorama_parameters(shape_Hs, np.linalg.inv(offH))
        if tmp_pano_size[1] < pano_size[1]:
            offset = tmp_offset
            pano_size = tmp_pano_size
    return offset, pano_size



def get_weight_array(length: int):
    weight_array = np.zeros((length,), dtype=float)
    halfLen = (length + 1) // 2
    weight_array[:halfLen] = np.linspace(0,1,halfLen)
    weight_array[-halfLen:] = weight_array[:halfLen][::-1]
    return weight_array


def get_weight_matrix(shape: Tuple[int]):
    assert len(shape) >= 2
    return (
        get_weight_array(shape[0])[:, np.newaxis] @ 
        get_weight_array(shape[1])[np.newaxis, :]
    )

if __name__ == "__main__":
    print(get_weight_array(5))
    print(get_weight_array(6))
    print(get_weight_matrix((5,5)))
    x, y, theta = 300, 0, np.pi / 180 * 20 
    M = [np.cos(theta), -np.sin(theta), x, np.sin(theta), np.cos(theta), y  , 0,0, 1]
    M = np.array(M).reshape(3,3)
    get_warped_corners((300, 500, 3), M)

