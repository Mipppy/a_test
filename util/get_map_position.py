# from helpers import gimmie_data,original_pos_to_pyqt5



# def get_ai_icon_positions():
#     # 2 - Statue
#     # 3 - Tele
#     # 154 - Domain
#     # 190 - Wave

#     # Sumeru City Waypoints Adventurer's Guild and Circle
#     # Icon clicked at: 12129.682658959538, 11123.236994219653
#     # Icon clicked at: 12031.682658959538, 11191.236994219653
#     ai_data = [2,3,154,190]    
#     pos = {}
#     for data in ai_data:
#         pos[data] = []
#         for more in gimmie_data(data)['point']:
#             pos[data].append([more['x_pos'], more['y_pos']])
#     print(pos)


# get_ai_icon_positions()

import cv2
import numpy as np

# Load images
full_map = cv2.imread('lower.png', 0)
small_portion = cv2.imread('cropped.png', 0)

# Perform template matching
result = cv2.matchTemplate(full_map, small_portion, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

# Get the top-left corner of the matched region
top_left = max_loc
h, w = small_portion.shape
bottom_right = (top_left[0] + w, top_left[1] + h)

# Draw a rectangle around the matched region
full_map_color = cv2.cvtColor(full_map, cv2.COLOR_GRAY2BGR)
cv2.rectangle(full_map_color, top_left, bottom_right, (0, 255, 0), 2)

# Display the result
cv2.imwrite('matched.png', full_map_color)
cv2.waitKey(0)
cv2.destroyAllWindows()