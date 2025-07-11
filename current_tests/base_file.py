"""
A copy of the testing10.py for reference
"""

import cv2
import numpy as np
from tqdm import tqdm

def feature_match_homography(template_path, full_map_path, output_path, min_matches=10,
                             sift_nfeatures=1000, downsample=0.7, show_progress=True):
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    full_map_orig = cv2.imread(full_map_path, cv2.IMREAD_GRAYSCALE)
    if template is None or full_map_orig is None:
        raise FileNotFoundError("Could not load images")

    if downsample != 1.0:
        full_map = cv2.resize(full_map_orig, (0, 0), fx=downsample, fy=downsample)
    else:
        full_map = full_map_orig

    sift = cv2.SIFT_create(nfeatures=sift_nfeatures)

    kp1, des1 = sift.detectAndCompute(template, None)
    kp2, des2 = sift.detectAndCompute(full_map, None)

    if des1 is None or des2 is None or len(kp1) == 0 or len(kp2) == 0:
        print("[ERROR] No keypoints detected.")
        return

    index_params = dict(algorithm=1, trees=5)  
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    raw_matches = flann.knnMatch(des1, des2, k=2)

    iterable = tqdm(raw_matches, desc="Filtering matches") if show_progress else raw_matches
    good = [m for m, n in iterable if m.distance < 0.7 * n.distance]

    if len(good) < min_matches:
        print(f"[WARN] Not enough good matches: {len(good)}")
        return

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if H is None:
        print("[ERROR] Homography could not be computed.")
        return

    h, w = template.shape
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    dst_corners = cv2.perspectiveTransform(corners, H)

    if downsample != 1.0:
        dst_corners /= downsample

    full_color = cv2.imread(full_map_path)
    cv2.polylines(full_color, [np.int32(dst_corners)], isClosed=True, color=(0, 255, 0), thickness=3)
    cv2.imwrite(output_path, full_color)

    print(f"[INFO] Homography box drawn with {len(good)} good matches.")
feature_match_homography(
    template_path='image_detection/cropped/cropped7.jpg',
    full_map_path='images/map/stitched/fullmap_25.png',
    output_path='feature_match_result.png',
    downsample=1,           # Optional speed boost
    sift_nfeatures=0,      # Reduce features to speed up SIFT
    show_progress=False        # Enables tqdm progress bar
)
