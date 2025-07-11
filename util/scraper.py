# import os
# import json

# def combine_json_files(input_directory, output_file):
#     combined_data = {
#         'point_list': [],
#         'label_list': []
#     }

#     # List all JSON files in the directory
#     for filename in os.listdir(input_directory):
#         if filename.endswith('.json'):
#             file_path = os.path.join(input_directory, filename)

#             try:
#                 # Read and parse each JSON file
#                 with open(file_path, 'r', encoding='utf-8') as file:
#                     data = json.load(file)
#                     data = data['data']
#                     # Check if 'point_list' and 'label_list' exist in the data
#                     if 'point_list' in data:
#                         combined_data['point_list'].extend(data['point_list'])
#                     else:
#                         print(f"Warning: 'point_list' not found in {filename}")
                    
#                     if 'label_list' in data:
#                         combined_data['label_list'].extend(data['label_list'])
#                     else:
#                         print(f"Warning: 'label_list' not found in {filename}")
                
#             except Exception as e:
#                 print(f"Error reading {filename}: {e}")

#     # Check if combined data contains anything
#     if not combined_data['point_list'] and not combined_data['label_list']:
#         print("No data was added to combined data.")
#         return

#     # Write the combined data to the output file
#     with open(output_file, 'w', encoding='utf-8') as output:
#         json.dump(combined_data, output, indent=4)

#     print(f"Combined data has been saved to {output_file}")

# # Example usage
# input_directory = './data/official_copy/'  # Replace with your directory path
# output_file = 'combined_output.json'  # Output file name
# combine_json_files(input_directory, output_file)

# import json
# import os
# import requests

# # Define the folder where images will be saved
# save_folder = "images/resources/official/"
# os.makedirs(save_folder, exist_ok=True)  # Create the folder if it doesn't exist

# # Load the JSON data
# with open('data/official/full_dataset.json', "r") as file:
#     data = json.load(file)

# # Iterate through labels and download images
# for label in data.get('label_list', []):
#     url = label.get('icon')
#     if url:
#         try:
#             response = requests.get(url, stream=True)  # Stream the download
#             response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)

#             # Extract the filename from the URL
#             filename = os.path.join(save_folder, os.path.basename(str(label['id']) + ".jpg"))

#             # Save the image
#             with open(filename, 'wb') as img_file:
#                 for chunk in response.iter_content(1024):
#                     img_file.write(chunk)

#             print(f"Downloaded: {filename}")

#         except requests.exceptions.RequestException as e:
#             print(f"Failed to download {url}: {e}")
