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

    qicon_paths: List[str] = [
        'images/resources/application/thumbs_up.png',
        'images/resources/application/thumbs_down.png'
    ]
    qicon_cache: Dict[str, QIcon] = {}

    map_pixmaps: dict[tuple[int, int], QPixmap] = {}
    
    @classmethod
    def init(cls):
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

        tasks = []
        with ThreadPoolExecutor() as executor:
            tasks.append(executor.submit(load_json, 'data/official/full/full_dataset.json', 'official_dataset', True, "official"))
            tasks.append(executor.submit(load_json, 'data/unofficial/location_data.json', 'unofficial_dataset', True, "unofficial"))
            tasks.append(executor.submit(load_json, 'application_data/official_unofficial_ids.json', 'id_oid_dataset', False, "id_oid"))
            tasks.append(executor.submit(load_json, 'application_data/map_object_mapping.json', 'official_id_to_unofficial_id', False, "mapping"))
            tasks.append(executor.submit(load_json, 'data/unofficial/button_data.json', 'unofficial_btn_data', True, "button"))
            tasks.append(executor.submit(cls.load_map_images_async))
            for path in cls.qicon_paths:
                tasks.append(executor.submit(load_icon, path))

            for future in as_completed(tasks):
                try:
                    future.result()
                except Exception as e:
                    print(f"[error] Unexpected error during loading: {e}")
                    
    @classmethod
    def load_map_images_async(cls, directory: str = "images/map/official/high_res"):
        from helpers import get_coordinates_from_filename
        d = time.time()
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
        print(f"{time.time() - d}")