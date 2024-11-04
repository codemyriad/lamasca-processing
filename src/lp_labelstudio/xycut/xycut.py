from typing import List
import cv2
import numpy as np


def points_to_bbox(points):
    left = min(points[::2])
    right = max(points[::2])
    top = min(points[1::2])
    bottom = max(points[1::2])
    return [left, top, right, bottom]


def vis_polygon(img, points, thickness=2, color=None):
    br2bl_color = color
    tl2tr_color = color
    tr2br_color = color
    bl2tl_color = color
    cv2.line(
        img,
        (points[0][0], points[0][1]),
        (points[1][0], points[1][1]),
        color=tl2tr_color,
        thickness=thickness,
    )

    cv2.line(
        img,
        (points[1][0], points[1][1]),
        (points[2][0], points[2][1]),
        color=tr2br_color,
        thickness=thickness,
    )

    cv2.line(
        img,
        (points[2][0], points[2][1]),
        (points[3][0], points[3][1]),
        color=br2bl_color,
        thickness=thickness,
    )

    cv2.line(
        img,
        (points[3][0], points[3][1]),
        (points[0][0], points[0][1]),
        color=bl2tl_color,
        thickness=thickness,
    )
    return img


def compute_gap_threshold(boxes: np.ndarray, axis: int) -> float:
    """Compute an adaptive threshold for identifying significant gaps between boxes.
    
    Args:
        boxes: Array of shape (N, 4) containing box coordinates [x1,y1,x2,y2]
        axis: 0 for horizontal gaps, 1 for vertical gaps
    
    Returns:
        Threshold value for minimum significant gap
    """
    # Get relevant coordinates for the axis
    coords = boxes[:, axis::2]
    
    # Compute gaps between adjacent boxes
    sorted_starts = np.sort(coords[:, 0])
    gaps = sorted_starts[1:] - sorted_starts[:-1]
    
    if len(gaps) == 0:
        return 1.0
        
    # Use median gap as base threshold
    median_gap = np.median(gaps)
    
    # Scale threshold based on box dimensions
    box_sizes = coords[:, 1] - coords[:, 0]
    median_size = np.median(box_sizes)
    
    # Threshold is minimum of median gap and fraction of median box size
    return min(median_gap, median_size * 0.3)

def vis_points(
    img: np.ndarray, points, texts: List[str] = None, color=(0, 200, 0)
) -> np.ndarray:
    """Visualize polygons and their labels on an image.
    
    Args:
        img: Input image as numpy array
        points: Array of shape [N, 8] containing polygon coordinates
               Format: [x1,y1,x2,y2,x3,y3,x4,y4] for each polygon
        texts: Optional list of N strings to display as labels
        color: RGB color tuple for drawing polygons and labels
    
    Returns:
        Image with visualized polygons and labels
    """
    points = np.array(points)
    if texts is not None:
        assert len(texts) == points.shape[0]

    for i, _points in enumerate(points):
        vis_polygon(img, _points.reshape(-1, 2), thickness=2, color=color)
        bbox = points_to_bbox(_points)
        left, top, right, bottom = bbox
        cx = (left + right) // 2
        cy = (top + bottom) // 2

        txt = texts[i]
        font = cv2.FONT_HERSHEY_SIMPLEX
        cat_size = cv2.getTextSize(txt, font, 0.5, 2)[0]

        img = cv2.rectangle(
            img,
            (cx - 5 * len(txt), cy - cat_size[1] - 5),
            (cx - 5 * len(txt) + cat_size[0], cy - 5),
            color,
            -1,
        )

        img = cv2.putText(
            img,
            txt,
            (cx - 5 * len(txt), cy - 5),
            font,
            0.5,
            (255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    return img


def vis_polygons_with_index(image, points):
    texts = [str(i) for i in range(len(points))]
    res_img = vis_points(image.copy(), points, texts)
    return res_img
