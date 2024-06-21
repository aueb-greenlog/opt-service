
from node import Node

class Segment:

    solver = None

    def __init__(self) -> None:
        
        self.is_empty = True
        self.weight_load = None
        self.excess_weight_load = None
        self.spatial_load = None
        self.excess_spatial_load = None
        self.travel_time = None
        self.distance = None
        self.time_warp = None
        self.first_node_earliest_visit = None
        self.first_node_latest_visit = None

    def copy_from_segment(self, other):

        self.is_empty = other.is_empty
        self.weight_load = other.weight_load
        self.excess_weight_load = other.excess_weight_load
        self.spatial_load = other.spatial_load
        self.excess_spatial_load = other.excess_spatial_load
        self.travel_time = other.travel_time
        self.distance = other.distance
        self.time_warp = other.time_warp
        self.first_node_earliest_visit = other.first_node_earliest_visit
        self.first_node_latest_visit = other.first_node_latest_visit

    @staticmethod
    def create_single_segment(segment, node: Node):
        
        segment.is_empty = False
        segment.weight_load = node.weight_demand
        segment.spatial_load = node.spatial_demand
        segment.travel_time = node.service_time
        segment.distance = 0
        segment.first_node_earliest_visit = node.tw_start
        segment.first_node_latest_visit = node.tw_end
        segment.time_warp = 0
        segment.excess_weight_load = 0
        segment.excess_spatial_load = 0

    @staticmethod
    def merge_segments(new_segment, segment_first, segment_last, dxy: int):

        if segment_first.is_empty == True and segment_last.is_empty == True:
            new_segment.is_empty = True
            return
        if segment_first.is_empty == True:
            new_segment.copy_from_segment(segment_last)
            return
        if segment_last.is_empty == True:
            new_segment.copy_from_segment(segment_first)
            return

        if new_segment.is_empty == True: new_segment.is_empty = False

        delta = segment_first.travel_time - segment_first.time_warp + dxy
        d_wt = max(0, segment_last.first_node_earliest_visit - delta - segment_first.first_node_latest_visit)
        d_tw = max(0, segment_first.first_node_earliest_visit + delta - segment_last.first_node_latest_visit)
        
        new_segment.weight_load = segment_first.weight_load + segment_last.weight_load
        new_segment.excess_weight_load = max(0, new_segment.weight_load - Segment.solver.model.weight_capacity)
        new_segment.spatial_load = segment_first.spatial_load + segment_last.spatial_load
        new_segment.excess_spatial_load = max(0, new_segment.spatial_load - Segment.solver.model.spatial_capacity)

        new_segment.travel_time = segment_first.travel_time + segment_last.travel_time + dxy + d_wt
        new_segment.time_warp = segment_first.time_warp + segment_last.time_warp + d_tw
        new_segment.first_node_earliest_visit = max(segment_last.first_node_earliest_visit - delta, segment_first.first_node_earliest_visit) - d_wt
        new_segment.first_node_latest_visit = min(segment_last.first_node_latest_visit - delta, segment_first.first_node_latest_visit) + d_tw

        new_segment.distance = segment_first.distance + dxy + segment_last.distance

    @staticmethod
    def merge_trip_segments(new_segment, segment_first, segment_last, dxy: int):

        if segment_first.is_empty == True and segment_last.is_empty == True:
            new_segment.is_empty = True
            return
        if segment_first.is_empty == True:
            new_segment.copy_from_segment(segment_last)
            return
        if segment_last.is_empty == True:
            new_segment.copy_from_segment(segment_first)
            return

        if new_segment.is_empty == True: new_segment.is_empty = False

        delta = segment_first.travel_time - segment_first.time_warp + dxy
        d_wt = max(0, segment_last.first_node_earliest_visit - delta - segment_first.first_node_latest_visit)
        d_tw = max(0, segment_first.first_node_earliest_visit + delta - segment_last.first_node_latest_visit)

        new_segment.weight_load = segment_first.weight_load + segment_last.weight_load
        new_segment.excess_weight_load = segment_first.excess_weight_load + segment_last.excess_weight_load # Here it is different that the original.
        new_segment.spatial_load = segment_first.spatial_load + segment_last.spatial_load
        new_segment.excess_spatial_load = segment_first.excess_spatial_load + segment_last.excess_spatial_load # Here it is different that the original.

        new_segment.travel_time = segment_first.travel_time + segment_last.travel_time + dxy + d_wt
        new_segment.time_warp = segment_first.time_warp + segment_last.time_warp + d_tw
        new_segment.first_node_earliest_visit = max(segment_last.first_node_earliest_visit - delta, segment_first.first_node_earliest_visit) - d_wt
        new_segment.first_node_latest_visit = min(segment_last.first_node_latest_visit - delta, segment_first.first_node_latest_visit) + d_tw

        new_segment.distance = segment_first.distance + dxy + segment_last.distance
