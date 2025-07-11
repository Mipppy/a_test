import cv2
import numpy as np

def feature_match_homography(template_path, full_map_path, output_path, min_matches=10):
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    full_map = cv2.imread(full_map_path, cv2.IMREAD_GRAYSCALE)
    if template is None or full_map is None:
        raise FileNotFoundError("Could not load images")

    sift = cv2.SIFT_create()

    kp1, des1 = sift.detectAndCompute(template, None)
    kp2, des2 = sift.detectAndCompute(full_map, None)

    index_params = dict(algorithm=1, trees=5) 
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    matches = flann.knnMatch(des1, des2, k=2)

    good = [m for m,n in matches if m.distance < 0.7 * n.distance]
    if len(good) < min_matches:
        print(f"[WARN] Not enough matches: {len(good)}")
        return

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1,1,2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    h, w = template.shape
    pts = np.float32([[0,0],[w,0],[w,h],[0,h]]).reshape(-1,1,2)
    dst = cv2.perspectiveTransform(pts, H)

    full_color = cv2.imread(full_map_path)
    cv2.polylines(full_color, [np.int32(dst)], True, (0,255,0), 3)
    cv2.imwrite(output_path, full_color)
    print(f"[INFO] Drawn homography box with {len(good)} matches.")

feature_match_homography(
    template_path='image_detection/cropped/cropped4.jpg',
    full_map_path='images/map/stitched/fullmap_25.png',
    output_path='feature_match_result.png'
)
