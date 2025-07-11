# map_overlay_methods.py
# Core methods to localize a smaller map portion within a larger map using file paths

import cv2
import numpy as np
from pathlib import Path
from skimage.metrics import normalized_mutual_information as nmi
import re
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
def save_boxed_output(image, top_left, box_size, output_path):
    boxed_img = image.copy()
    bottom_right = (top_left[0] + box_size[0], top_left[1] + box_size[1])
    cv2.rectangle(boxed_img, top_left, bottom_right, (0, 255, 0), 3)
    cv2.imwrite(str(output_path), boxed_img)

def compute_edge_density(image):
    edges = cv2.Canny(image, 50, 150)
    return np.count_nonzero(edges) / edges.size

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
def refined_sliding_template_match(snippet_path, full_map_path, output_path, scales=np.linspace(0.1, 1.2, 5)):
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

        snippet_gray = cv2.cvtColor(scaled_snippet, cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        snippet_edges = cv2.Canny(snippet_gray, 50, 150)
        roi_edges = cv2.Canny(roi_gray, 50, 150)

        if cv2.countNonZero(snippet_edges) < 100 or cv2.countNonZero(roi_edges) < 200:
            print("Skipping refinement due to low edge content.")
            draw_boxes_with_confidence(
                full_map.copy(),
                [(x, y, w, h, best['score'])],
                output_path
            )
            return

        res = cv2.matchTemplate(roi_edges, snippet_edges, cv2.TM_CCORR_NORMED)
        _, _, _, fine_loc = cv2.minMaxLoc(res)
        fx, fy = fine_loc

        top_left = (fx + max(0, x - pad), fy + max(0, y - pad))
        refined_box_size = scaled_snippet.shape[1::-1]

        draw_boxes_with_confidence(
            full_map.copy(),
            [(top_left[0], top_left[1], refined_box_size[0], refined_box_size[1], best['score'])],
            output_path
        )


def refined_template_match_topk(snippet_path, full_map_path, output_path, top_k=5):
    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)

    snippet_h = snippet.shape[0]

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

            rx, ry = refine_with_edges(full_map, scaled_snippet, x, y, w, h)
            matches.append((rx, ry, w, h, score))
            if len(matches) >= top_k:
                break

    matches.sort(key=lambda x: x[4], reverse=True)
    top_matches = matches[:top_k]
    draw_boxes_with_confidence(full_map.copy(), top_matches, output_path)
def reliable_fast_template_match(
    snippet_path, full_map_path, output_path, 
    scales=(0.9, 1.0, 1.1), max_dim=3000, refine_edges=True, early_exit_score=0.98
):
    """
    A balanced version of template matching:
    - Uses color for accuracy
    - Limits scales to reduce overhead
    - Optionally refines with Canny edge detection
    - Early exit if a high-confidence match is found
    """

    snippet = cv2.imread(str(snippet_path), cv2.IMREAD_COLOR)
    full_map = cv2.imread(str(full_map_path), cv2.IMREAD_COLOR)

    if snippet is None or full_map is None:
        print("[ERROR] Failed to load one or both images.")
        return

    # Resize full_map if it's too large
    h, w = full_map.shape[:2]
    scale_factor = 1.0
    if max(h, w) > max_dim:
        scale_factor = max_dim / max(h, w)
        full_map = cv2.resize(full_map, (int(w * scale_factor), int(h * scale_factor)))
        print(f"[INFO] Resized full map to {(int(w * scale_factor), int(h * scale_factor))}")

    best = {'score': -np.inf, 'loc': None, 'scale': 1.0, 'size': None, 'snippet': None}

    for s in scales:
        scaled_snippet = cv2.resize(snippet, (0, 0), fx=s, fy=s)
        sh, sw = scaled_snippet.shape[:2]

        if sh >= full_map.shape[0] or sw >= full_map.shape[1]:
            continue

        result = cv2.matchTemplate(full_map, scaled_snippet, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best['score']:
            best.update({
                'score': max_val,
                'loc': max_loc,
                'scale': s,
                'size': (sw, sh),
                'snippet': scaled_snippet
            })

        if max_val >= early_exit_score:
            print(f"[INFO] Early exit at scale {s:.2f} with score {max_val:.4f}")
            break

    if best['loc'] is None:
        print("[WARN] No good match found.")
        return

    x, y = best['loc']
    w, h = best['size']
    refined_x, refined_y = x, y

    # Optional refinement using edges
    if refine_edges:
        pad = 10
        roi = full_map[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
        snip_gray = cv2.cvtColor(best['snippet'], cv2.COLOR_BGR2GRAY)
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        snip_edges = cv2.Canny(snip_gray, 50, 150)
        roi_edges = cv2.Canny(roi_gray, 50, 150)

        if cv2.countNonZero(snip_edges) > 50 and cv2.countNonZero(roi_edges) > 100:
            result = cv2.matchTemplate(roi_edges, snip_edges, cv2.TM_CCORR_NORMED)
            _, _, _, fine_loc = cv2.minMaxLoc(result)
            fx, fy = fine_loc
            refined_x = fx + max(0, x - pad)
            refined_y = fy + max(0, y - pad)
        else:
            print("[INFO] Skipping edge refinement due to low edge content.")

    # Draw and save result
    top_left = (refined_x, refined_y)
    bottom_right = (refined_x + w, refined_y + h)
    boxed_img = full_map.copy()
    cv2.rectangle(boxed_img, top_left, bottom_right, (0, 255, 0), 3)
    cv2.putText(boxed_img, f"{best['score']:.2f}", (top_left[0], max(20, top_left[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imwrite(output_path, boxed_img)
    print(f"[✅] Match score: {best['score']:.4f} | Scale: {best['scale']:.2f} | Location: {top_left}")


def parse_tile_filename(filename):
    match = re.match(r'(\d+)_(\d+)_P0\.webp', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def load_tiles_map(tiles_dir):
    tiles = defaultdict(dict)
    for f in Path(tiles_dir).glob("*.webp"):
        coords = parse_tile_filename(f.name)
        if coords:
            x, y = coords
            tiles[x][y] = str(f)
    return tiles

TILE_SIZE = 256
def get_tile_region(tiles, start_x, start_y, nx, ny):
    """Assemble a region from tiles into a single image"""
    canvas = np.zeros((ny * TILE_SIZE, nx * TILE_SIZE, 3), dtype=np.uint8)
    for dx in range(nx):
        for dy in range(ny):
            x, y = start_x + dx, start_y + dy
            tile_path = tiles.get(x, {}).get(y)
            if tile_path:
                tile = cv2.imread(tile_path)
                if tile is not None:
                    canvas[dy*TILE_SIZE:(dy+1)*TILE_SIZE, dx*TILE_SIZE:(dx+1)*TILE_SIZE] = tile
    return canvas

def tile_based_template_match(template_path, tile_dir, output_path, max_x=100, max_y=100, scales=np.geomspace(1.5, 0.2, 3), window_size=(3, 3)):
    """
    Attempts to locate a template image within stitched tile patches.
    """
    tiles = load_tiles_map(tile_dir)
    template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    best = {'score': -np.inf, 'loc': None, 'coords': None, 'scale': 1.0, 'region': None}

    for s in scales:
        template = cv2.resize(template_orig, (0, 0), fx=s, fy=s)
        th, tw = template.shape[:2]

        for x in range(0, max_x - window_size[0]):
            for y in range(0, max_y - window_size[1]):
                patch = get_tile_region(tiles, x, y, *window_size)
                print((x,y))
                if patch is None or patch.shape[0] == 0 or patch.shape[1] == 0:
                    continue

                patch_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

                if th >= patch_gray.shape[0] or tw >= patch_gray.shape[1]:
                    continue  # skip if template is too large

                res = cv2.matchTemplate(patch_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val > best['score']:
                    best.update({
                        'score': max_val,
                        'loc': max_loc,
                        'coords': (x, y),
                        'scale': s,
                        'region': patch.copy(),
                        'template_size': (tw, th),
                    })

    if best['loc']:
        x, y = best['loc']
        w, h = best['template_size']
        top_left = (x, y)
        bottom_right = (x + w, y + h)
        cv2.rectangle(best['region'], top_left, bottom_right, (0, 255, 0), 3)
        cv2.putText(best['region'], f"{best['score']:.2f}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, best['region'])
        print(f"[INFO] Match found in tiles starting at {best['coords']} with scale {best['scale']:.2f}, score {best['score']:.4f}")
    else:
        print("[WARN] No match found.")



def parse_tile_filename(filename):
    try:
        x, y, *_ = filename.split("_")
        return int(x), int(y)
    except:
        return None

def preload_tiles(tile_dir):
    tiles = {}
    for path in Path(tile_dir).glob("*.webp"):
        coords = parse_tile_filename(path.name)
        if coords:
            tile_img = cv2.imread(str(path))
            if tile_img is not None:
                tiles[coords] = tile_img
    return tiles

def get_tile_region(tile_images, start_x, start_y, nx, ny):
    canvas = np.zeros((ny * TILE_SIZE, nx * TILE_SIZE, 3), dtype=np.uint8)
    for dx in range(nx):
        for dy in range(ny):
            tile = tile_images.get((start_x + dx, start_y + dy))
            if tile is not None:
                canvas[dy*TILE_SIZE:(dy+1)*TILE_SIZE, dx*TILE_SIZE:(dx+1)*TILE_SIZE] = tile
            else:
                return None  # skip region if any tile is missing
    return canvas

def match_patch(x, y, template, tile_images, window_size):
    patch = get_tile_region(tile_images, x, y, *window_size)
    if patch is None:
        return -np.inf, None, None, None, None

    patch_gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    th, tw = template.shape[:2]
    if th >= patch_gray.shape[0] or tw >= patch_gray.shape[1]:
        return -np.inf, None, None, None, None

    res = cv2.matchTemplate(patch_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    return max_val, max_loc, patch, (tw, th), (x, y)

def tile_based_template_match_multithreaded(template_path, tile_dir, output_path,
                                            max_x=100, max_y=100,
                                            scales=np.geomspace(1.5, 0.2, 3),
                                            window_size=(3, 3),
                                            max_workers=8):
    tile_images = preload_tiles(tile_dir)
    template_orig = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    best = {'score': -np.inf}

    for scale in scales:
        template = cv2.resize(template_orig, (0, 0), fx=scale, fy=scale)
        th, tw = template.shape[:2]
        print(f"[INFO] Scale: {scale:.2f}, Template size: {tw}x{th}")

        coords_list = [(x, y) for x in range(0, max_x - window_size[0])
                             for y in range(0, max_y - window_size[1])]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(match_patch, x, y, template, tile_images, window_size)
                       for (x, y) in coords_list]

            for f in futures:
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
        cv2.rectangle(best['region'], top_left, bottom_right, (0, 255, 0), 3)
        cv2.putText(best['region'], f"{best['score']:.2f}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, best['region'])
        print(f"[MATCH] Found at tile {best['coords']} @ scale {best['scale']:.2f}, score={best['score']:.4f}")
    else:
        print("[WARN] No match found.")

# Example usage:
tile_based_template_match_multithreaded(
    template_path='image_detection/cropped/cropped.png',
    tile_dir='images/map/official/high_res/',
    output_path='tile_match_result2.png',
    max_x=100,
    max_y=100,
    window_size=(4, 4)
)
# refined_sliding_template_match('image_detection/cropped/cropped.png', 'images/map/stitched/fullmap_25.png', 'wind.png')