import json
import re
import requests

with open('all_images.har', 'r') as file:
    har_data = json.load(file)

pattern = re.compile(r'\d{2}_\d{2}_P0\.webp')

matching_images = []

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    if pattern.search(url):
        matching_images.append(url)

for image_url in matching_images:
    image_name = image_url.split('/')[-1]
    response = requests.get(image_url)

    if response.status_code == 200:
        with open(f"images/map/official/high_res/{image_name}", 'wb') as img_file:
            img_file.write(response.content)
        print(f"Downloaded: {image_name}")
    else:
        print(f"Failed to download: {image_name}")

print("Matching images URLs:")
for url in matching_images:
    print(url)
