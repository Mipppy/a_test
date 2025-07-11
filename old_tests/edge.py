from __future__ import print_function
import cv2 as cv
import numpy as np
import argparse

# Argument parser
parser = argparse.ArgumentParser(description='AKAZE feature matching without homography.')
parser.add_argument('--input1', help='Path to input image 1.', default='graf1.png')
parser.add_argument('--input2', help='Path to input image 2.', default='graf3.png')
args = parser.parse_args()

# Load images
img1 = cv.imread(cv.samples.findFile(args.input1), cv.IMREAD_GRAYSCALE)
img2 = cv.imread(cv.samples.findFile(args.input2), cv.IMREAD_GRAYSCALE)

if img1 is None or img2 is None:
    print('Could not open or find the images!')
    exit(0)

# AKAZE feature detector and descriptor
akaze = cv.AKAZE_create()
kpts1, desc1 = akaze.detectAndCompute(img1, None)
kpts2, desc2 = akaze.detectAndCompute(img2, None)

# Create a Brute-Force Matcher with Hamming distance
matcher = cv.DescriptorMatcher_create(cv.DescriptorMatcher_BRUTEFORCE_HAMMING)
nn_matches = matcher.knnMatch(desc1, desc2, 2)

# Apply ratio test to find good matches
good_matches = []
nn_match_ratio = 0.8  # Nearest neighbor matching ratio
for m, n in nn_matches:
    if m.distance < nn_match_ratio * n.distance:
        good_matches.append(m)

# Draw matches
res = cv.drawMatches(img1, kpts1, img2, kpts2, good_matches, None)

# Save and display the result
cv.imwrite("akaze_result_no_homography.png", res)
print('A-KAZE Matching Results (Without Homography)')
print('*********************************************')
print('# Keypoints 1: \t', len(kpts1))
print('# Keypoints 2: \t', len(kpts2))
print('# Matches: \t', len(good_matches))

cv.imshow('result', res)
cv.waitKey()
