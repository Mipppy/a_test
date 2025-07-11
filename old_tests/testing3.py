import cv2
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Lazy tile loading only when needed
def stitch_tiles_lazy(x, y, tile_dir, window_size):
    rows = []
    for dy in range(window_size[1]):
        row = []
        for dx in range(window_size[0]):
            tile_path = os.path.join(tile_dir, f"{x+dx}_{y+dy}_P0.webp")
            if not os.path.exists(tile_path):
                return None
            tile_img = cv2.imread(tile_path, cv2.IMREAD_GRAYSCALE)
            if tile_img is None:
                return None
            row.append(tile_img)
        rows.append(np.hstack(row))
    return np.vstack(rows)

def match_patch(x, y, template, tile_dir, window_size):
    patch = stitch_tiles_lazy(x, y, tile_dir, window_size)
    if patch is None or patch.shape[0] < template.shape[0] or patch.shape[1] < template.shape[1]:
        return -np.inf, (0, 0), None, (0, 0), (x, y)
    result = cv2.matchTemplate(patch, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc, patch, template.shape[::-1], (x, y)

def tile_based_template_match_multithreaded(template_path, tile_dir, output_path,
                                            x_range=(10, 84), y_range=(10, 42),
                                            scales=np.geomspace(1.5, 0.2, 3),
                                            window_size=(3, 3), max_workers=8):
    template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    best = {'score': -np.inf}

    for scale in scales:
        template = cv2.resize(template_orig, (0, 0), fx=scale, fy=scale)
        th, tw = template.shape[:2]
        print(f"[INFO] Scale: {scale:.2f}, Template size: {tw}x{th}")

        coords_list = [(x, y) for x in range(x_range[0], x_range[1] - window_size[0] + 1)
                             for y in range(y_range[0], y_range[1] - window_size[1] + 1)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(match_patch, x, y, template, tile_dir, window_size): (x, y)
                       for (x, y) in coords_list}

            for f in tqdm(as_completed(futures), total=len(futures), desc=f"Scanning scale {scale:.2f}"):
                score, loc, patch, size, coords = f.result()
                if score > best['score']:
                    best.update({
                        'score': score,
                        'loc': loc,
                        'region': patch,
                        'template_size': size,
                        'coords': coords,
                        'scale': scale
                    })

    if best.get('region') is not None:
        x, y = best['loc']
        w, h = best['template_size']
        top_left = (x, y)
        bottom_right = (x + w, y + h)
        result_img = best['region'].copy()
        cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 3)
        cv2.putText(result_img, f"{best['score']:.2f}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, result_img)
        print(f"[MATCH] Found at tile {best['coords']} @ scale {best['scale']:.2f}, score={best['score']:.4f}")
    else:
        print("[WARN] No match found.")

# Example usage
if __name__ == '__main__':
    tile_based_template_match_multithreaded(
        template_path='image_detection/cropped/cropped5.png',
        tile_dir='images/map/official/high_res/',
        output_path='tile_match_result_fixed.png',
        x_range=(10, 84),
        y_range=(10, 42),
        window_size=(3, 3),
        scales=np.geomspace(1.5, 0.8, 6),
        max_workers=6
    )
