import json
import os
import time
from typing import Dict, List
from PyQt5.QtGui import QIcon, QPixmap, QImage, QImageReader
from concurrent.futures import ThreadPoolExecutor, as_completed


class LoadedData:

    official_dataset: dict = None
    unofficial_dataset: dict = None
    id_oid_dataset: dict = None
    official_id_to_unofficial_id: dict = None
    unofficial_btn_data: dict = None
    all_official_ids: dict = None

    qicon_paths: List[str] = [
        'images/resources/application/thumbs_up_dark.png',
        'images/resources/application/thumbs_up_light.png',
        'images/resources/application/thumbs_up_selected.png',
        'images/resources/application/thumbs_down_dark.png',
        'images/resources/application/thumbs_down_light.png',
        'images/resources/application/thumbs_down_selected.png',
    ]
    qicon_cache: Dict[str, QIcon] = {}

    map_pixmaps: dict[tuple[int, int], QPixmap] = {}
    btn_pixmaps: dict[int, QPixmap] = {}

    
    @classmethod
    def init(cls):
        from helpers import get_all_ids
        cls.all_official_ids = get_all_ids()
        def load_json(path: str, attr: str, is_required=True, label=""):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    setattr(cls, attr, json.load(f))
            except Exception as e:
                level = "[error]" if is_required else "[warn]"
                label_text = f" ({label})" if label else ""
                print(f"{level} Failed to load {attr}{label_text}: {e}")

        def load_icon(path: str):
            try:
                filename = os.path.basename(path)
                if filename not in cls.qicon_cache:
                    cls.qicon_cache[filename] = QIcon(path)
            except Exception as e:
                print(f"[error] Failed to load icon: {path}: {e}")

        json_tasks = []
        with ThreadPoolExecutor() as executor:
            json_tasks.append(executor.submit(load_json, 'data/official/full/full_dataset.json', 'official_dataset', True, "official"))
            json_tasks.append(executor.submit(load_json, 'data/unofficial/location_data.json', 'unofficial_dataset', True, "unofficial"))
            json_tasks.append(executor.submit(load_json, 'application_data/official_unofficial_ids.json', 'id_oid_dataset', False, "id_oid"))
            json_tasks.append(executor.submit(load_json, 'application_data/map_object_mapping.json', 'official_id_to_unofficial_id', False, "mapping"))
            json_tasks.append(executor.submit(load_json, 'data/unofficial/button_data.json', 'unofficial_btn_data', True, "button"))

            for future in as_completed(json_tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"[error] Unexpected error during JSON loading: {e}")

        image_tasks = []
        with ThreadPoolExecutor() as executor:
            image_tasks.append(executor.submit(cls.load_map_images_async, "images/map/official/high_res/"))
            image_tasks.append(executor.submit(cls.load_button_images_async, "images/resources/official/"))
            for path in cls.qicon_paths:
                image_tasks.append(executor.submit(load_icon, path))

            for future in as_completed(image_tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"[error] Unexpected error during image/icon loading: {e}")

                    
    @classmethod
    def load_map_images_async(cls, directory: str):
        from helpers import get_coordinates_from_filename
        def load_image(image_file: str) -> tuple[tuple[int, int], QImage] | None:
            coords = get_coordinates_from_filename(image_file)
            if coords:
                path = os.path.join(directory, image_file)
                reader = QImageReader(path)
                reader.setAutoDetectImageFormat(True)
                # reader.setScaledSize(QSize(256, 256)) 

                image = reader.read()
                if not image.isNull():
                    return coords, image
            return None


        try:
            files = [f for f in os.listdir(directory) if f.endswith('.webp')]
        except Exception as e:
            print(f"[error] Failed to list map image directory: {e}")
            return

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(load_image, f) for f in files]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    coords, qimage = result
                    pixmap = QPixmap.fromImage(qimage) 
                    cls.map_pixmaps[coords] = pixmap
        
    @classmethod
    def load_button_images_async(cls, directory: str):
        if cls.btn_pixmaps:
            return

        def load_button_image(entry: list[int, str]) -> tuple[int, QPixmap] | None:
            btn_id, _ = entry
            for ext in (".webp", ".jpg", ".png"):
                image_path = os.path.join(directory, f"{btn_id}{ext}")
                if os.path.exists(image_path):
                    reader = QImageReader(image_path)
                    reader.setAutoDetectImageFormat(True)
                    image = reader.read()
                    if not image.isNull():
                        return btn_id, QPixmap.fromImage(image)
            return None

        if not cls.all_official_ids:
            print("[warn] No button data loaded, skipping button image loading.")
            return

        entries = []
        for category, id_name_list in cls.all_official_ids.items():
            entries.extend(id_name_list)

        d = time.time()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(load_button_image, entry) for entry in entries]
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, tuple) and len(result) == 2:
                    btn_id, pixmap = result
                    if pixmap is not None:
                        cls.btn_pixmaps[btn_id] = pixmap
                else:
                    print(f"[warn] Failed to load button image for entry: {result}")

        print(f"[info] Loaded {len(cls.btn_pixmaps)} button images in {time.time() - d:.2f}s")
