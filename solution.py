
from workday import Workday
from segment import Segment

class Solution:

    solver = None

    def __init__(self) -> None:
        
        self.workdays: list[Workday] = [Workday() for _ in range(Solution.solver.model.vehicles)]
        self.distance = 0
        self.time_warp = 0
        self.excess_weight_load = 0
        self.excess_spatial_load = 0
        self.node_map = {i:[-1, -1, -1] for i in range(1, Solution.solver.model.num_clients + 1)}

    def copy_solution(self, other):

        for w_ix in range(len(other.workdays)):
            self.workdays[w_ix].copy_workday(other.workdays[w_ix])

        self.distance = other.distance
        self.time_warp = other.time_warp
        self.excess_weight_load = other.excess_weight_load
        self.excess_spatial_load = other.excess_spatial_load

    def initialize_best(self):

        self.distance = 10 ** 6
        self.time_warp = 10 ** 6
        self.excess_weight_load = 10 ** 6
        self.excess_spatial_load = 10 ** 6

    def is_feasible(self):

        if self.time_warp == 0 and self.excess_weight_load == 0 and self.excess_spatial_load == 0: return True
        return False

    def is_feasible_check(self):

        for wd_ix, wd in enumerate(self.workdays):

            # If the workday is empty, there is nothing to check.
            if len(wd.trips) == 0: continue

            # Check load constraints.
            for tr in wd.trips:

                tr_weight_load = 0
                tr_spatial_load = 0
                
                for cl in tr:
                    tr_weight_load += Solution.solver.model.nodes[cl].weight_demand
                    tr_spatial_load += Solution.solver.model.nodes[cl].spatial_demand

                if tr_weight_load > Solution.solver.model.weight_capacity or tr_spatial_load > Solution.solver.model.spatial_capacity: return False

            # Create the workday as a single tour like 0 - trip_1 - 0 - trip_2 - ... - trin_T (- 0).
            tour = [0]
            for tr in wd.trips:
                tour.extend(tr)
                tour.append(0)

            if Solution.solver.return_depot == False: tour.pop()

            u_start_service_time = Solution.solver.model.vehicle_release_times[wd_ix]
            for i in range(1, len(tour)):

                u = Solution.solver.model.nodes[tour[i - 1]]
                v = Solution.solver.model.nodes[tour[i]]

                v_tw_start = v.tw_start
                if v.id == 0: v_tw_start = Solution.solver.model.vehicle_release_times[wd_ix]

                v_arrival_time = u_start_service_time + u.service_time + Solution.solver.model.distance_matrix[u.id][v.id]
                if v_arrival_time > v.tw_end: return False

                u_start_service_time = v_tw_start if v_arrival_time < v_tw_start else v_arrival_time

        return True

    def keep_track_of_map(self, workday_ix):

        for tr_ix, tr in enumerate(self.workdays[workday_ix].trips):
            for cl_ix, cl in enumerate(tr):

                self.node_map[cl] = [workday_ix, tr_ix, cl_ix]

    def check_analytically(self):

        seg_workday: Segment = Segment()
        seg_trip: Segment = Segment()

        for wd_ix, workday in enumerate(self.workdays):

            seg_workday.copy_from_segment(Solution.solver.vehicle_segments[wd_ix])
            for tr_ix, trip in enumerate(workday.trips):

                # Clients in trip.
                seg_trip.copy_from_segment(Solution.solver.segments[trip[0]][trip[0]])
                for i in range(1, len(trip)):

                    dxy = Solution.solver.model.distance_matrix[trip[i-1]][trip[i]]
                    Segment.merge_segments(seg_trip, seg_trip, Solution.solver.segments[trip[i]][trip[i]], dxy)

                # ... + Clients in trip.
                dxy = Solution.solver.model.distance_matrix[0][trip[0]]
                Segment.merge_trip_segments(seg_workday, seg_workday, seg_trip, dxy)

                if tr_ix == len(workday.trips) - 1 and Solution.solver.return_depot == False: continue
                
                # Clients in trip + 0.
                dxy = Solution.solver.model.distance_matrix[trip[-1]][0]
                Segment.merge_trip_segments(seg_workday, seg_workday, Solution.solver.vehicle_segments[wd_ix], dxy)

            assert workday.distance == seg_workday.distance
            assert workday.time_warp == seg_workday.time_warp
            assert workday.excess_weight_load == seg_workday.excess_weight_load
            assert workday.excess_spatial_load == seg_workday.excess_spatial_load

        total_distance = 0
        for workday in self.workdays:

            distance = 0

            for tr_ix, trip in enumerate(workday.trips):

                distance += Solution.solver.model.distance_matrix[0][trip[0]]

                for i in range(len(trip) - 1):
                    distance += Solution.solver.model.distance_matrix[trip[i]][trip[i + 1]]

                if tr_ix == len(workday.trips) - 1 and Solution.solver.return_depot == False: continue

                distance += Solution.solver.model.distance_matrix[trip[-1]][0]

            assert distance == workday.distance
            total_distance += distance
        
        assert total_distance == self.distance

    def count_workdays_and_trips(self):

        num_wds = 0
        num_trips = 0

        for wd in self.workdays:

            wd_trips = len(wd.trips)
            if wd_trips == 0: continue
            num_wds += 1
            num_trips += wd_trips

        return num_wds, num_trips

    def get_representation_for_plot(self):

        lines = []

        for wd_ix, wd in enumerate(self.workdays):

            str_wd = f"{wd_ix}: "
            num_trips = len(wd.trips)

            if num_trips == 0:

                str_wd += "-\n"
                lines.append(str_wd)
                continue

            str_wd += "0"

            for tr_ix in range(num_trips):

                tr = wd.trips[tr_ix]
                for c in tr: str_wd += f" {c}"
                if tr_ix == num_trips - 1 and Solution.solver.return_depot == False: continue
                str_wd += " 0"

            str_wd += "\n"
            lines.append(str_wd)

        return lines

    def get_end_service_time_vehicles(self):

        lines = []

        for wd_ix, wd in enumerate(self.workdays):

            str_wd = f"{wd_ix}: "

            if len(wd.trips) == 0:

                str_wd += "-\n"
                lines.append(str_wd)
                continue

            # Create the workday as a single tour like 0 - trip_1 - 0 - trip_2 - ... - trin_T (- 0).
            tour = [0]
            for tr in wd.trips:
                tour.extend(tr)
                tour.append(0)

            if Solution.solver.return_depot == False: tour.pop()

            u_start_service_time = Solution.solver.model.vehicle_release_times[wd_ix]
            for i in range(1, len(tour)):

                u = Solution.solver.model.nodes[tour[i - 1]]
                v = Solution.solver.model.nodes[tour[i]]

                v_tw_start = v.tw_start
                if v.id == 0: v_tw_start = Solution.solver.model.vehicle_release_times[wd_ix]

                v_arrival_time = u_start_service_time + u.service_time + Solution.solver.model.distance_matrix[u.id][v.id]
                u_start_service_time = v_tw_start if v_arrival_time < v_tw_start else v_arrival_time

            wd_last_node_id = tour[-1]
            wd_end_service_time = u_start_service_time + Solution.solver.model.nodes[wd_last_node_id].service_time

            str_wd += f"{wd_last_node_id} ({wd_end_service_time})\n"
            lines.append(str_wd)

        return lines

    def print_solution(self):

        print("Overall solution:")
        print(f"Distance = {self.distance} Time Warp = {self.time_warp} Excess Weight Load = {self.excess_weight_load} Excess Spatial Load = {self.excess_spatial_load}\n")
        print(f"Workdays in solution:")

        for wd_ix, wd in enumerate(self.workdays):
            
            if len(wd.trips) == 0: continue
            wd.print_workday(wd_ix)
