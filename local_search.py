
from moves import *
from solution import Solution
from workday import Workday
from segment import Segment

class LocalSearch:

    solver = None
    temp_insertion_move: InsertionMove
    temp_ex10_move: Exchange10Move
    temp_ex20_move: Exchange20Move
    temp_ex11_move: Exchange11Move
    temp_ex21_move: Exchange21Move
    temp_ex22_move: Exchange22Move
    temp_solution: Solution

    def __init__(self) -> None:
        
        if LocalSearch.solver.sanity_check == False: return
        self.temp_insertion_move = InsertionMove()
        self.temp_ex10_move = Exchange10Move()
        self.temp_ex20_move = Exchange20Move()
        self.temp_ex11_move = Exchange11Move()
        self.temp_ex21_move = Exchange21Move()
        self.temp_ex22_move = Exchange22Move()
        self.temp_solution = Solution()

    def test_move(self, move: Move, solution: Solution):

        move.apply_move(solution)
        solution.check_analytically()
        assert solution.is_feasible() == solution.is_feasible_check()

    # Insertion.
    def form_insertion_move_clients(self, solution: Solution, solution_pen_cost, client, tar_n_id):

        move: InsertionMove = InsertionMove()
        seg_tar_wd: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_tar_n_next_to_end: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        tar_n_next_id = None
        new_tar_trip_first, new_tar_trip_last = None, None
        last = 0

        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]
        tar_wd = solution.workdays[tar_wd_ix]
        tar_trip = tar_wd.trips[tar_tr_ix]
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        if tar_n_ix == len(tar_trip) - 1:
            tar_n_next_id = tar_n_id
            seg_tar_n_next_to_end.is_empty = True
        else:
            tar_n_next_id = tar_trip[tar_n_ix + 1]
            seg_tar_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_n_next_id][tar_trip[-1]])

        new_tar_trip_first = tar_trip[0]

        if tar_n_ix == len(tar_trip) - 1: new_tar_trip_last = client
        else: new_tar_trip_last = tar_trip[-1]

        # previous(target_trip) + (target_trip)' + next(target_trip).

        # Workday segment is initialized with the depot start.
        # The depot start takes into account the release time of the
        # vehicle running the current workday.
        last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

        # + previous(origin_trip).
        last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

        # Create the new target trip segment -> (target_trip)'.
        # (start, target) + (client) + (target_next, end).

        # (start, target) + (client).
        dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][client]
        Segment.merge_segments(seg_tar_trip, LocalSearch.solver.segments[new_tar_trip_first][tar_n_id], LocalSearch.solver.segments[client][client], dxy)

        # + (target_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[client][tar_n_next_id]
        Segment.merge_segments(seg_tar_trip, seg_tar_trip, seg_tar_n_next_to_end, dxy)

        # + (target_trip)'.
        last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

        # + next(target_trip).
        last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)
                    
        # + depot end.
        self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

        # Compute resulting penalized cost.
        move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, tar_wd_pen_cost, seg_tar_wd)

        move.store_move(cl=client,
                        tar_w_ix=tar_wd_ix,
                        tar_t_ix=tar_tr_ix,
                        tar_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_tar_w_d=seg_tar_wd.distance,
                        new_tar_w_tw=seg_tar_wd.time_warp,
                        new_tar_w_ewl=seg_tar_wd.excess_weight_load,
                        new_tar_w_esl=seg_tar_wd.excess_spatial_load,
                        open_new_t=False,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_insertion_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_insertion_move, self.temp_solution)

        return move

    def form_insertion_move_trips(self, solution: Solution, solution_pen_cost, client, tar_wd_ix, tar_tr_ix, open_new_trip):

        move: InsertionMove = InsertionMove()
        seg_tar_wd: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        new_tar_trip_first, new_tar_trip_last = None, None
        last = 0

        tar_wd = solution.workdays[tar_wd_ix]
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        if open_new_trip == True:

            tar_n_ix = None

            new_tar_trip_first = client
            new_tar_trip_last = client

            if tar_tr_ix == -1:

                # (all trips) + (target_trip)'.

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[client][client])
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

            else:

                # previous(target_trip) + (new_trip) + (target_trip) + next(target_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (new_trip).
                seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[client][client])
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + (target_trip) + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix - 1, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

        else:

            tar_n_ix = -1
            tar_trip = tar_wd.trips[tar_tr_ix]
            tar_n_id = tar_trip[0]

            new_tar_trip_first = client
            new_tar_trip_last = tar_trip[-1]

            # previous(target_trip) + (target_trip)' + next(target_trip).

            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

            # Create the new target trip segment -> (target_trip)'.
            # (client) + (target_trip).

            # (client) + (target_trip).
            dxy = LocalSearch.solver.model.distance_matrix[client][tar_n_id]
            Segment.merge_segments(seg_tar_trip, LocalSearch.solver.segments[client][client], LocalSearch.solver.segments[tar_n_id][new_tar_trip_last], dxy)

            # + (target_trip)'.
            last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

            # + next(target_trip).
            last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)
                        
            # + depot end.
            self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

        # Compute resulting penalized cost.
        move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, tar_wd_pen_cost, seg_tar_wd)

        move.store_move(cl=client,
                        tar_w_ix=tar_wd_ix,
                        tar_t_ix=tar_tr_ix,
                        tar_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_tar_w_d=seg_tar_wd.distance,
                        new_tar_w_tw=seg_tar_wd.time_warp,
                        new_tar_w_ewl=seg_tar_wd.excess_weight_load,
                        new_tar_w_esl=seg_tar_wd.excess_spatial_load,
                        open_new_t=open_new_trip,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_insertion_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_insertion_move, self.temp_solution)

        return move

    # Exchange10.
    def search_pruned_exchange10(self, solution: Solution):

        best_move: Exchange10Move = Exchange10Move()
        solution_pen_cost = LocalSearch.solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            for v in LocalSearch.solver.pruned_neighborhood[u]:

                move: Exchange10Move = self.form_exchange10_move_clients(solution, solution_pen_cost, u, v)
                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            
            for wd_ix in range(len(solution.workdays)):
                
                wd = solution.workdays[wd_ix]

                if len(wd.trips) == 0:
                    move: Exchange10Move = self.form_exchange10_move_trips(solution, solution_pen_cost, u, wd_ix, 0, True)
                    if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                    best_move.copy_move(move)
                    continue

                for tr_ix in range(len(wd.trips)):

                    move: Exchange10Move = self.form_exchange10_move_trips(solution, solution_pen_cost, u, wd_ix, tr_ix, False)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)

                    move: Exchange10Move = self.form_exchange10_move_trips(solution, solution_pen_cost, u, wd_ix, tr_ix, True)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)

                move: Exchange10Move = self.form_exchange10_move_trips(solution, solution_pen_cost, u, wd_ix, -1, True)
                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        return best_move

    def form_exchange10_move_clients(self, solution: Solution, solution_pen_cost, ori_n_id, tar_n_id):

        move: Exchange10Move = Exchange10Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_ori_n_next_to_end: Segment = Segment()
        seg_tar_n_next_to_end: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        ori_trip_to_be_empty = False
        ori_n_prev_id, ori_n_next_id = None, None
        tar_n_next_id = None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = None

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        
        ori_trip = ori_wd.trips[ori_tr_ix]
        tar_trip = tar_wd.trips[tar_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        ori_trip_to_be_empty = False if (len(ori_trip) > 1) else True

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        if ori_n_ix == len(ori_trip) - 1:
            ori_n_next_id = ori_n_id
            seg_ori_n_next_to_end.is_empty = True
        else:
            ori_n_next_id = ori_trip[ori_n_ix + 1]
            seg_ori_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[ori_n_next_id][ori_trip[-1]])

        if tar_n_ix == len(tar_trip) - 1:
            tar_n_next_id = tar_n_id
            seg_tar_n_next_to_end.is_empty = True
        else:
            tar_n_next_id = tar_trip[tar_n_ix + 1]
            seg_tar_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_n_next_id][tar_trip[-1]])

        if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

            if ori_n_ix == 0: new_ori_trip_first = ori_n_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 1 and tar_n_ix != len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
            elif ori_n_ix != len(ori_trip) - 1 and tar_n_ix == len(ori_trip) - 1: new_ori_trip_last = ori_n_id
            elif ori_n_ix != len(ori_trip) - 1 and tar_n_ix != len(ori_trip) - 1: new_ori_trip_last = ori_trip[-1]
            
            if ori_trip_to_be_empty == True: return move

            # previous(origin_trip) + (origin_trip)' + next(origin_trip).
        
            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                                                    
            # Create the new origin trip segment -> (origin_trip)'.
            if ori_n_ix < tar_n_ix:
                
                # (start, origin_previous) + (origin_next, target) + (origin) + (target_next, end).
            
                # (start, origin_previous) + (origin_next, target).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][ori_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_start_to_ori_n_prev, LocalSearch.solver.segments[ori_n_next_id][tar_n_id], dxy)

                # + (origin).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][ori_n_id], dxy)

                # + (target_next, end).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_tar_n_next_to_end, dxy)       

            else:
                
                if ori_n_ix - 1 == tar_n_ix: return move

                # (start, target) + (origin) + (target_next, origin_previous) + (origin_next, end).

                # (start, target).
                seg_ori_trip.copy_from_segment(LocalSearch.solver.segments[new_ori_trip_first][tar_n_id])

                # + (origin).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][ori_n_id], dxy)

                # + (target_next, origin_previous).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_next_id][ori_n_prev_id], dxy)

                # + (origin_next, end).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][ori_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_ori_n_next_to_end, dxy)

            # + (origin_trip)'.
            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

            # + next(origin_trip).
            last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                        
            # + depot end.
            self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

            # Compute resulting penalized cost.
            move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

        else:

            if ori_n_ix == 0: new_ori_trip_first = ori_n_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
            else: new_ori_trip_last = ori_trip[-1]

            new_tar_trip_first = tar_trip[0] 

            if tar_n_ix == len(tar_trip) - 1: new_tar_trip_last = ori_n_id
            else: new_tar_trip_last = tar_trip[-1]

            if ori_wd_ix == tar_wd_ix:

                if ori_tr_ix < tar_tr_ix:

                    # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                else:

                    # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix, last_tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                if ori_trip_to_be_empty == False:

                    self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                # previous(target_trip) + (target_trip)' + next(target_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        or_t_empty=ori_trip_to_be_empty,
                        open_new_t=False,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex10_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex10_move, self.temp_solution)

        return move
        
    def form_exchange10_move_trips(self, solution: Solution, solution_pen_cost, ori_n_id, tar_wd_ix, tar_tr_ix, open_new_trip):

        move: Exchange10Move = Exchange10Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_ori_n_next_to_end: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        ori_trip_to_be_empty = False
        ori_n_prev_id, ori_n_next_id = None, None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = None

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        ori_wd = solution.workdays[ori_wd_ix]
        ori_trip = ori_wd.trips[ori_tr_ix]
        tar_wd = solution.workdays[tar_wd_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        ori_trip_to_be_empty = False if (len(ori_trip) > 1) else True

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        if ori_n_ix == len(ori_trip) - 1:
            ori_n_next_id = ori_n_id
            seg_ori_n_next_to_end.is_empty = True
        else:
            ori_n_next_id = ori_trip[ori_n_ix + 1]
            seg_ori_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[ori_n_next_id][ori_trip[-1]])

        if open_new_trip == True:

            tar_n_ix = None
            tar_trip = None
            tar_n_id = None

            if ori_n_ix == 0: new_ori_trip_first = ori_n_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
            else: new_ori_trip_last = ori_trip[-1]

            new_tar_trip_first = ori_n_id
            new_tar_trip_last = ori_n_id

            if ori_wd_ix == tar_wd_ix:

                if tar_tr_ix == -1:

                    # previous(origin_trip) + (origin_trip)' + next(origin_trip) + (target_trip)'.

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                elif tar_tr_ix <= ori_tr_ix:

                    # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix - 1, last_tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                else:

                    # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix - 1, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                if ori_trip_to_be_empty == False:

                    self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                if tar_tr_ix == -1:

                    # (all trips) + (target_trip)'.

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                else:

                    # previous(target_trip) + (new_trip) + (target_trip) + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (new_trip).
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + (target_trip) + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix - 1, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        else:

            tar_n_ix = -1
            tar_trip = tar_wd.trips[tar_tr_ix]
            tar_n_id = tar_trip[0]

            if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

                if ori_trip_to_be_empty == True: return move
                if ori_n_ix == 0: return move

                new_ori_trip_first = ori_n_id
                if ori_n_ix == len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
                else: new_ori_trip_last = ori_trip[-1]

                # previous(origin_trip) + (origin_trip)' + next(origin_trip).
            
                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # Create the new origin trip segment -> (origin_trip)'.
                # (origin) + (target, origin_previous) + (origin_next, end)

                # (origin) + (target, origin_previous)
                seg_ori_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][ori_n_id])
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_id][tar_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_id][ori_n_prev_id], dxy)

                # + (origin_next, end)
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][ori_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_ori_n_next_to_end, dxy)

                # + (origin_trip)'.
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                            
                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                if ori_n_ix == 0: new_ori_trip_first = ori_n_next_id
                else: new_ori_trip_first = ori_trip[0]

                if ori_n_ix == len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
                else: new_ori_trip_last = ori_trip[-1]

                new_tar_trip_first = ori_n_id
                new_tar_trip_last = tar_trip[-1]

                if ori_wd_ix == tar_wd_ix:

                    if ori_tr_ix < tar_tr_ix:
                    
                        # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                        # Workday segment is initialized with the depot start.
                        # The depot start takes into account the release time of the
                        # vehicle running the current workday.
                        last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                        # + previous(origin_trip).
                        last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                        # + (origin_trip)'.
                        if ori_trip_to_be_empty == False:

                            self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                        # + intermediate.
                        last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                        # + (target_trip)'.
                        self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                        # + next(target_trip).
                        last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                        # + depot end.
                        self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)
                    
                    else:

                        # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                        # Workday segment is initialized with the depot start.
                        # The depot start takes into account the release time of the
                        # vehicle running the current workday.
                        last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                        # + previous(target_trip).
                        last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                        # + (target_trip)'.
                        self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                        # + intermediate.
                        last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix, last_tr_ix=ori_tr_ix, last=last)

                        # + (origin_trip)'.
                        if ori_trip_to_be_empty == False:

                            self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                        # + next(origin_trip).
                        last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                        # + depot end.
                        self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                    # Compute resulting penalized cost.
                    move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

                else:

                    # Origin workday.
                    # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange10_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, pr=ori_n_prev_id, nx=ori_n_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                    # Target workday.
                    # previous(target_trip) + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange10_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                    # Compute resulting penalized cost.
                    move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        or_t_empty=ori_trip_to_be_empty,
                        open_new_t=open_new_trip,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex10_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex10_move, self.temp_solution)

        return move

    # Exchange20.
    def search_pruned_exchange20(self, solution: Solution):

        best_move: Exchange20Move = Exchange20Move()
        solution_pen_cost = LocalSearch.solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            for v in LocalSearch.solver.pruned_neighborhood[u]:

                move: Exchange20Move = self.form_exchange20_move_clients(solution, solution_pen_cost, u, v)
                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            
            for wd_ix in range(len(solution.workdays)):
                
                wd = solution.workdays[wd_ix]

                if len(wd.trips) == 0:
                    move: Exchange20Move = self.form_exchange20_move_trips(solution, solution_pen_cost, u, wd_ix, 0, True)
                    if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                    best_move.copy_move(move)
                    continue

                for tr_ix in range(len(wd.trips)):

                    move: Exchange20Move = self.form_exchange20_move_trips(solution, solution_pen_cost, u, wd_ix, tr_ix, False)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)

                    move: Exchange20Move = self.form_exchange20_move_trips(solution, solution_pen_cost, u, wd_ix, tr_ix, True)
                    if move.new_solution_penalized_cost < best_move.new_solution_penalized_cost:
                        best_move.copy_move(move)

                move: Exchange20Move = self.form_exchange20_move_trips(solution, solution_pen_cost, u, wd_ix, -1, True)
                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        return best_move

    def form_exchange20_move_clients(self, solution: Solution, solution_pen_cost, ori_n_id, tar_n_id):

        move: Exchange20Move = Exchange20Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_subseq_next_to_end: Segment = Segment()
        seg_tar_n_next_to_end: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        ori_trip_to_be_empty = False
        ori_n_prev_id, last_in_subseq_id, subseq_next_id = None, None, None
        tar_n_next_id = None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = None

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        
        ori_trip = ori_wd.trips[ori_tr_ix]
        tar_trip = tar_wd.trips[tar_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        ori_trip_to_be_empty = False if (len(ori_trip) > 2) else True

        # There is no subsequence of 2 client starting for the origin client, as origin client is the last.
        if ori_n_ix == len(ori_trip) - 1: return move

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        last_in_subseq_id = ori_trip[ori_n_ix + 1]

        if ori_n_ix == len(ori_trip) - 2:
            subseq_next_id = ori_n_id
            seg_subseq_next_to_end.is_empty = True
        else:
            subseq_next_id = ori_trip[ori_n_ix + 2]
            seg_subseq_next_to_end.copy_from_segment(LocalSearch.solver.segments[subseq_next_id][ori_trip[-1]])

        if tar_n_ix == len(tar_trip) - 1:
            tar_n_next_id = tar_n_id
            seg_tar_n_next_to_end.is_empty = True
        else:
            tar_n_next_id = tar_trip[tar_n_ix + 1]
            seg_tar_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_n_next_id][tar_trip[-1]])

        if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

            if ori_n_ix == 0: new_ori_trip_first = subseq_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 2 and tar_n_ix != len(ori_trip) - 1: new_ori_trip_last = ori_n_prev_id
            elif ori_n_ix != len(ori_trip) - 2 and tar_n_ix == len(ori_trip) - 1: new_ori_trip_last = last_in_subseq_id
            elif ori_n_ix != len(ori_trip) - 2 and tar_n_ix != len(ori_trip) - 1: new_ori_trip_last = ori_trip[-1]

            if ori_trip_to_be_empty == True: return move

            # previous(origin_trip) + (origin_trip)' + next(origin_trip).
        
            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                                                    
            # Create the new origin trip segment -> (origin_trip)'.
            if ori_n_ix < tar_n_ix:
                
                # The whole client subsequence needs to be before the target client.
                if ori_n_ix + 1 >= tar_n_ix: return move 

                # (start, origin_previous) + (subseq_next, target) + (origin, last_in_subseq) + (target_next, end).
            
                # (start, origin_previous) + (subseq_next, target).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][subseq_next_id]
                Segment.merge_segments(seg_ori_trip, seg_start_to_ori_n_prev, LocalSearch.solver.segments[subseq_next_id][tar_n_id], dxy)

                # + (origin).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][last_in_subseq_id], dxy)

                # + (target_next, end).
                dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_tar_n_next_to_end, dxy)       

            else:
                
                # The whole client sebsequence needs to be after the target_next client.
                if ori_n_ix <= tar_n_ix + 1: return move

                # (start, target) + (origin, last_in_subseq) + (target_next, origin_previous) + (subseq_next, end).

                # (start, target).
                seg_ori_trip.copy_from_segment(LocalSearch.solver.segments[new_ori_trip_first][tar_n_id])

                # + (origin, last_in_subseq).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][last_in_subseq_id], dxy)

                # + (target_next, origin_previous).
                dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_next_id][ori_n_prev_id], dxy)

                # + (subseq_next, end).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][subseq_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_subseq_next_to_end, dxy)

            # + (origin_trip)'.
            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

            # + next(origin_trip).
            last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                        
            # + depot end.
            self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

            # Compute resulting penalized cost.
            move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

        else:

            if ori_n_ix == 0: new_ori_trip_first = subseq_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = ori_n_prev_id
            else: new_ori_trip_last = ori_trip[-1]

            new_tar_trip_first = tar_trip[0] 

            if tar_n_ix == len(tar_trip) - 1: new_tar_trip_last = last_in_subseq_id
            else: new_tar_trip_last = tar_trip[-1]

            if ori_wd_ix == tar_wd_ix:

                if ori_tr_ix < tar_tr_ix:

                    # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last) 

                else:

                    # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix, last_tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                if ori_trip_to_be_empty == False:

                    self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                # previous(target_trip) + (target_trip)' + next(target_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=seg_tar_n_next_to_end, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=tar_n_next_id, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        or_t_empty=ori_trip_to_be_empty,
                        open_new_t=False,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex20_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex20_move, self.temp_solution)

        return move

    def form_exchange20_move_trips(self, solution: Solution, solution_pen_cost, ori_n_id, tar_wd_ix, tar_tr_ix, open_new_trip):

        move: Exchange20Move = Exchange20Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_subseq_next_to_end: Segment = Segment()
        dxy: int = 0
        move_res_pen_cost = 0
        ori_trip_to_be_empty = False
        ori_n_prev_id, last_in_subseq_id, subseq_next_id = None, None, None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = None

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        
        ori_trip = ori_wd.trips[ori_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        ori_trip_to_be_empty = False if (len(ori_trip) > 2) else True

        # There is no subsequence of 2 client starting for the origin client, as origin client is the last.
        if ori_n_ix == len(ori_trip) - 1: return move

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        last_in_subseq_id = ori_trip[ori_n_ix + 1]

        if ori_n_ix == len(ori_trip) - 2:
            subseq_next_id = ori_n_id
            seg_subseq_next_to_end.is_empty = True
        else:
            subseq_next_id = ori_trip[ori_n_ix + 2]
            seg_subseq_next_to_end.copy_from_segment(LocalSearch.solver.segments[subseq_next_id][ori_trip[-1]])

        if open_new_trip == True:

            tar_n_ix = None
            tar_trip = None
            tar_n_id = None

            if ori_n_ix == 0: new_ori_trip_first = subseq_next_id
            else: new_ori_trip_first = ori_trip[0]

            if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = ori_n_prev_id
            else: new_ori_trip_last = ori_trip[-1]

            new_tar_trip_first = ori_n_id
            new_tar_trip_last = last_in_subseq_id

            if ori_wd_ix == tar_wd_ix:

                if tar_tr_ix == -1:

                    # previous(origin_trip) + (origin_trip)' + next(origin_trip) + (target_trip)'.

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                elif tar_tr_ix <= ori_tr_ix:

                    # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix - 1, last_tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                else:

                    # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix - 1, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                if ori_trip_to_be_empty == False:

                    self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                if tar_tr_ix == -1:

                    # (all trips) + (target_trip)'.

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                else:

                    # previous(target_trip) + (new_trip) + (target_trip) + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (new_trip).
                    seg_tar_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + (target_trip) + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix - 1, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        else:

            tar_n_ix = -1
            tar_trip = tar_wd.trips[tar_tr_ix]
            tar_n_id = tar_trip[0]

            if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

                if ori_trip_to_be_empty == True: return move
                if ori_n_ix == 0: return move

                new_ori_trip_first = ori_n_id
                if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = ori_n_prev_id
                else: new_ori_trip_last = ori_trip[-1]

                # previous(origin_trip) + (origin_trip)' + next(origin_trip).
            
                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # Create the new origin trip segment -> (origin_trip)'.
                # (origin, last_in_subseq) + (target, origin_previous) + (subseq_next, end)

                # (origin, last_in_subseq) + (target, origin_previous)
                seg_ori_trip.copy_from_segment(LocalSearch.solver.segments[ori_n_id][last_in_subseq_id])
                dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq_id][tar_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_id][ori_n_prev_id], dxy)

                # + (subseq_next, end)
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][subseq_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_subseq_next_to_end, dxy)

                # + (origin_trip)'.
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)
                            
                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                if ori_n_ix == 0: new_ori_trip_first = subseq_next_id
                else: new_ori_trip_first = ori_trip[0]

                if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = ori_n_prev_id
                else: new_ori_trip_last = ori_trip[-1]

                new_tar_trip_first = ori_n_id
                new_tar_trip_last = tar_trip[-1]

                if ori_wd_ix == tar_wd_ix:

                    if ori_tr_ix < tar_tr_ix:
                    
                        # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                        # Workday segment is initialized with the depot start.
                        # The depot start takes into account the release time of the
                        # vehicle running the current workday.
                        last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                        # + previous(origin_trip).
                        last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                        # + (origin_trip)'.
                        if ori_trip_to_be_empty == False:

                            self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                        # + intermediate.
                        last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                        # + (target_trip)'.
                        self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                        # + next(target_trip).
                        last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                        # + depot end.
                        self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)
                    
                    else:

                        # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                        # Workday segment is initialized with the depot start.
                        # The depot start takes into account the release time of the
                        # vehicle running the current workday.
                        last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                        # + previous(target_trip).
                        last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                        # + (target_trip)'.
                        self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                        # + intermediate.
                        last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix, last_tr_ix=ori_tr_ix, last=last)

                        # + (origin_trip)'.
                        if ori_trip_to_be_empty == False:

                            self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                        # + next(origin_trip).
                        last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                        # + depot end.
                        self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                    # Compute resulting penalized cost.
                    move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

                else:

                    # Origin workday.
                    # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    if ori_trip_to_be_empty == False:

                        self.inter_trip_exchange20_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                        last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                    # Target workday.
                    # previous(target_trip) + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange20_create_target_trip_segment(seg_tr=seg_tar_trip, seg_from_n_nx=None, n_ix=tar_n_ix, ori=ori_n_id, last_subseq=last_in_subseq_id, tar=tar_n_id, nx=None, new_first=new_tar_trip_first, new_last=new_tar_trip_last)
                    last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                    # Compute resulting penalized cost.
                    move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        or_t_empty=ori_trip_to_be_empty,
                        open_new_t=open_new_trip,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex20_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex20_move, self.temp_solution)

        return move

    # Exchange11.
    def search_pruned_exchange11(self, solution: Solution):

        best_move: Exchange11Move = Exchange11Move()
        solution_pen_cost = LocalSearch.solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

        # To handle the symmetry of Exchange11.
        is_computed = {(i, j):False for i in range(1, LocalSearch.solver.model.num_clients + 1) for j in range(1, LocalSearch.solver.model.num_clients + 1)}

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            for v in LocalSearch.solver.pruned_neighborhood[u]:

                if is_computed[(u, v)] == True: continue

                move: Exchange11Move = self.form_exchange11_move(solution, solution_pen_cost, u, v)
                is_computed[(u, v)] = True

                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        return best_move

    def form_exchange11_move(self, solution: Solution, solution_pen_cost, ori_n_id, tar_n_id):

        move: Exchange11Move = Exchange11Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_ori_n_next_to_end: Segment = Segment()
        seg_start_to_tar_n_prev: Segment = Segment()
        seg_tar_n_next_to_end: Segment = Segment()
        dxy: float = 0
        move_res_pen_cost = 0
        ori_n_prev_id, ori_n_next_id = None, None
        tar_n_prev_id, tar_n_next_id = None, None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = 0

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        ori_trip = solution.workdays[ori_wd_ix].trips[ori_tr_ix]
        tar_trip = solution.workdays[tar_wd_ix].trips[tar_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        if ori_n_ix == len(ori_trip) - 1:
            ori_n_next_id = ori_n_id
            seg_ori_n_next_to_end.is_empty = True
        else:
            ori_n_next_id = ori_trip[ori_n_ix + 1]
            seg_ori_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[ori_n_next_id][ori_trip[-1]])

        if tar_n_ix == 0:
            tar_n_prev_id = tar_n_id
            seg_start_to_tar_n_prev.is_empty = True
        else:
            tar_n_prev_id = tar_trip[tar_n_ix - 1]
            seg_start_to_tar_n_prev.copy_from_segment(LocalSearch.solver.segments[tar_trip[0]][tar_n_prev_id])

        if tar_n_ix == len(tar_trip) - 1:
            tar_n_next_id = tar_n_id
            seg_tar_n_next_to_end.is_empty = True
        else:
            tar_n_next_id = tar_trip[tar_n_ix + 1]
            seg_tar_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_n_next_id][tar_trip[-1]])

        if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

            if ori_n_ix > tar_n_ix:

                ori_n_ix, tar_n_ix = tar_n_ix, ori_n_ix
                ori_n_id, tar_n_id = tar_n_id, ori_n_id
                ori_n_prev_id, tar_n_prev_id = tar_n_prev_id, ori_n_prev_id
                ori_n_next_id, tar_n_next_id = tar_n_next_id, ori_n_next_id
                seg_start_to_ori_n_prev, seg_start_to_tar_n_prev = seg_start_to_tar_n_prev, seg_start_to_ori_n_prev
                seg_ori_n_next_to_end, seg_tar_n_next_to_end = seg_tar_n_next_to_end, seg_ori_n_next_to_end

            if ori_n_ix == tar_n_ix - 1: return move

            if ori_n_ix == 0:
                new_ori_trip_first = tar_n_id
                if tar_n_ix == len(tar_trip) - 1: new_ori_trip_last = ori_n_id
                else: new_ori_trip_last = ori_trip[-1]
            elif ori_n_ix == len(ori_trip) - 1:
                new_ori_trip_last = tar_n_id
                if tar_n_ix == 0: new_ori_trip_first = ori_n_id
                else: new_ori_trip_first = ori_trip[0]
            else:
                if tar_n_ix != 0:
                    new_ori_trip_first = ori_trip[0]
                    if tar_n_ix == len(tar_trip) - 1: new_ori_trip_last = ori_n_id
                    else: new_ori_trip_last = ori_trip[-1]
                else:
                    new_ori_trip_first = ori_n_id
                    new_ori_trip_last = ori_trip[-1]

            # previous(origin_trip) + (origin_trip)' + next(origin_trip).

            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # Create the new origin trip segment -> (origin_trip)'.
            # (start, origin_previous) + (target) + (origin_next, target_previous) + (origin) + (target_next, end).

            # (start, origin_previous) + (target).
            dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][tar_n_id]
            Segment.merge_segments(seg_ori_trip, seg_start_to_ori_n_prev, LocalSearch.solver.segments[tar_n_id][tar_n_id], dxy)

            # + (origin_next, target_previous).
            dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][ori_n_next_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_next_id][tar_n_prev_id], dxy)

            # + (origin).
            dxy = LocalSearch.solver.model.distance_matrix[tar_n_prev_id][ori_n_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][ori_n_id], dxy)

            # + (target_next, end).
            dxy = LocalSearch.solver.model.distance_matrix[ori_n_id][tar_n_next_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_tar_n_next_to_end, dxy)

            # + (origin_trip)'.
            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

            # + next(origin_trip).
            last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # + depot end.
            self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

            # Compute resulting penalized cost.
            move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

        else:
            
            if ori_n_ix == 0: new_ori_trip_first = tar_n_id
            else: new_ori_trip_first = ori_trip[0]
            if ori_n_ix == len(ori_trip) - 1: new_ori_trip_last = tar_n_id
            else: new_ori_trip_last = ori_trip[-1]
            if tar_n_ix == 0: new_tar_trip_first = ori_n_id
            else: new_tar_trip_first = tar_trip[0] 
            if tar_n_ix == len(tar_trip) - 1: new_tar_trip_last = ori_n_id
            else: new_tar_trip_last = tar_trip[-1]

            if ori_wd_ix == tar_wd_ix:

                if ori_tr_ix > tar_tr_ix:

                    ori_n_ix, tar_n_ix = tar_n_ix, ori_n_ix
                    ori_n_id, tar_n_id = tar_n_id, ori_n_id
                    ori_n_prev_id, tar_n_prev_id = tar_n_prev_id, ori_n_prev_id
                    ori_n_next_id, tar_n_next_id = tar_n_next_id, ori_n_next_id
                    seg_start_to_ori_n_prev, seg_start_to_tar_n_prev = seg_start_to_tar_n_prev, seg_start_to_ori_n_prev
                    seg_ori_n_next_to_end, seg_tar_n_next_to_end = seg_tar_n_next_to_end, seg_ori_n_next_to_end
                    ori_tr_ix, tar_tr_ix = tar_tr_ix, ori_tr_ix
                    new_ori_trip_first, new_tar_trip_first = new_tar_trip_first, new_ori_trip_first
                    new_ori_trip_last, new_tar_trip_last = new_tar_trip_last, new_ori_trip_last

                # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                self.inter_trip_exchange11_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, tar=tar_n_id, pr=ori_n_prev_id, nx=ori_n_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + intermediate.
                last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange11_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_n_nx=seg_tar_n_next_to_end, ori=ori_n_id, pr=tar_n_prev_id, nx=tar_n_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                self.inter_trip_exchange11_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_n_nx=seg_ori_n_next_to_end, tar=tar_n_id, pr=ori_n_prev_id, nx=ori_n_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                # previous(target_trip) + (target_trip)' + next(target_trip).
                    
                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange11_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_n_nx=seg_tar_n_next_to_end, ori=ori_n_id, pr=tar_n_prev_id, nx=tar_n_next_id)
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex11_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex11_move, self.temp_solution)

        return move

    # Exchange21.
    def search_pruned_exchange21(self, solution: Solution):

        best_move: Exchange21Move = Exchange21Move()
        solution_pen_cost = LocalSearch.solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            for v in LocalSearch.solver.pruned_neighborhood[u]:

                move: Exchange21Move = self.form_exchange21_move(solution, solution_pen_cost, u, v)
                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        return best_move
        
    def form_exchange21_move(self, solution: Solution, solution_pen_cost, ori_n_id, tar_n_id):

        move: Exchange21Move = Exchange21Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_subseq_next_to_end: Segment = Segment()
        seg_start_to_tar_n_prev: Segment = Segment()
        seg_tar_n_next_to_end: Segment = Segment()
        dxy: float = 0
        move_res_pen_cost = 0
        ori_n_prev_id, last_in_subseq_id, subseq_next_id = None, None, None
        tar_n_prev_id, tar_n_next_id = None, None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = 0

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        ori_trip = solution.workdays[ori_wd_ix].trips[ori_tr_ix]
        tar_trip = solution.workdays[tar_wd_ix].trips[tar_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        # There is no subsequence of 2 client starting for the origin client, as origin client is the last.
        if ori_n_ix == len(ori_trip) - 1: return move

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        last_in_subseq_id = ori_trip[ori_n_ix + 1]

        if ori_n_ix == len(ori_trip) - 2:
            subseq_next_id = ori_n_id
            seg_subseq_next_to_end.is_empty = True
        else:
            subseq_next_id = ori_trip[ori_n_ix + 2]
            seg_subseq_next_to_end.copy_from_segment(LocalSearch.solver.segments[subseq_next_id][ori_trip[-1]])

        if tar_n_ix == 0:
            tar_n_prev_id = tar_n_id
            seg_start_to_tar_n_prev.is_empty = True
        else:
            tar_n_prev_id = tar_trip[tar_n_ix - 1]
            seg_start_to_tar_n_prev.copy_from_segment(LocalSearch.solver.segments[tar_trip[0]][tar_n_prev_id])

        if tar_n_ix == len(tar_trip) - 1:
            tar_n_next_id = tar_n_id
            seg_tar_n_next_to_end.is_empty = True
        else:
            tar_n_next_id = tar_trip[tar_n_ix + 1]
            seg_tar_n_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_n_next_id][tar_trip[-1]])

        if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

            if ori_n_ix == 0:
                new_ori_trip_first = tar_n_id
                if tar_n_ix == len(tar_trip) - 1: new_ori_trip_last = last_in_subseq_id
                else: new_ori_trip_last = ori_trip[-1]
            elif ori_n_ix == len(ori_trip) - 2:
                new_ori_trip_last = tar_n_id
                if tar_n_ix == 0: new_ori_trip_first = ori_n_id
                else: new_ori_trip_first = ori_trip[0]
            else:
                if tar_n_ix != 0:
                    new_ori_trip_first = ori_trip[0]
                    if tar_n_ix == len(tar_trip) - 1: new_ori_trip_last = last_in_subseq_id
                    else: new_ori_trip_last = ori_trip[-1]
                else:
                    new_ori_trip_first = ori_n_id
                    new_ori_trip_last = ori_trip[-1]

            # previous(origin_trip) + (origin_trip)' + next(origin_trip).

            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # Create the new origin trip segment -> (origin_trip)'.
            if ori_n_ix < tar_n_ix:

                # The whole client subsequence needs to be before the target_previous.
                if ori_n_ix + 1 >= tar_n_ix - 1: return move

                # (depot, origin_previous) + (target) + (subseq_next, target_previous) + (origin, last_in_subseq) + (target_next, end).

                # (depot, origin_previous) + (target).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][tar_n_id]
                Segment.merge_segments(seg_ori_trip, seg_start_to_ori_n_prev, LocalSearch.solver.segments[tar_n_id][tar_n_id], dxy)

                # + (subseq_next, target_previous).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][subseq_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[subseq_next_id][tar_n_prev_id], dxy)

                # + (origin, last_in_subseq).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_prev_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][last_in_subseq_id], dxy)

                # + (target_next, end).
                dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_tar_n_next_to_end, dxy)

            else:

                # The whole client subsequence needs to be before the target_next.
                if ori_n_ix <= tar_n_ix + 1: return move

                # (depot, target_previous) + (origin, last_in_subseq) + (target_next, origin_previous) + (target) + (subseq_next, depot).

                # (depot, target_previous) + (origin, last_in_subseq).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_prev_id][ori_n_id]
                Segment.merge_segments(seg_ori_trip, seg_start_to_tar_n_prev, LocalSearch.solver.segments[ori_n_id][last_in_subseq_id], dxy)

                # + (target_next, origin_previous).
                dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq_id][tar_n_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_next_id][ori_n_prev_id], dxy)

                # + (target).
                dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][tar_n_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[tar_n_id][tar_n_id], dxy)

                # + (subseq_next, depot).
                dxy = LocalSearch.solver.model.distance_matrix[tar_n_id][subseq_next_id]
                Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_subseq_next_to_end, dxy)

            # + (origin_trip)'.
            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

            # + next(origin_trip).
            last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # + depot end.
            self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

            # Compute resulting penalized cost.
            move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

        else:

            if ori_n_ix == 0: new_ori_trip_first = tar_n_id
            else: new_ori_trip_first = ori_trip[0]
            if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = tar_n_id
            else: new_ori_trip_last = ori_trip[-1]
            if tar_n_ix == 0: new_tar_trip_first = ori_n_id
            else: new_tar_trip_first = tar_trip[0] 
            if tar_n_ix == len(tar_trip) - 1: new_tar_trip_last = last_in_subseq_id
            else: new_tar_trip_last = tar_trip[-1]

            if ori_wd_ix == tar_wd_ix:

                if ori_tr_ix < tar_tr_ix:

                    # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(origin_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    self.inter_trip_exchange21_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, tar=tar_n_id, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange21_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_n_nx=seg_tar_n_next_to_end, ori=ori_n_id, last_in_subseq=last_in_subseq_id, pr=tar_n_prev_id, nx=tar_n_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + next(target_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                else:

                    # previous(target_trip) + (target_trip)' + intermediate + (origin_trip)' + next(origin_trip).

                    # Workday segment is initialized with the depot start.
                    # The depot start takes into account the release time of the
                    # vehicle running the current workday.
                    last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                    # + previous(target_trip).
                    last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                    # + (target_trip)'.
                    self.inter_trip_exchange21_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_n_nx=seg_tar_n_next_to_end, ori=ori_n_id, last_in_subseq=last_in_subseq_id, pr=tar_n_prev_id, nx=tar_n_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                    # + intermediate.
                    last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=tar_tr_ix, last_tr_ix=ori_tr_ix, last=last)

                    # + (origin_trip)'.
                    self.inter_trip_exchange21_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, tar=tar_n_id, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                    last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                    # + next(origin_trip).
                    last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                    # + depot end.
                    self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                self.inter_trip_exchange21_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_subseq_next_to_end, tar=tar_n_id, pr=ori_n_prev_id, subseq_next=subseq_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                # previous(target_trip) + (target_trip)' + next(target_trip).
                    
                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange21_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_n_nx=seg_tar_n_next_to_end, ori=ori_n_id, last_in_subseq=last_in_subseq_id, pr=tar_n_prev_id, nx=tar_n_next_id)
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex21_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex21_move, self.temp_solution)

        return move

    # Exchange22.
    def search_pruned_exchange22(self, solution: Solution):

        best_move: Exchange22Move = Exchange22Move()
        solution_pen_cost = LocalSearch.solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)

        # To handle the symmetry of Exchange11.
        is_computed = {(i, j):False for i in range(1, LocalSearch.solver.model.num_clients + 1) for j in range(1, LocalSearch.solver.model.num_clients + 1)}

        for u in range(1, LocalSearch.solver.model.num_clients + 1):
            for v in LocalSearch.solver.pruned_neighborhood[u]:

                if is_computed[(u, v)] == True: continue

                move: Exchange22Move = self.form_exchange22_move(solution, solution_pen_cost, u, v)
                is_computed[(u, v)] = True

                if move.new_solution_penalized_cost >= best_move.new_solution_penalized_cost: continue
                best_move.copy_move(move)

        return best_move
        
    def form_exchange22_move(self, solution: Solution, solution_pen_cost, ori_n_id, tar_n_id):

        move: Exchange22Move = Exchange22Move()
        seg_ori_wd: Segment = Segment()
        seg_tar_wd: Segment = Segment()
        seg_ori_trip: Segment = Segment()
        seg_tar_trip: Segment = Segment()
        seg_start_to_ori_n_prev: Segment = Segment()
        seg_ori_subseq_next_to_end: Segment = Segment()
        seg_start_to_tar_n_prev: Segment = Segment()
        seg_tar_subseq_next_to_end: Segment = Segment()
        dxy: float = 0
        move_res_pen_cost = 0
        ori_n_prev_id, ori_last_in_subseq_id, ori_subseq_next_id = None, None, None
        tar_n_prev_id, tar_last_in_subseq_id, tar_subseq_next_id = None, None, None
        new_ori_trip_first = None
        new_ori_trip_last = None
        new_tar_trip_first = None
        new_tar_trip_last = None
        last = 0

        ori_wd_ix, ori_tr_ix, ori_n_ix = solution.node_map[ori_n_id]
        tar_wd_ix, tar_tr_ix, tar_n_ix = solution.node_map[tar_n_id]

        ori_wd = solution.workdays[ori_wd_ix]
        tar_wd = solution.workdays[tar_wd_ix]
        ori_trip = solution.workdays[ori_wd_ix].trips[ori_tr_ix]
        tar_trip = solution.workdays[tar_wd_ix].trips[tar_tr_ix]

        ori_wd_pen_cost = LocalSearch.solver.penalized_cost(ori_wd.distance, ori_wd.time_warp, ori_wd.excess_weight_load, ori_wd.excess_spatial_load)
        tar_wd_pen_cost = LocalSearch.solver.penalized_cost(tar_wd.distance, tar_wd.time_warp, tar_wd.excess_weight_load, tar_wd.excess_spatial_load)

        # There is no subsequence of 2 client starting for the origin client, as origin client is the last.
        if ori_n_ix == len(ori_trip) - 1: return move

        # There is no subsequence of 2 client starting for the target client, as target client is the last.
        if tar_n_ix == len(tar_trip) - 1: return move

        if ori_n_ix == 0:
            ori_n_prev_id = ori_n_id
            seg_start_to_ori_n_prev.is_empty = True
        else:
            ori_n_prev_id = ori_trip[ori_n_ix - 1]
            seg_start_to_ori_n_prev.copy_from_segment(LocalSearch.solver.segments[ori_trip[0]][ori_n_prev_id])

        ori_last_in_subseq_id = ori_trip[ori_n_ix + 1]

        if ori_n_ix == len(ori_trip) - 2:
            ori_subseq_next_id = ori_n_id
            seg_ori_subseq_next_to_end.is_empty = True
        else:
            ori_subseq_next_id = ori_trip[ori_n_ix + 2]
            seg_ori_subseq_next_to_end.copy_from_segment(LocalSearch.solver.segments[ori_subseq_next_id][ori_trip[-1]])

        if tar_n_ix == 0:
            tar_n_prev_id = tar_n_id
            seg_start_to_tar_n_prev.is_empty = True
        else:
            tar_n_prev_id = tar_trip[tar_n_ix - 1]
            seg_start_to_tar_n_prev.copy_from_segment(LocalSearch.solver.segments[tar_trip[0]][tar_n_prev_id])

        tar_last_in_subseq_id = tar_trip[tar_n_ix + 1]

        if tar_n_ix == len(tar_trip) - 2:
            tar_subseq_next_id = tar_n_id
            seg_tar_subseq_next_to_end.is_empty = True
        else:
            tar_subseq_next_id = tar_trip[tar_n_ix + 2]
            seg_tar_subseq_next_to_end.copy_from_segment(LocalSearch.solver.segments[tar_subseq_next_id][tar_trip[-1]])

        if ori_wd_ix == tar_wd_ix and ori_tr_ix == tar_tr_ix:

            if ori_n_ix > tar_n_ix:

                ori_n_ix, tar_n_ix = tar_n_ix, ori_n_ix
                ori_n_id, tar_n_id = tar_n_id, ori_n_id
                ori_n_prev_id, tar_n_prev_id = tar_n_prev_id, ori_n_prev_id
                ori_last_in_subseq_id, tar_last_in_subseq_id = tar_last_in_subseq_id, ori_last_in_subseq_id
                ori_subseq_next_id, tar_subseq_next_id = tar_subseq_next_id, ori_subseq_next_id
                seg_start_to_ori_n_prev, seg_start_to_tar_n_prev = seg_start_to_tar_n_prev, seg_start_to_ori_n_prev
                seg_ori_subseq_next_to_end, seg_tar_subseq_next_to_end = seg_tar_subseq_next_to_end, seg_ori_subseq_next_to_end

            # The whole origin subsequence needs to be before the target_previous.
            if ori_n_ix + 1 >= tar_n_ix - 1: return move;

            if ori_n_ix == 0:
                new_ori_trip_first = tar_n_id
                if tar_n_ix == len(tar_trip) - 2: new_ori_trip_last = ori_last_in_subseq_id
                else: new_ori_trip_last = ori_trip[-1]
            elif ori_n_ix == len(ori_trip) - 2:
                new_ori_trip_last = tar_last_in_subseq_id
                if tar_n_ix == 0: new_ori_trip_first = ori_n_id
                else: new_ori_trip_first = ori_trip[0]
            else:
                if tar_n_ix != 0:
                    new_ori_trip_first = ori_trip[0]
                    if tar_n_ix == len(tar_trip) - 2: new_ori_trip_last = ori_last_in_subseq_id
                    else: new_ori_trip_last = ori_trip[-1]
                else:
                    new_ori_trip_first = ori_n_id
                    new_ori_trip_last = ori_trip[-1]

            # previous(origin_trip) + (origin_trip)' + next(origin_trip).

            # Workday segment is initialized with the depot start.
            # The depot start takes into account the release time of the
            # vehicle running the current workday.
            last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

            # + previous(origin_trip).
            last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # Create the new origin trip segment -> (origin_trip)'.
            # (start, origin_previous) + (target, target_last_in_subseq) + (origin_subseq_next, target_previous) + (origin, origin_last_in_subseq) + (target_subseq_next, end).

            # (start, origin_previous) + (target, target_last_in_subseq).
            dxy = LocalSearch.solver.model.distance_matrix[ori_n_prev_id][tar_n_id]
            Segment.merge_segments(seg_ori_trip, seg_start_to_ori_n_prev, LocalSearch.solver.segments[tar_n_id][tar_last_in_subseq_id], dxy)

            # + (origin_subseq_next, target_previous).
            dxy = LocalSearch.solver.model.distance_matrix[tar_last_in_subseq_id][ori_subseq_next_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_subseq_next_id][tar_n_prev_id], dxy)

            # + (origin, origin_last_in_subseq).
            dxy = LocalSearch.solver.model.distance_matrix[tar_n_prev_id][ori_n_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, LocalSearch.solver.segments[ori_n_id][ori_last_in_subseq_id], dxy)

            # + (target_subseq_next, end).
            dxy = LocalSearch.solver.model.distance_matrix[ori_last_in_subseq_id][tar_subseq_next_id]
            Segment.merge_segments(seg_ori_trip, seg_ori_trip, seg_tar_subseq_next_to_end, dxy)

            # + (origin_trip)'.
            last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

            # + next(origin_trip).
            last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

            # + depot end.
            self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

            # Compute resulting penalized cost.
            move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

        else:
            
            if ori_n_ix == 0: new_ori_trip_first = tar_n_id
            else: new_ori_trip_first = ori_trip[0]
            if ori_n_ix == len(ori_trip) - 2: new_ori_trip_last = tar_last_in_subseq_id
            else: new_ori_trip_last = ori_trip[-1]
            if tar_n_ix == 0: new_tar_trip_first = ori_n_id
            else: new_tar_trip_first = tar_trip[0] 
            if tar_n_ix == len(tar_trip) - 2: new_tar_trip_last = ori_last_in_subseq_id
            else: new_tar_trip_last = tar_trip[-1]

            if ori_wd_ix == tar_wd_ix:

                if ori_tr_ix > tar_tr_ix:

                    ori_n_ix, tar_n_ix = tar_n_ix, ori_n_ix
                    ori_n_id, tar_n_id = tar_n_id, ori_n_id
                    ori_n_prev_id, tar_n_prev_id = tar_n_prev_id, ori_n_prev_id
                    ori_last_in_subseq_id, tar_last_in_subseq_id = tar_last_in_subseq_id, ori_last_in_subseq_id
                    ori_subseq_next_id, tar_subseq_next_id = tar_subseq_next_id, ori_subseq_next_id
                    seg_start_to_ori_n_prev, seg_start_to_tar_n_prev = seg_start_to_tar_n_prev, seg_start_to_ori_n_prev
                    seg_ori_subseq_next_to_end, seg_tar_subseq_next_to_end = seg_tar_subseq_next_to_end, seg_ori_subseq_next_to_end
                    ori_tr_ix, tar_tr_ix = tar_tr_ix, ori_tr_ix
                    new_ori_trip_first, new_tar_trip_first = new_tar_trip_first, new_ori_trip_first
                    new_ori_trip_last, new_tar_trip_last = new_tar_trip_last, new_ori_trip_last
                    
                # previous(origin_trip) + (origin_trip)' + intermediate + (target_trip)' + next(target_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                self.inter_trip_exchange22_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_ori_subseq_next_to_end, tar=tar_n_id, tar_last_in_subseq=tar_last_in_subseq_id, pr=ori_n_prev_id, subseq_next=ori_subseq_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + intermediate.
                last = self.add_intermediate_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, first_tr_ix=ori_tr_ix, last_tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange22_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_subseq_next=seg_tar_subseq_next_to_end, ori=ori_n_id, ori_last_in_subseq=ori_last_in_subseq_id, pr=tar_n_prev_id, subseq_next=tar_subseq_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_tar_trip, wd_ix=ori_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_intra_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, seg_ori_wd)

            else:

                # Origin workday.
                # previous(origin_trip) + (origin_trip)' + next(origin_trip).

                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix)

                # + previous(origin_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + (origin_trip)'.
                self.inter_trip_exchange22_create_origin_trip_segment(seg_tr=seg_ori_trip, seg_to_n_pr=seg_start_to_ori_n_prev, seg_from_subseq_next=seg_ori_subseq_next_to_end, tar=tar_n_id, tar_last_in_subseq=tar_last_in_subseq_id, pr=ori_n_prev_id, subseq_next=ori_subseq_next_id)
                last = self.add_trip(seg_wd=seg_ori_wd, seg_tr=seg_ori_trip, wd_ix=ori_wd_ix, new_first=new_ori_trip_first, new_last=new_ori_trip_last, last=last)

                # + next(origin_trip).
                last = self.add_next_trips_segment(seg_wd=seg_ori_wd, wd=ori_wd, wd_ix=ori_wd_ix, tr_ix=ori_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_ori_wd, wd_ix=ori_wd_ix, last=last)

                # Target workday.
                # previous(target_trip) + (target_trip)' + next(target_trip).
                    
                # Workday segment is initialized with the depot start.
                # The depot start takes into account the release time of the
                # vehicle running the current workday.
                last = self.add_depot_start(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix)

                # + previous(target_trip).
                last = self.add_previous_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + (target_trip)'.
                self.inter_trip_exchange22_create_target_trip_segment(seg_tr=seg_tar_trip, seg_to_n_pr=seg_start_to_tar_n_prev, seg_from_subseq_next=seg_tar_subseq_next_to_end, ori=ori_n_id, ori_last_in_subseq=ori_last_in_subseq_id, pr=tar_n_prev_id, subseq_next=tar_subseq_next_id)
                last = self.add_trip(seg_wd=seg_tar_wd, seg_tr=seg_tar_trip, wd_ix=tar_wd_ix, new_first=new_tar_trip_first, new_last=new_tar_trip_last, last=last)

                # + next(target_trip).
                last = self.add_next_trips_segment(seg_wd=seg_tar_wd, wd=tar_wd, wd_ix=tar_wd_ix, tr_ix=tar_tr_ix, last=last)

                # + depot end.
                self.add_return_to_depot(seg_wd=seg_tar_wd, wd_ix=tar_wd_ix, last=last)

                # Compute resulting penalized cost.
                move_res_pen_cost = self.compute_inter_workday_move_penalized_cost(solution_pen_cost, ori_wd_pen_cost, tar_wd_pen_cost, seg_ori_wd, seg_tar_wd)

        move.store_move(or_w_ix=ori_wd_ix,
                        ta_w_ix=tar_wd_ix,
                        or_t_ix=ori_tr_ix,
                        ta_t_ix=tar_tr_ix,
                        or_n_ix=ori_n_ix,
                        ta_n_ix=tar_n_ix,
                        new_s_pc=move_res_pen_cost,
                        new_or_w_d=seg_ori_wd.distance,
                        new_or_w_ewl=seg_ori_wd.excess_weight_load,
                        new_or_w_esl=seg_ori_wd.excess_spatial_load,
                        new_or_w_tw=seg_ori_wd.time_warp,
                        new_ta_w_d=seg_tar_wd.distance,
                        new_ta_w_ewl=seg_tar_wd.excess_weight_load,
                        new_ta_w_esl=seg_tar_wd.excess_spatial_load,
                        new_ta_w_tw=seg_tar_wd.time_warp,
                        found=True)

        if LocalSearch.solver.sanity_check == True:

            self.temp_ex22_move.copy_move(move)
            self.temp_solution.copy_solution(solution)
            self.test_move(self.temp_ex22_move, self.temp_solution)

        return move

    # General penalized cost computation.
    def compute_intra_workday_move_penalized_cost(self, solution_penalized_cost, origin_workday_penalized_cost, origin_workday_segment: Segment):

        new_origin_workday_penalized_cost = LocalSearch.solver.penalized_cost(origin_workday_segment.distance,
                                                                              origin_workday_segment.time_warp,
                                                                              origin_workday_segment.excess_weight_load,
                                                                              origin_workday_segment.excess_spatial_load)
        
        return solution_penalized_cost + (new_origin_workday_penalized_cost - origin_workday_penalized_cost)

    def compute_inter_workday_move_penalized_cost(self, solution_penalized_cost, origin_workday_penalized_cost, target_workday_penalized_cost,
                                                origin_workday_segment: Segment, target_workday_segment: Segment):
        
        new_origin_workday_penalized_cost = LocalSearch.solver.penalized_cost(origin_workday_segment.distance,
                                                                            origin_workday_segment.time_warp,
                                                                            origin_workday_segment.excess_weight_load,
                                                                            origin_workday_segment.excess_spatial_load)
        
        new_target_workday_penalized_cost = LocalSearch.solver.penalized_cost(target_workday_segment.distance,
                                                                            target_workday_segment.time_warp,
                                                                            target_workday_segment.excess_weight_load,
                                                                            target_workday_segment.excess_spatial_load)
        
        return solution_penalized_cost + (new_origin_workday_penalized_cost - origin_workday_penalized_cost) + (new_target_workday_penalized_cost - target_workday_penalized_cost)

    # General segment computations.
    def add_depot_start(self, seg_wd, wd_ix):

        seg_wd.copy_from_segment(LocalSearch.solver.vehicle_segments[wd_ix])
        return 0

    def add_previous_trips_segment(self, seg_wd: Segment, wd: Workday, wd_ix: int, tr_ix: int, last: int):

        if tr_ix > 0:

            dxy = LocalSearch.solver.model.distance_matrix[last][wd.trips[0][0]]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.workday_segments[wd_ix][0][tr_ix - 1], dxy)
            last = wd.trips[tr_ix - 1][-1]

        return last

    def add_intermediate_trips_segment(self, seg_wd: Segment, wd: Workday, wd_ix: int, first_tr_ix: int, last_tr_ix: int, last: int):

        if first_tr_ix < last_tr_ix - 1:

            dxy = LocalSearch.solver.model.distance_matrix[last][0]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.vehicle_segments[wd_ix], dxy)
            dxy = LocalSearch.solver.model.distance_matrix[0][wd.trips[first_tr_ix + 1][0]]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.workday_segments[wd_ix][first_tr_ix + 1][last_tr_ix - 1], dxy)
            last = wd.trips[last_tr_ix - 1][-1]

        return last

    def add_next_trips_segment(self, seg_wd: Segment, wd: Workday, wd_ix: int, tr_ix: int, last: int):

        if tr_ix < len(wd.trips) - 1:

            dxy = LocalSearch.solver.model.distance_matrix[last][0]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.vehicle_segments[wd_ix], dxy)
            dxy = LocalSearch.solver.model.distance_matrix[0][wd.trips[tr_ix + 1][0]]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.workday_segments[wd_ix][tr_ix + 1][-1], dxy)
            last = wd.trips[-1][-1]

        return last

    def add_return_to_depot(self, seg_wd: Segment, wd_ix: int, last: int):

        if LocalSearch.solver.return_depot == True:

            dxy = LocalSearch.solver.model.distance_matrix[last][0]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.vehicle_segments[wd_ix], dxy)

    def add_trip(self, seg_wd: Segment, seg_tr: Segment, wd_ix: int, new_first: int, new_last: int, last: int):

        # + (trip)'.
        if last != 0:
            dxy = LocalSearch.solver.model.distance_matrix[last][0]
            Segment.merge_trip_segments(seg_wd, seg_wd, LocalSearch.solver.vehicle_segments[wd_ix], dxy)
        
        dxy = LocalSearch.solver.model.distance_matrix[0][new_first]
        Segment.merge_trip_segments(seg_wd, seg_wd, seg_tr, dxy)
        last = new_last

        return last

    # For Exchange10.
    def inter_trip_exchange10_create_origin_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_n_nx: Segment, pr: int, nx: int):

        # Create the new origin trip segment -> (origin_trip)'.
        # (start, origin_previous) + (origin_next, end).
            
        # (start, origin_previous) + (origin_next, end). 
        dxy = LocalSearch.solver.model.distance_matrix[pr][nx]
        Segment.merge_segments(seg_tr, seg_to_n_pr, seg_from_n_nx, dxy)

    def inter_trip_exchange10_create_target_trip_segment(self, seg_tr: Segment, seg_from_n_nx: Segment, n_ix: int, ori: int, tar: int, nx: int, new_first: int, new_last: int):

        # Create the new target trip segment -> (target_trip)'.
        if n_ix == -1:

            # (origin) + (target_trip)
            seg_tr.copy_from_segment(LocalSearch.solver.segments[ori][ori])
            dxy = LocalSearch.solver.model.distance_matrix[ori][tar]
            Segment.merge_segments(seg_tr, seg_tr, LocalSearch.solver.segments[tar][new_last], dxy)

        else:

            # (target_trip)'.
            # (start, target) + (origin) + (target_next, end).

            # (start, target).
            seg_tr.copy_from_segment(LocalSearch.solver.segments[new_first][tar])

            # + (origin).
            dxy = LocalSearch.solver.model.distance_matrix[tar][ori]
            Segment.merge_segments(seg_tr, seg_tr, LocalSearch.solver.segments[ori][ori], dxy)

            # + (target_next, end).
            dxy = LocalSearch.solver.model.distance_matrix[ori][nx]
            Segment.merge_segments(seg_tr, seg_tr, seg_from_n_nx, dxy)

    # For Exchange20.
    def inter_trip_exchange20_create_origin_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_subseq_next: Segment, pr: int, subseq_next: int):

        # Create the new origin trip segment -> (origin_trip)'.
        # (start, origin_previous) + (subseq_next, end).

        # (start, origin_previous) + (subseq_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[pr][subseq_next]
        Segment.merge_segments(seg_tr, seg_to_n_pr, seg_from_subseq_next, dxy)

    def inter_trip_exchange20_create_target_trip_segment(self, seg_tr: Segment, seg_from_n_nx: Segment, n_ix: int, ori: int, last_subseq: int, tar: int, nx: int, new_first: int, new_last: int):

        # Create the new target trip segment -> (target_trip)'.
        if n_ix == -1:

            # (origin, last_in_subseq) + (target_trip)
            seg_tr.copy_from_segment(LocalSearch.solver.segments[ori][last_subseq])
            dxy = LocalSearch.solver.model.distance_matrix[last_subseq][tar]
            Segment.merge_segments(seg_tr, seg_tr, LocalSearch.solver.segments[tar][new_last], dxy)

        else:

            # (target_trip)'.
            # (start, target) + (origin, last_in_subseq) + (target_next, end).

            # (start, target).
            seg_tr.copy_from_segment(LocalSearch.solver.segments[new_first][tar])

            # + (origin, last_in_subseq).
            dxy = LocalSearch.solver.model.distance_matrix[tar][ori]
            Segment.merge_segments(seg_tr, seg_tr, LocalSearch.solver.segments[ori][last_subseq], dxy)

            # + (target_next, end).
            dxy = LocalSearch.solver.model.distance_matrix[last_subseq][nx]
            Segment.merge_segments(seg_tr, seg_tr, seg_from_n_nx, dxy)

    # For Exchange11.
    def inter_trip_exchange11_create_origin_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_n_nx: Segment, tar: int, pr: int, nx: int):

        # Create the new origin trip segment -> (origin_trip)'.
        # (start, origin_previous) + (target) + (origin_next, end).
        
        # (start, origin_previous) + (target).
        dxy = LocalSearch.solver.model.distance_matrix[pr][tar]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[tar][tar], dxy)

        # + (origin_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[tar][nx]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_n_nx, dxy)

    def inter_trip_exchange11_create_target_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_n_nx: Segment, ori: int, pr: int, nx: int):

        # Create the new target trip segment -> (target_trip)'.
        # (start, target_previous) + (origin) + (target_next, end).

        # (start, target_previous) + (origin).
        dxy = LocalSearch.solver.model.distance_matrix[pr][ori]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[ori][ori], dxy)

        # + (target_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[ori][nx]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_n_nx, dxy)

    # For Exchange21.
    def inter_trip_exchange21_create_origin_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_subseq_next: Segment, tar: int, pr: int, subseq_next: int):

        # Create the new origin trip segment -> (origin_trip)'.
        # (start, origin_previous) + (target) + (subseq_next, end).
        
        # (start, origin_previous) + (target).
        dxy = LocalSearch.solver.model.distance_matrix[pr][tar]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[tar][tar], dxy)

        # + (subseq_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[tar][subseq_next]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_subseq_next, dxy)

    def inter_trip_exchange21_create_target_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_n_nx: Segment, ori: int, last_in_subseq: int, pr: int, nx: int):

        # Create the new target trip segment -> (target_trip)'.
        # (start, target_previous) + (origin, last_in_subseq) + (target_next, end).

        # (start, target_previous) + (origin, last_in_subseq).
        dxy = LocalSearch.solver.model.distance_matrix[pr][ori]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[ori][last_in_subseq], dxy)

        # + (target_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[last_in_subseq][nx]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_n_nx, dxy)

    # For Exchange22.
    def inter_trip_exchange22_create_origin_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_subseq_next: Segment, tar: int, tar_last_in_subseq: int, pr: int, subseq_next: int):

        # Create the new origin trip segment -> (origin_trip)'.
        # (start, origin_previous) + (target, target_last_in_subseq) + (origin_subseq_next, end).
        
        # (start, origin_previous) + (target, target_last_in_subseq).
        dxy = LocalSearch.solver.model.distance_matrix[pr][tar]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[tar][tar_last_in_subseq], dxy)

        # + (origin_subseq_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[tar_last_in_subseq][subseq_next]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_subseq_next, dxy)

    def inter_trip_exchange22_create_target_trip_segment(self, seg_tr: Segment, seg_to_n_pr: Segment, seg_from_subseq_next: Segment, ori: int, ori_last_in_subseq: int, pr: int, subseq_next: int):

        # Create the new target trip segment -> (target_trip)'.
        # (start, target_previous) + (origin, origin_last_in_subseq) + (target_subseq_next, end).

        # (start, target_previous) + (origin, origin_last_in_subseq).
        dxy = LocalSearch.solver.model.distance_matrix[pr][ori]
        Segment.merge_segments(seg_tr, seg_to_n_pr, LocalSearch.solver.segments[ori][ori_last_in_subseq], dxy)

        # + (target_subseq_next, end).
        dxy = LocalSearch.solver.model.distance_matrix[ori_last_in_subseq][subseq_next]
        Segment.merge_segments(seg_tr, seg_tr, seg_from_subseq_next, dxy)
