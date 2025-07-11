import torch
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
from tqdm import tqdm

# Feature extractor using VGG16 (conv layers only)
class VGGFeatureExtractor(torch.nn.Module):
    def __init__(self, layers=16):
        super().__init__()
        vgg = models.vgg16(pretrained=True).features
        self.features = torch.nn.Sequential(*list(vgg.children())[:layers])

    def forward(self, x):
        return self.features(x)

def preprocess_image(img_bgr, device):
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_pil = transforms.ToPILImage()(img_rgb)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # VGG16 expects this size
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return transform(img_pil).unsqueeze(0).to(device)

def cnn_template_match(template_path, map_path, output_path, stride=32):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = VGGFeatureExtractor().to(device).eval()

    # Load images
    template_img = cv2.imread(template_path)
    map_img = cv2.imread(map_path)

    # Preprocess and extract template features
    template_tensor = preprocess_image(template_img, device)
    template_feat = model(template_tensor)
    template_feat = F.normalize(template_feat, p=2, dim=1)

    # Slide over the full map
    h, w = map_img.shape[:2]
    patch_h, patch_w = 224, 224
    best = {'score': -np.inf}

    for y in tqdm(range(0, h - patch_h, stride), desc="Sliding window"):
        for x in range(0, w - patch_w, stride):
            patch = map_img[y:y+patch_h, x:x+patch_w]
            if patch.shape[0] != patch_h or patch.shape[1] != patch_w:
                continue
            patch_tensor = preprocess_image(patch, device)
            patch_feat = model(patch_tensor)
            patch_feat = F.normalize(patch_feat, p=2, dim=1)

            similarity = F.cosine_similarity(patch_feat, template_feat).mean().item()

            if similarity > best['score']:
                best.update({'score': similarity, 'coords': (x, y)})

    # Draw the best match
    if best.get('coords'):
        x, y = best['coords']
        cv2.rectangle(map_img, (x, y), (x + patch_w, y + patch_h), (0, 255, 0), 3)
        cv2.putText(map_img, f"{best['score']:.2f}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imwrite(output_path, map_img)
        print(f"[MATCH] CNN match found at ({x}, {y}), score={best['score']:.4f}")
    else:
        print("[WARN] No match found using CNN.")

# Example usage:
cnn_template_match("image_detection/cropped/cropped8.jpg", "images/map/stitched/fullmap_25.png", "cnn_match_result.png")
