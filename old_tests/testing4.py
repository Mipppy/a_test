import cv2
import numpy as np
from tqdm import tqdm
import os

def match_template_on_full_map(template_path, full_map_path, output_path, scales=np.geomspace(1.5, 0.8, 6)):
    """
    Matches a scaled template on the full map image using OpenCV's template matching.
    """
    template_orig = cv2.imread(template_path, cv2.IMREAD_COLOR)
    full_map = cv2.imread(full_map_path, cv2.IMREAD_COLOR)

    best = {'score': -np.inf}

    for scale in tqdm(scales, desc="Scanning full map at multiple scales"):
        template = cv2.resize(template_orig, (0, 0), fx=scale, fy=scale)
        th, tw = template.shape[:2]
        if th > full_map.shape[0] or tw > full_map.shape[1]:
            continue  # Skip too-large templates

        result = cv2.matchTemplate(full_map, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best['score']:
            best.update({
                'score': max_val,
                'loc': max_loc,
                'template_size': (tw, th),
                'scale': scale
            })

    if best.get('loc') is not None:
        top_left = best['loc']
        w, h = best['template_size']
        bottom_right = (top_left[0] + w, top_left[1] + h)

        result_img = cv2.cvtColor(full_map, cv2.RGB)
        cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 3)
        cv2.putText(result_img, f"{best['score']:.2f}", (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, result_img)
        print(f"[MATCH] Full map match @ scale {best['scale']:.2f}, score={best['score']:.4f}")
    else:
        print("[WARN] No match found on full map.")

# Example usage (disabled here, but should be placed in `if __name__ == '__main__':`)
match_template_on_full_map(
    template_path='image_detection/cropped/cropped9.jpg',
    full_map_path='images/map/stitched/fullmap_25.png',
    output_path='tile_match_fullmap_result.png'
)

