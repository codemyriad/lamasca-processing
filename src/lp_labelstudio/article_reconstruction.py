from typing import List, Dict, Any, Tuple
import numpy as np
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Zone:
    id: str
    x: float
    y: float
    width: float 
    height: float
    label: str
    debug_weights: dict = None  # Store weight calculation details

class ArticleReconstructor:
    def __init__(self):
        self.zones: List[Zone] = []
        self.graph = defaultdict(list)
        
    def add_zone(self, zone_data: Dict[str, Any]) -> None:
        """Add a zone from Label Studio annotation data"""
        if 'value' not in zone_data or 'labels' not in zone_data['value']:
            return
            
        zone = Zone(
            id=zone_data['id'],
            x=zone_data['value']['x'],
            y=zone_data['value']['y'], 
            width=zone_data['value']['width'],
            height=zone_data['value']['height'],
            label=zone_data['value']['labels'][0]
        )
        self.zones.append(zone)

    def build_graph(self) -> None:
        """Build connectivity graph between zones"""
        # Sort zones by y-coordinate for top-down processing
        self.zones.sort(key=lambda z: z.y)
        
        # Build edges between zones based on spatial relationships
        for i, zone1 in enumerate(self.zones):
            for zone2 in self.zones[i+1:]:
                weight = self._calculate_edge_weight(zone1, zone2)
                if weight > 0:
                    self.graph[zone1.id].append((zone2.id, weight))

    def _calculate_edge_weight(self, zone1: Zone, zone2: Zone) -> float:
        """Calculate edge weight between two zones based on spatial relationship"""
        debug_info = {}
        weight = 1.0
        
        # Calculate vertical and horizontal overlap
        x_overlap = max(0, min(zone1.x + zone1.width, zone2.x + zone2.width) - max(zone1.x, zone2.x))
        y_overlap = max(0, min(zone1.y + zone1.height, zone2.y + zone2.height) - max(zone1.y, zone2.y))
        
        # Penalize distance between zones
        distance = np.sqrt((zone1.x - zone2.x)**2 + (zone1.y - zone2.y)**2)
        distance_factor = max(0, 1 - distance/100)
        weight *= distance_factor
        debug_info['distance'] = f"{distance:.1f}px → {distance_factor:.2f}"
        
        # Bonus for vertical alignment
        if x_overlap > 0:
            weight *= 1.5
            debug_info['alignment'] = "1.5x"
            
        # Bonus for compatible types (e.g. headline -> text)
        if zone1.label == "Headline" and zone2.label == "Text":
            weight *= 2.0
            debug_info['type_match'] = "2.0x"
            
        zone1.debug_weights = debug_info
        return weight

    def reconstruct_articles(self) -> List[List[Zone]]:
        """Group zones into articles using the connectivity graph"""
        articles = []
        visited = set()
        
        # Start with headlines
        headlines = [z for z in self.zones if z.label == "Headline"]
        
        for headline in headlines:
            if headline.id in visited:
                continue
                
            # Start new article with this headline
            article = [headline]
            visited.add(headline.id)
            
            # Find connected zones using graph
            stack = [(nid, w) for nid, w in self.graph[headline.id]]
            while stack:
                zone_id, weight = max(stack, key=lambda x: x[1])
                stack.remove((zone_id, weight))
                
                if zone_id not in visited:
                    zone = next(z for z in self.zones if z.id == zone_id)
                    article.append(zone)
                    visited.add(zone_id)
                    stack.extend(self.graph[zone_id])
                    
            articles.append(article)
            
        return articles
