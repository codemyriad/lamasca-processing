from typing import List
import cv2
import numpy as np


def projection_by_bboxes(boxes: np.array, axis: int) -> np.ndarray:
    """Generate a projection histogram from a set of bounding boxes.
    
    Creates a per-pixel projection histogram by counting overlapping boxes
    along the specified axis.

    Args:
        boxes: Array of shape [N, 4] containing bounding box coordinates 
              in format [x1, y1, x2, y2]
        axis: Projection direction
              0 - Project onto x-axis (horizontal projection)
              1 - Project onto y-axis (vertical projection)

    Returns:
        1D projection histogram array. Length equals maximum coordinate 
        along projection axis. Each value counts number of overlapping
        boxes at that position.
    """
    assert axis in [0, 1]
    length = np.max(boxes[:, axis::2])
    res = np.zeros(length, dtype=int)
    # TODO: how to remove for loop?
    for start, end in boxes[:, axis::2]:
        res[start:end] += 1
    return res


# from: https://dothinking.github.io/2021-06-19-%E9%80%92%E5%BD%92%E6%8A%95%E5%BD%B1%E5%88%86%E5%89%B2%E7%AE%97%E6%B3%95/#:~:text=%E9%80%92%E5%BD%92%E6%8A%95%E5%BD%B1%E5%88%86%E5%89%B2%EF%BC%88Recursive%20XY,%EF%BC%8C%E5%8F%AF%E4%BB%A5%E5%88%92%E5%88%86%E6%AE%B5%E8%90%BD%E3%80%81%E8%A1%8C%E3%80%82
def split_projection_profile(arr_values: np.array, min_value: float, min_gap: float):
    """Split projection profile:

    ```
                              ┌──┐
         arr_values           │  │       ┌─┐───
             ┌──┐             │  │       │ │ |
             │  │             │  │ ┌───┐ │ │min_value
             │  │<- min_gap ->│  │ │   │ │ │ |
         ────┴──┴─────────────┴──┴─┴───┴─┴─┴─┴───
         0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
    ```

    Args:
        arr_values (np.array): 1-d array representing the projection profile.
        min_value (float): Ignore the profile if `arr_value` is less than `min_value`.
        min_gap (float): Ignore the gap if less than this value.

    Returns:
        tuple: Start indexes and end indexes of split groups.
    """
    # all indexes with projection height exceeding the threshold
    arr_index = np.where(arr_values > min_value)[0]
    if not len(arr_index):
        return

    # find zero intervals between adjacent projections
    # |  |                    ||
    # ||||<- zero-interval -> |||||
    arr_diff = arr_index[1:] - arr_index[0:-1]
    arr_diff_index = np.where(arr_diff > min_gap)[0]
    arr_zero_intvl_start = arr_index[arr_diff_index]
    arr_zero_intvl_end = arr_index[arr_diff_index + 1]

    # convert to index of projection range:
    # the start index of zero interval is the end index of projection
    arr_start = np.insert(arr_zero_intvl_end, 0, arr_index[0])
    arr_end = np.append(arr_zero_intvl_start, arr_index[-1])
    arr_end += 1  # end index will be excluded as index slice

    return arr_start, arr_end



def recursive_xy_cut(boxes: np.ndarray, indices: List[int], res: List[int]):
    """Sort boxes using a reading gravity approach.
    
    Strategy:
    1. Group boxes that are vertically close together into rows
    2. Sort boxes left-to-right within each row
    3. Process rows from top to bottom
    
    This better handles newspaper layouts where content may not align perfectly
    into columns and some elements span multiple columns.
    """
    if len(boxes) <= 1:
        if len(boxes) == 1:
            res.extend(indices)
        return

    # Convert inputs to numpy arrays if they aren't already
    boxes = np.array(boxes)
    indices = np.array(indices)
    
    # Calculate vertical overlap threshold based on median box height
    heights = boxes[:, 3] - boxes[:, 1]  # y2 - y1
    overlap_threshold = np.median(heights) * 0.5
    
    # Sort all boxes by top edge position
    sorted_by_top = boxes[:, 1].argsort()
    boxes = boxes[sorted_by_top]
    indices = indices[sorted_by_top]
    
    # Group into rows based on vertical position
    rows = []
    current_row = [0]  # Start with first box
    current_row_bottom = boxes[0][3]
    
    for i in range(1, len(boxes)):
        box = boxes[i]
        # If this box starts before the current row ends (with threshold)
        if box[1] <= current_row_bottom + overlap_threshold:
            current_row.append(i)
            current_row_bottom = max(current_row_bottom, box[3])
        else:
            # Sort current row by x position and add to result
            row_boxes = boxes[current_row]
            row_indices = indices[current_row]
            left_to_right = row_boxes[:, 0].argsort()
            res.extend(row_indices[left_to_right])
            
            # Start new row
            current_row = [i]
            current_row_bottom = box[3]
    
    # Handle last row
    if current_row:
        row_boxes = boxes[current_row]
        row_indices = indices[current_row]
        left_to_right = row_boxes[:, 0].argsort()
        res.extend(row_indices[left_to_right])




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
