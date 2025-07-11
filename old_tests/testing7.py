import cv2
import numpy as np
import torch
import torchvision.transforms as T
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Transformation for MobileNetV2
transform = T.Compose([
    T.ToPILImage(),
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

# Load MobileNetV2 model
_weight = MobileNet_V2_Weights.DEFAULT
mobilenet = mobilenet_v2(weights=_weight).features.eval()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mobilenet.to(device)

@torch.no_grad()
def extract_feature(image):
    img_t = transform(image).unsqueeze(0).to(device)
    feat = mobilenet(img_t)
    pooled = torch.nn.functional.adaptive_avg_pool2d(feat, 1)
    return pooled.squeeze().cpu().numpy()

def cnn_feature_match_threaded(template_path, full_map_path, output_path,
                                stride=64, patch_size=144, downsample=0.7,
                                max_workers=8):
    template_img = cv2.imread(template_path)
    full_map = cv2.imread(full_map_path)

    if downsample != 1.0:
        full_map = cv2.resize(full_map, (0, 0), fx=downsample, fy=downsample)

    h, w, _ = full_map.shape
    th, tw = patch_size, patch_size

    print("[INFO] Extracting template feature...")
    template_feat = extract_feature(cv2.resize(template_img, (patch_size, patch_size)))

    coords = [(x, y) for y in range(0, h - th + 1, stride)
                    for x in range(0, w - tw + 1, stride)]

    def compute_patch_similarity(x, y):
        patch = full_map[y:y+th, x:x+tw]
        if patch.shape[:2] != (th, tw):
            return -1, (x, y)
        feat = extract_feature(patch)
        sim = cosine_similarity([template_feat], [feat])[0][0]
        return sim, (x, y)

    best_score = -1
    best_coord = (0, 0)

    print("[INFO] Scanning full map with multithreading...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(compute_patch_similarity, x, y) for x, y in coords]
        for f in tqdm(as_completed(futures), total=len(futures), desc="CNN matching"):
            sim, (x, y) = f.result()
            if sim > best_score:
                best_score = sim
                best_coord = (x, y)

    x, y = best_coord
    top_left = (int(x / downsample), int(y / downsample))
    bottom_right = (int((x + tw) / downsample), int((y + th) / downsample))

    original_map = cv2.imread(full_map_path)
    result_img = original_map.copy()
    cv2.rectangle(result_img, top_left, bottom_right, (0, 255, 0), 3)
    cv2.putText(result_img, f"{best_score:.2f}", (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imwrite(output_path, result_img)
    print(f"[MATCH] CNN Match @ {top_left}, score={best_score:.4f}")

# Example usage
cnn_feature_match_threaded(
    template_path='image_detection/cropped/cropped8.jpg',
    full_map_path='images/map/stitched/fullmap_25.png',
    output_path='tile_match_fullmap_result_cnn.png',
    stride=32,
    patch_size=600,
    downsample=0.6,
    max_workers=8
)
