import cv2
from jdeskew.estimator import get_angle
from jdeskew.utility import rotate

input_image_path = "/tmp/newspapers/lamasca-pages/1994/lamasca-1994-11-23/page_01.jpeg"
output_image_path = "/tmp/deskewed.jpeg"

# Load the image
image = cv2.imread(input_image_path)

# Get the skew angle
angle = get_angle(image)

# Rotate the image
output_image = rotate(image, angle)

# Save the deskewed image
cv2.imwrite(output_image_path, output_image)

print(f"Deskewed image saved to: {output_image_path}")
print(f"Detected skew angle: {angle} degrees")
