
input_image_path = "/tmp/newspapers/lamasca-pages/1994/lamasca-1994-11-23/page_01.jpeg"
output_image_path = "/tmp/deskewed.jpeg"
from jdeskew.estimator import get_angle
angle = get_angle(image)

from jdeskew.utility import rotate
output_image = rotate(image, angle)
