# map_overlay_methods.py
# Six different methods to localize a smaller map portion within a larger map using file paths

import cv2
import numpy as np
import SimpleITK as sitk
from pathlib import Path
from skimage.metrics import normalized_mutual_information as nmi


def save_boxed_output(image, top_left, box_size, output_path):
    boxed_img = image.copy()
    bottom_right = (top_left[0] + box_size[0], top_left[1] + box_size[1])
    cv2.rectangle(boxed_img, top_left, bottom_right, (0, 255, 0), 3)
    cv2.imwrite(str(output_path), boxed_img)


# Method 1: Coarse-to-Fine Template Matching
def coarse_to_fine_template_match(snippet_path, full_map_path, output_path):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)
    best_match = {'score': -np.inf, 'loc': None, 'scale': 1.0}
    for scale in np.linspace(0.5, 1.5, 11):
        resized_snippet = cv2.resize(snippet, (0, 0), fx=scale, fy=scale)
        if resized_snippet.shape[0] > full_map.shape[0] or resized_snippet.shape[1] > full_map.shape[1]:
            continue
        res = cv2.matchTemplate(full_map, resized_snippet, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_match['score']:
            best_match.update({'score': max_val, 'loc': max_loc, 'scale': scale, 'size': resized_snippet.shape[1::-1]})
    if best_match['loc']:
        save_boxed_output(full_map, best_match['loc'], best_match['size'], output_path)


# Method 2: Feature Matching with Homography (ORB)
def feature_match_homography(snippet_path, full_map_path, output_path):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)
    orb = cv2.ORB_create(3000)
    kp1, des1 = orb.detectAndCompute(snippet, None)
    kp2, des2 = orb.detectAndCompute(full_map, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des1, des2, k=2)
    good = [m[0] for m in matches if len(m) == 2 and m[0].distance < 0.75 * m[1].distance]
    if len(good) >= 4:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        h, w = snippet.shape[:2]
        pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, H)
        boxed_img = full_map.copy()
        cv2.polylines(boxed_img, [np.int32(dst)], True, (0, 255, 0), 3)
        cv2.imwrite(str(output_path), boxed_img)


# Method 3: Sliding Window + Multi-Scale Template Match
def sliding_window_template(snippet_path, full_map_path, output_path, scales=[0.9, 1.0, 1.1]):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)
    best = {'score': -np.inf, 'loc': None, 'scale': 1.0, 'size': None}
    for s in scales:
        scaled_snippet = cv2.resize(snippet, (0, 0), fx=s, fy=s)
        res = cv2.matchTemplate(full_map, scaled_snippet, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best['score']:
            best.update({'score': max_val, 'loc': max_loc, 'scale': s, 'size': scaled_snippet.shape[1::-1]})
    if best['loc']:
        save_boxed_output(full_map, best['loc'], best['size'], output_path)


def ecc_alignment(snippet_path, full_map_path, output_path):
    snippet = cv2.imread(str(snippet_path))
    full_map = cv2.imread(str(full_map_path))

    # Convert to grayscale
    snippet_gray = cv2.cvtColor(snippet, cv2.COLOR_BGR2GRAY)
    full_gray = cv2.cvtColor(full_map, cv2.COLOR_BGR2GRAY)

    # Resize snippet to match approximate scale of full map
    snippet_resized = snippet_gray.copy()
    full_resized = full_gray.copy()

    # Must be same size; so crop or resize the map to a region if known (here assuming center crop for test)
    h, w = snippet_resized.shape
    center_y, center_x = full_resized.shape[0] // 2, full_resized.shape[1] // 2
    cropped_map = full_resized[center_y - h // 2:center_y + h // 2, center_x - w // 2:center_x + w // 2]

    if cropped_map.shape != snippet_resized.shape:
        print("Skipping ECC: mismatched crop size")
        return

    warp_matrix = np.eye(2, 3, dtype=np.float32)

    try:
        cc, warp_matrix = cv2.findTransformECC(
            cropped_map,
            snippet_resized,
            warp_matrix,
            cv2.MOTION_TRANSLATION,
            (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)
        )

        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        transformed_corners = cv2.transform(corners, warp_matrix)
        offset = (center_x - w // 2, center_y - h // 2)
        transformed_corners += np.array(offset, dtype=np.float32).reshape(1, 1, 2)

        boxed_img = full_map.copy()
        cv2.polylines(boxed_img, [np.int32(transformed_corners)], True, (255, 0, 0), 3)
        cv2.imwrite(str(output_path), boxed_img)

    except cv2.error as e:
        print("ECC alignment failed:", e)



# Method 5: Frequency Domain / Phase Correlation
def frequency_phase_correlation(snippet_path, full_map_path, output_path):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_GRAYSCALE)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_GRAYSCALE)
    snippet_f = np.fft.fft2(snippet, s=full_map.shape)
    full_f = np.fft.fft2(full_map)
    cross_power = (snippet_f * full_f.conj()) / np.abs(snippet_f * full_f.conj())
    correlation = np.fft.ifft2(cross_power)
    maxima = np.unravel_index(np.argmax(np.abs(correlation)), correlation.shape)
    save_boxed_output(cv2.cvtColor(full_map, cv2.COLOR_GRAY2BGR), (maxima[1], maxima[0]), snippet.shape[::-1], output_path)


# Method 6: Mutual Information Registration using SimpleITK
def mutual_info_registration(snippet_path, full_map_path, output_path):
    fixed = sitk.ReadImage(str(full_map_path), sitk.sitkFloat32)
    moving = sitk.ReadImage(str(snippet_path), sitk.sitkFloat32)
    initial_transform = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler2DTransform())
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation(50)
    registration_method.SetOptimizerAsRegularStepGradientDescent(learningRate=2.0, minStep=1e-4, numberOfIterations=100)
    registration_method.SetInitialTransform(initial_transform)
    registration_method.SetInterpolator(sitk.sitkLinear)
    final_transform = registration_method.Execute(fixed, moving)

    resampler = sitk.Resample(moving, fixed, final_transform, sitk.sitkLinear, 0.0, sitk.sitkFloat32)
    composite = sitk.Cast(fixed, sitk.sitkUInt8) + sitk.Cast(resampler, sitk.sitkUInt8)
    sitk.WriteImage(composite, str(output_path))
    
def refined_sliding_template_match(snippet_path, full_map_path, output_path, scales=[0.9,1,1.1]):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)
    best = {'score': -np.inf, 'loc': None, 'scale': 1.0, 'size': None}

    for s in scales:
        scaled_snippet = cv2.resize(snippet, (0, 0), fx=s, fy=s)
        res = cv2.matchTemplate(full_map, scaled_snippet, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best['score']:
            best.update({
                'score': max_val,
                'loc': max_loc,
                'scale': s,
                'size': scaled_snippet.shape[1::-1],
                'snippet': scaled_snippet
            })

    if best['loc']:
        x, y = best['loc']
        w, h = best['size']
        scaled_snippet = best['snippet']
        pad = 10
        roi = full_map[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]

        # Convert to grayscale and detect edges
        snippet_gray = cv2.cvtColor(scaled_snippet, cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        snippet_edges = cv2.Canny(snippet_gray, 50, 150)
        roi_edges = cv2.Canny(roi_gray, 50, 150)

        # Heuristic: Skip refinement if too few edges are found in either image
        if cv2.countNonZero(snippet_edges) < 100 or cv2.countNonZero(roi_edges) < 200:
            print("Skipping refinement due to low edge content.")
            save_boxed_output(full_map, best['loc'], best['size'], output_path)
            return

        # Use correlation-based template matching on edges
        res = cv2.matchTemplate(roi_edges, snippet_edges, cv2.TM_CCORR_NORMED)
        _, _, _, fine_loc = cv2.minMaxLoc(res)

        fx, fy = fine_loc
        top_left = (fx + max(0, x - pad), fy + max(0, y - pad))
        refined_box_size = scaled_snippet.shape[1::-1]

        save_boxed_output(full_map, top_left, refined_box_size, output_path)
        
        



def compute_edge_density(image):
    edges = cv2.Canny(image, 50, 150)
    return np.count_nonzero(edges) / edges.size

def draw_boxes_with_confidence(image, boxes, output_path):
    for i, (x, y, w, h, score) in enumerate(boxes):
        color = (0, 255, 0)  # green box
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        text = f"{score:.3f}"
        cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(str(output_path), image)

def refined_nmi_top_matches(snippet_path, full_map_path, output_path, top_k=5, scales=[0.8, 0.9, 1.0, 1.1, 1.2]):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)
    snippet_gray = cv2.cvtColor(snippet, cv2.COLOR_BGR2GRAY)
    full_map_gray = cv2.cvtColor(full_map, cv2.COLOR_BGR2GRAY)

    matches = []

    for s in scales:
        scaled_snippet = cv2.resize(snippet_gray, (0, 0), fx=s, fy=s)
        sh, sw = scaled_snippet.shape

        if full_map_gray.shape[0] < sh or full_map_gray.shape[1] < sw:
            continue

        stride_y = max(10, sh // 10)
        stride_x = max(10, sw // 10)

        for y in range(0, full_map_gray.shape[0] - sh + 1, stride_y):
            for x in range(0, full_map_gray.shape[1] - sw + 1, stride_x):
                roi = full_map_gray[y:y + sh, x:x + sw]

                if compute_edge_density(roi) < 0.05:
                    continue

                try:
                    score = nmi(scaled_snippet, roi)
                except:
                    continue

                matches.append((x, y, sw, sh, score))

    # Sort by score descending and keep top_k
    matches.sort(key=lambda x: x[4], reverse=True)
    top_matches = matches[:top_k]

    draw_boxes_with_confidence(full_map.copy(), top_matches, output_path)


def draw_boxes_with_confidence(image, boxes, output_path):
    for (x, y, w, h, score) in boxes:
        x2 = min(x + w, image.shape[1])
        y2 = min(y + h, image.shape[0])
        color = (0, 255, 0)
        cv2.rectangle(image, (x, y), (x2, y2), color, 2)
        label = f"{score:.2f}"
        cv2.putText(image, label, (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.imwrite(output_path, image)


def edge_density(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    return np.sum(edges > 0) / edges.size


def refine_with_edges(full_img, snippet, x, y, w, h):
    roi = full_img[y:y+h, x:x+w]
    snippet_gray = cv2.cvtColor(snippet, cv2.COLOR_BGR2GRAY)
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    snippet_edges = cv2.Canny(snippet_gray, 50, 150)
    roi_edges = cv2.Canny(roi_gray, 50, 150)

    res = cv2.matchTemplate(roi_edges, snippet_edges, cv2.TM_CCOEFF_NORMED)
    _, _, _, fine_loc = cv2.minMaxLoc(res)
    fx, fy = fine_loc
    return x + fx, y + fy


def refined_template_match_topk(snippet_path, full_map_path, output_path, top_k=5):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)

    snippet_h = snippet.shape[0]

    # Dynamically adjust scale range based on size
    if snippet_h < 100:
        scales = np.linspace(0.4, 1.3, 18)
    elif snippet_h < 200:
        scales = np.linspace(0.6, 1.2, 12)
    else:
        scales = [0.9, 1.0, 1.1]

    matches = []

    for scale in scales:
        scaled_snippet = cv2.resize(snippet, (0, 0), fx=scale, fy=scale)
        h, w = scaled_snippet.shape[:2]

        if h >= full_map.shape[0] or w >= full_map.shape[1]:
            continue

        result = cv2.matchTemplate(full_map, scaled_snippet, cv2.TM_CCOEFF_NORMED)

        result_flat = result.flatten()
        sorted_indices = np.argsort(result_flat)[::-1][:top_k * 5]
        seen = set()

        for idx in sorted_indices:
            y, x = divmod(idx, result.shape[1])
            score = result[y, x]

            if x + w > full_map.shape[1] or y + h > full_map.shape[0]:
                continue

            roi = full_map[y:y+h, x:x+w]
            if edge_density(roi) < 0.03:
                continue

            key = (x // 10, y // 10)
            if key in seen:
                continue
            seen.add(key)

            # Refine location using edges
            rx, ry = refine_with_edges(full_map, scaled_snippet, x, y, w, h)
            matches.append((rx, ry, w, h, score))
            if len(matches) >= top_k:
                break

    matches.sort(key=lambda x: x[4], reverse=True)
    top_matches = matches[:top_k]
    draw_boxes_with_confidence(full_map.copy(), top_matches, output_path)

# refined_template_match_topk('image_detection/cropped/cropped1.jpg','images/map/stitched/fullmap_25.png', 'wind.png')
refined_sliding_template_match('image_detection/cropped/cropped1.jpg','images/map/stitched/fullmap_20.png', 'wind.png')