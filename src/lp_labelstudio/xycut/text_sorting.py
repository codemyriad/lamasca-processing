from typing import List, Dict, Any
import numpy as np

def sort_text_areas(areas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort text areas in reading order (top-to-bottom, left-to-right within similar vertical positions).
    Only includes text, headline, subheadline and author areas.
    
    Args:
        areas: List of dictionaries containing area information with keys:
            - 'value': Dict containing x, y, width, height, labels
            
    Returns:
        List of areas sorted in reading order
    """
    # Filter for text-related areas only
    text_labels = {'Text', 'Headline', 'SubHeadline', 'Author'}
    text_areas = [
        area for area in areas 
        if any(label in text_labels for label in area['value']['labels'])
    ]
    
    if not text_areas:
        return []

    # Convert to numpy array of [x, y, x+w, y+h] format for easier processing
    boxes = np.array([
        [
            area['value']['x'],
            area['value']['y'],
            area['value']['x'] + area['value']['width'],
            area['value']['y'] + area['value']['height']
        ] 
        for area in text_areas
    ])

    # Calculate vertical overlap threshold based on median box height
    heights = boxes[:, 3] - boxes[:, 1]
    median_height = np.median(heights)
    vertical_threshold = median_height * 0.5

    # Group boxes that are vertically close to each other
    groups = []
    used = set()
    
    for i in range(len(boxes)):
        if i in used:
            continue
            
        current_group = [i]
        used.add(i)
        
        # Find all boxes that are vertically close to this one
        y_mid_i = (boxes[i][1] + boxes[i][3]) / 2
        
        for j in range(len(boxes)):
            if j in used:
                continue
                
            y_mid_j = (boxes[j][1] + boxes[j][3]) / 2
            if abs(y_mid_j - y_mid_i) < vertical_threshold:
                current_group.append(j)
                used.add(j)
                
        groups.append(current_group)

    # Sort groups by average y-coordinate
    groups.sort(key=lambda g: np.mean([boxes[i][1] for i in g]))
    
    # Within each group, sort boxes left-to-right
    sorted_areas = []
    for group in groups:
        # Sort indices within group by x coordinate
        group_sorted = sorted(group, key=lambda i: boxes[i][0])
        sorted_areas.extend([text_areas[i] for i in group_sorted])

    return sorted_areas
