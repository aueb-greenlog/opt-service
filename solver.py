
from model import Model
from solution import Solution
from segment import Segment
from moves import *
from local_search import LocalSearch
from numpy.random import shuffle
from numpy import argsort


class Solver:

    def __init__(self, m: Model, return_depot: bool = True, verbose: bool = False, sanity_check: bool=False) -> None:
        
        self.model: Model = m
        self.verbose = verbose
        self.sanity_check = sanity_check
        self.return_depot = return_depot
        self.num_restarts = 5
        self.time_warp_penalty = 30
        self.excess_weight_load_penalty = 30
        self.excess_spatial_load_penalty = 30
        self.pruned_neighborhood_size = "half"
        self.pruned_neighborhood = {i:[] for i in range(1, self.model.num_clients + 1)}
        self.vehicle_segments: list[Segment] = None
        self.segments: list[list[Segment]] = None
        self.workday_segments: list[list[list[Segment]]] = None

        Segment.solver = self
        Solution.solver = self
        LocalSearch.solver = self

        self.LS = LocalSearch()

    # Solve methods.
    def solve_with_restarts(self):

        if self.verbose:
            print(f"<<<<<<<<<<<<<<< {self.model.name} >>>>>>>>>>>>>>>")

        best_solution_overall: Solution = Solution()
        best_solution_overall.initialize_best()

        for i in range(self.num_restarts):

            if self.verbose:
                print(f"------------------------------------- RESTART {i} -------------------------------------")

            best_solution_restart = self.solve()
            if self.best_is_better_than_current(best_solution_overall, best_solution_restart) == True: continue
            best_solution_overall.copy_solution(best_solution_restart)

            if self.verbose:
                print(f"!!!!!!!!!!!!! New best overall! Distance = {best_solution_overall.distance} Time Warp = {best_solution_overall.time_warp} Excess Weight Load = {best_solution_overall.excess_weight_load}  Excess Spatial Load = {best_solution_overall.excess_spatial_load} !!!!!!!!!!!!!")

        if self.verbose:
            print()
        
        return best_solution_overall

    def solve(self):

        self.init_segments()
        self.create_vehicle_segments()
        self.compute_pruned_neighborhood()

        solution: Solution = self.construct_initial_solution()

        if self.sanity_check == True:
            solution.check_analytically()

        self.vnd(solution)

        return solution

    # Utilities on solution cost.
    def penalized_cost(self, d: int, tw: int, ewl: int, esl: int): 
        return d + self.time_warp_penalty * tw + self.excess_weight_load_penalty * ewl + self.excess_spatial_load_penalty * esl

    def best_is_better_than_current(self, best: Solution, current: Solution):

        if best.is_feasible() is False and current.is_feasible() is True: return False
        if best.is_feasible() is True and current.is_feasible() is False: return True
        if self.penalized_cost(best.distance, best.time_warp, best.excess_weight_load, best.excess_spatial_load) <= self.penalized_cost(current.distance, current.time_warp, current.excess_weight_load, best.excess_spatial_load): return True
        return False

    # Utilities on initial solution construction.
    def construct_initial_solution(self):

        solution: Solution = Solution()
        self.create_segments(solution)

        clients_random_order = list(range(1, self.model.num_clients + 1))
        shuffle(clients_random_order)

        for c in clients_random_order:

            best_move: InsertionMove = InsertionMove()
            solution_pen_cost = self.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

            for wd_ix, wd in enumerate(solution.workdays):

                if len(wd.trips) == 0:

                    move: InsertionMove = self.LS.form_insertion_move_trips(solution, solution_pen_cost, c, wd_ix, 0, True)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)
                    continue

                for tr_ix, tr in enumerate(wd.trips):

                    move: InsertionMove = self.LS.form_insertion_move_trips(solution, solution_pen_cost, c, wd_ix, tr_ix, True)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)

                    move: InsertionMove = self.LS.form_insertion_move_trips(solution, solution_pen_cost, c, wd_ix, tr_ix, False)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)         

                    for tar_n_id in tr:

                        move: InsertionMove = self.LS.form_insertion_move_clients(solution, solution_pen_cost, c, tar_n_id)
                        if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                        best_move.copy_move(move)

                move: InsertionMove = self.LS.form_insertion_move_trips(solution, solution_pen_cost, c, wd_ix, -1, True)
                if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                    best_move.copy_move(move)

            best_move.apply_move(solution)
            self.update_segments(solution, [best_move.target_workday_ix])

        return solution

    # Segments.
    def init_segments(self):
        self.segments = [[Segment() for _ in range(len(self.model.nodes))] for _ in range(len(self.model.nodes))]

    def create_vehicle_segments(self):

        # Every vehicle segment will have 'earliest' equal to its release time
        # and 'latest' equal to the depot node's time window end.
        # The vehicle segments are to be used instead of the depot segment
        # in their corresponding workdays.
        depot_tw_end = self.model.nodes[0].tw_end
        self.vehicle_segments = [Segment() for _ in range(self.model.vehicles)]
        seg: Segment = None
        
        for ix, vrt in enumerate(self.model.vehicle_release_times):

            seg = self.vehicle_segments[ix]
            seg.is_empty = False
            seg.weight_load = 0
            seg.spatial_load = 0
            seg.travel_time = 0
            seg.distance = 0
            seg.first_node_earliest_visit = vrt
            seg.first_node_latest_visit = depot_tw_end
            seg.time_warp = 0
            seg.excess_weight_load = 0
            seg.excess_spatial_load = 0

    def create_segments(self, solution: Solution):

        # Create the single segments.
        for id, node in enumerate(self.model.nodes):
            Segment.create_single_segment(self.segments[id][id], node)

        # Create the segments from the trips of the workdays.
        for workday in solution.workdays:

            if len(workday.trips) == 0: continue

            for trip in workday.trips:
                
                for i in range(0, len(trip) - 1):

                    u_id = trip[i]

                    for j in range(i + 1, len(trip)):

                        v_id = trip[j]
                        v_prev_id = trip[j - 1]

                        temp = self.segments[u_id][v_prev_id]
                        dxy = self.model.distance_matrix[v_prev_id][v_id]
                        Segment.merge_segments(self.segments[u_id][v_id], temp, self.segments[v_id][v_id], dxy)

        self.create_workday_segments(solution)

    def create_workday_segments(self, solution: Solution):

        '''
        For each workday:
        Let's say that the workday consists of T trips.
        For each trip i = {0, 1, ..., T} create a segment
        seg_i_j with j >= i.
        This essentially is: trip_i + 0 + trip_i_+_1 + 0 + ... + trip_j_-_1 + 0 + trip_j.
        '''
        temp_seg: Segment = Segment()
        dxy = 0
        
        self.workday_segments = [[[Segment() if i >= tr_ix else None for i in range(len(solution.workdays[wd_ix].trips))]
                                    for tr_ix in range(len(solution.workdays[wd_ix].trips))]
                                    for wd_ix in range(len(solution.workdays))]

        for wd_ix, wd in enumerate(solution.workdays):

            for tr_ix, tr in enumerate(wd.trips):
                self.workday_segments[wd_ix][tr_ix][tr_ix].copy_from_segment(self.segments[tr[0]][tr[-1]])

            for i in range(len(wd.trips)):
                for j in range(i + 1, len(wd.trips)):

                    # i to j-1 + 0.
                    dxy = self.model.distance_matrix[wd.trips[j - 1][-1]][0]
                    Segment.merge_trip_segments(temp_seg, self.workday_segments[wd_ix][i][j - 1], self.vehicle_segments[wd_ix], dxy)

                    # + j.
                    dxy = self.model.distance_matrix[0][wd.trips[j][0]]
                    Segment.merge_trip_segments(self.workday_segments[wd_ix][i][j],
                                                temp_seg,
                                                self.workday_segments[wd_ix][j][j],
                                                dxy)

    def determine_ixs_for_segments_update(self, move):

        if move.origin_workday_ix == move.target_workday_ix: return [move.origin_workday_ix]
        else: return [move.origin_workday_ix, move.target_workday_ix]

    def update_segments(self, solution: Solution, workday_ixs: list[int]):

        for wd_ix in workday_ixs:

            for tr_ix in range(len(solution.workdays[wd_ix].trips)):

                trip = solution.workdays[wd_ix].trips[tr_ix]
            
                for i in range(0, len(trip) - 1):

                    u_id = trip[i]

                    for j in range(i + 1, len(trip)):

                        v_id = trip[j]
                        v_prev_id = trip[j - 1]

                        temp = self.segments[u_id][v_prev_id]
                        dxy = self.model.distance_matrix[v_prev_id][v_id]
                        Segment.merge_segments(self.segments[u_id][v_id], temp, self.segments[v_id][v_id], dxy)

        self.update_workday_segments(solution, workday_ixs)

    def update_workday_segments(self, solution: Solution, workday_ixs: list[int]):

        temp_seg: Segment = Segment()
        dxy = 0

        for wd_ix in workday_ixs:

            wd = solution.workdays[wd_ix]
            self.workday_segments[wd_ix] = [[Segment() if i >= tr_ix else None for i in range(len(wd.trips))] for tr_ix in range(len(wd.trips))]

            for tr_ix, tr in enumerate(wd.trips):
                self.workday_segments[wd_ix][tr_ix][tr_ix].copy_from_segment(self.segments[tr[0]][tr[-1]])

            for i in range(len(wd.trips)):
                for j in range(i + 1, len(wd.trips)):

                    # i to j-1 + 0.
                    dxy = self.model.distance_matrix[wd.trips[j - 1][-1]][0]
                    Segment.merge_trip_segments(temp_seg, self.workday_segments[wd_ix][i][j - 1], self.vehicle_segments[wd_ix], dxy)

                    # + j.
                    dxy = self.model.distance_matrix[0][wd.trips[j][0]]
                    Segment.merge_trip_segments(self.workday_segments[wd_ix][i][j],
                                                temp_seg,
                                                self.workday_segments[wd_ix][j][j],
                                                dxy)

    # Pruned neighbors.
    def compute_pruned_neighborhood(self):

        if self.pruned_neighborhood_size == "all": neighborhood_size = self.model.num_clients - 1
        elif self.pruned_neighborhood_size == "half": neighborhood_size = (self.model.num_clients - 1) // 2
        elif self.pruned_neighborhood_size == "third": neighborhood_size = (self.model.num_clients - 1) // 3
        else: neighborhood_size = self.pruned_neighborhood_size

        for cl in range(1, self.model.num_clients + 1):

            cl_distances = self.model.distance_matrix[cl]
            cl_neighbors = argsort(cl_distances)
            added = 0

            for n in cl_neighbors:

                if n == 0 or n == cl: continue

                self.pruned_neighborhood[cl].append(n)
                added += 1
                if added == neighborhood_size: break

    # Variable Neighborhood Descent.
    def vnd(self, solution: Solution):

        neighborhoods = [self.LS.search_pruned_exchange10, self.LS.search_pruned_exchange20, self.LS.search_pruned_exchange11, self.LS.search_pruned_exchange21, self.LS.search_pruned_exchange22]
        move: Move = None

        max_nb_ix = len(neighborhoods) - 1
        consecutive_non_improv_nbs = 0
        nb_ix = 0

        while True:

            neighborhood = neighborhoods[nb_ix]
            move = neighborhood(solution)

            # If an improving move is found in the current neighborhood.
            if move.new_solution_penalized_cost < self.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load):

                consecutive_non_improv_nbs = 0
                move.apply_move(solution)
                wd_ixs = self.determine_ixs_for_segments_update(move)
                self.update_segments(solution, wd_ixs)
                
                if self.sanity_check == True:
                    # Sanity check code - start.
                    assert solution.is_feasible() == solution.is_feasible_check()
                    solution.check_analytically()
                    # Sanity check code - end.

            else:

                # Jump to the next neighborhood.
                consecutive_non_improv_nbs += 1
                if consecutive_non_improv_nbs == max_nb_ix + 1: break
                if nb_ix == max_nb_ix: nb_ix = 0
                else: nb_ix += 1
