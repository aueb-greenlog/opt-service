
from abc import ABC, abstractmethod


class Move(ABC):

    def __init__(self) -> None:
        
        self.origin_workday_ix = -1
        self.target_workday_ix = -1
        self.origin_trip_ix = -1
        self.target_trip_ix = -1
        self.origin_node_ix = -1
        self.target_node_ix = -1
        self.new_solution_penalized_cost = 10 ** 9
        self.new_origin_workday_distance = -1
        self.new_origin_workday_excess_weight_load = -1
        self.new_origin_workday_excess_spatial_load = -1
        self.new_origin_workday_time_warp = -1
        self.new_target_workday_distance = -1
        self.new_target_workday_excess_weight_load = -1
        self.new_target_workday_excess_spatial_load = -1
        self.new_target_workday_time_warp = -1
        self.origin_trip_empty = False
        self.open_new_trip = False
        self.found_move = False    

    @abstractmethod
    def apply_move(self, solution): pass

    def copy_move(self, other):

        self.origin_workday_ix = other.origin_workday_ix
        self.target_workday_ix = other.target_workday_ix
        self.origin_trip_ix = other.origin_trip_ix
        self.target_trip_ix = other.target_trip_ix
        self.origin_node_ix = other.origin_node_ix
        self.target_node_ix = other.target_node_ix
        self.new_solution_penalized_cost = other.new_solution_penalized_cost
        self.new_origin_workday_distance = other.new_origin_workday_distance
        self.new_origin_workday_excess_weight_load = other.new_origin_workday_excess_weight_load
        self.new_origin_workday_excess_spatial_load = other.new_origin_workday_excess_spatial_load
        self.new_origin_workday_time_warp = other.new_origin_workday_time_warp
        self.new_target_workday_distance = other.new_target_workday_distance
        self.new_target_workday_excess_weight_load = other.new_target_workday_excess_weight_load
        self.new_target_workday_excess_spatial_load = other.new_target_workday_excess_spatial_load
        self.new_target_workday_time_warp = other.new_target_workday_time_warp
        self.origin_trip_empty = other.origin_trip_empty
        self.open_new_trip = other.open_new_trip
        self.found_move = other.found_move        

    def intra_workday_solution_update(self, solution):

            origin_workday = solution.workdays[self.origin_workday_ix]

            # Update solution.
            origin_workday_distance_diff = self.new_origin_workday_distance - origin_workday.distance
            origin_workday_time_warp_diff = self.new_origin_workday_time_warp - origin_workday.time_warp
            origin_workday_excess_weight_load_diff = self.new_origin_workday_excess_weight_load - origin_workday.excess_weight_load
            origin_workday_excess_spatial_load_diff = self.new_origin_workday_excess_spatial_load - origin_workday.excess_spatial_load

            solution.distance += origin_workday_distance_diff
            solution.time_warp += origin_workday_time_warp_diff
            solution.excess_weight_load += origin_workday_excess_weight_load_diff
            solution.excess_spatial_load += origin_workday_excess_spatial_load_diff

            # Update workday.
            origin_workday.distance = self.new_origin_workday_distance
            origin_workday.time_warp = self.new_origin_workday_time_warp
            origin_workday.excess_weight_load = self.new_origin_workday_excess_weight_load
            origin_workday.excess_spatial_load = self.new_origin_workday_excess_spatial_load

            solution.keep_track_of_map(self.origin_workday_ix)

    def inter_workday_solution_update(self, solution):
        
        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]

        # Update solution.
        origin_workday_distance_diff = self.new_origin_workday_distance - origin_workday.distance
        origin_workday_time_warp_diff = self.new_origin_workday_time_warp - origin_workday.time_warp
        origin_workday_excess_weight_load_diff = self.new_origin_workday_excess_weight_load - origin_workday.excess_weight_load
        origin_workday_excess_spatial_load_diff = self.new_origin_workday_excess_spatial_load - origin_workday.excess_spatial_load

        target_workday_distance_diff = self.new_target_workday_distance - target_workday.distance
        target_workday_time_warp_diff = self.new_target_workday_time_warp - target_workday.time_warp
        target_workday_excess_weight_load_diff = self.new_target_workday_excess_weight_load - target_workday.excess_weight_load
        target_workday_excess_spatial_load_diff = self.new_target_workday_excess_spatial_load - target_workday.excess_spatial_load

        solution.distance += origin_workday_distance_diff + target_workday_distance_diff
        solution.time_warp += origin_workday_time_warp_diff + target_workday_time_warp_diff
        solution.excess_weight_load += origin_workday_excess_weight_load_diff + target_workday_excess_weight_load_diff
        solution.excess_spatial_load += origin_workday_excess_spatial_load_diff + target_workday_excess_spatial_load_diff

        # Update workdays.
        origin_workday.distance = self.new_origin_workday_distance
        origin_workday.time_warp = self.new_origin_workday_time_warp
        origin_workday.excess_weight_load = self.new_origin_workday_excess_weight_load
        origin_workday.excess_spatial_load = self.new_origin_workday_excess_spatial_load

        target_workday.distance = self.new_target_workday_distance
        target_workday.time_warp = self.new_target_workday_time_warp
        target_workday.excess_weight_load = self.new_target_workday_excess_weight_load
        target_workday.excess_spatial_load = self.new_target_workday_excess_spatial_load

        solution.keep_track_of_map(self.origin_workday_ix)
        solution.keep_track_of_map(self.target_workday_ix)


class InsertionMove(Move):

    def __init__(self) -> None:
        super().__init__()
        self.client = -1

    def store_move(self, cl: int, tar_w_ix: int, tar_t_ix: int, tar_n_ix: int, new_s_pc: int, new_tar_w_d: int, new_tar_w_tw: int, new_tar_w_ewl: int, new_tar_w_esl: int, open_new_t: bool, found: bool):

        self.client = cl
        self.target_workday_ix = tar_w_ix
        self.target_trip_ix = tar_t_ix
        self.target_node_ix = tar_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_target_workday_distance = new_tar_w_d
        self.new_target_workday_time_warp = new_tar_w_tw
        self.new_target_workday_excess_weight_load = new_tar_w_ewl
        self.new_target_workday_excess_spatial_load = new_tar_w_esl
        self.open_new_trip = open_new_t
        self.found_move = found

    def copy_move(self, other):
        self.client = other.client
        super().copy_move(other)

    def solution_update(self, solution):

        target_workday = solution.workdays[self.target_workday_ix]

        # Update solution.
        target_workday_distance_diff = self.new_target_workday_distance - target_workday.distance
        target_workday_time_warp_diff = self.new_target_workday_time_warp - target_workday.time_warp
        target_workday_excess_weight_load_diff = self.new_target_workday_excess_weight_load - target_workday.excess_weight_load
        target_workday_excess_spatial_load_diff = self.new_target_workday_excess_spatial_load - target_workday.excess_spatial_load

        solution.distance += target_workday_distance_diff
        solution.time_warp += target_workday_time_warp_diff
        solution.excess_weight_load += target_workday_excess_weight_load_diff
        solution.excess_spatial_load += target_workday_excess_spatial_load_diff

        # Update workday.
        target_workday.distance = self.new_target_workday_distance
        target_workday.time_warp = self.new_target_workday_time_warp
        target_workday.excess_weight_load = self.new_target_workday_excess_weight_load
        target_workday.excess_spatial_load = self.new_target_workday_excess_spatial_load

        solution.keep_track_of_map(self.target_workday_ix)        

    def apply_move(self, solution):
        
        target_workday = solution.workdays[self.target_workday_ix]

        if self.open_new_trip == True:

            if self.target_trip_ix == -1: target_workday.trips.append([self.client])
            else: target_workday.trips.insert(self.target_trip_ix, [self.client])

        else:

            target_workday.trips[self.target_trip_ix].insert(self.target_node_ix + 1, self.client)

        self.solution_update(solution)


class Exchange10Move(Move):
     
    def __init__(self) -> None:
        super().__init__()

    def store_move(self, or_w_ix: int, ta_w_ix: int, or_t_ix: int, ta_t_ix: int, or_n_ix: int, ta_n_ix: int, new_s_pc: int, new_or_w_d: int, new_or_w_ewl: int, new_or_w_esl: int, new_or_w_tw: int,
                            new_ta_w_d: int, new_ta_w_ewl: int, new_ta_w_esl: int, new_ta_w_tw: int, or_t_empty: bool, open_new_t: bool, found: bool):

        self.origin_workday_ix = or_w_ix
        self.target_workday_ix = ta_w_ix
        self.origin_trip_ix = or_t_ix
        self.target_trip_ix = ta_t_ix
        self.origin_node_ix = or_n_ix
        self.target_node_ix = ta_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_origin_workday_distance = new_or_w_d
        self.new_origin_workday_excess_weight_load = new_or_w_ewl
        self.new_origin_workday_excess_spatial_load = new_or_w_esl
        self.new_origin_workday_time_warp = new_or_w_tw
        self.new_target_workday_distance = new_ta_w_d
        self.new_target_workday_excess_weight_load = new_ta_w_ewl
        self.new_target_workday_excess_spatial_load = new_ta_w_esl
        self.new_target_workday_time_warp = new_ta_w_tw
        self.origin_trip_empty = or_t_empty
        self.open_new_trip = open_new_t
        self.found_move = found

    def apply_move(self, solution):

        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]
        origin_trip = origin_workday.trips[self.origin_trip_ix]
        origin_node_id = origin_trip[self.origin_node_ix]

        origin_trip.pop(self.origin_node_ix)

        if self.open_new_trip == True:

            if self.origin_workday_ix == self.target_workday_ix:

                if self.target_trip_ix == -1:
                    origin_workday.trips.append([origin_node_id])
                    if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)

                else:
                    
                    origin_workday.trips.insert(self.target_trip_ix, [origin_node_id])
                    if self.origin_trip_empty == True:
                        if self.target_trip_ix <= self.origin_trip_ix: origin_workday.trips.pop(self.origin_trip_ix + 1)
                        else: origin_workday.trips.pop(self.origin_trip_ix)

                self.intra_workday_solution_update(solution)

            else:

                if self.target_trip_ix == -1: target_workday.trips.append([origin_node_id])
                else: target_workday.trips.insert(self.target_trip_ix, [origin_node_id])

                if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)
                self.inter_workday_solution_update(solution)

            return

        target_trip = target_workday.trips[self.target_trip_ix]

        if self.origin_workday_ix == self.target_workday_ix:

            if self.origin_trip_ix == self.target_trip_ix:

                if self.origin_node_ix > self.target_node_ix: origin_trip.insert(self.target_node_ix + 1, origin_node_id)
                else: origin_trip.insert(self.target_node_ix, origin_node_id)

            else:

                target_trip.insert(self.target_node_ix + 1, origin_node_id)

            if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)        
            self.intra_workday_solution_update(solution)

        else:

            target_trip.insert(self.target_node_ix + 1, origin_node_id)
            
            if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)        
            self.inter_workday_solution_update(solution)


class Exchange20Move(Move):

    def __init__(self) -> None:
        super().__init__()

    def store_move(self, or_w_ix: int, ta_w_ix: int, or_t_ix: int, ta_t_ix: int, or_n_ix: int, ta_n_ix: int, new_s_pc: int, new_or_w_d: int, new_or_w_ewl: int, new_or_w_esl: int, new_or_w_tw: int,
                            new_ta_w_d: int, new_ta_w_ewl: int, new_ta_w_esl: int, new_ta_w_tw: int, or_t_empty: bool, open_new_t: bool, found: bool):

        self.origin_workday_ix = or_w_ix
        self.target_workday_ix = ta_w_ix
        self.origin_trip_ix = or_t_ix
        self.target_trip_ix = ta_t_ix
        self.origin_node_ix = or_n_ix
        self.target_node_ix = ta_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_origin_workday_distance = new_or_w_d
        self.new_origin_workday_excess_weight_load = new_or_w_ewl
        self.new_origin_workday_excess_spatial_load = new_or_w_esl
        self.new_origin_workday_time_warp = new_or_w_tw
        self.new_target_workday_distance = new_ta_w_d
        self.new_target_workday_excess_weight_load = new_ta_w_ewl
        self.new_target_workday_excess_spatial_load = new_ta_w_esl
        self.new_target_workday_time_warp = new_ta_w_tw
        self.origin_trip_empty = or_t_empty
        self.open_new_trip = open_new_t
        self.found_move = found

    def apply_move(self, solution):

        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]
        origin_trip = origin_workday.trips[self.origin_trip_ix]

        if self.open_new_trip == True:

            temp_origin_trip = origin_trip[:]
            origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
            origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end).
            subseq_to_ex = temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2] # (origin, origin + 1).

            if self.origin_workday_ix == self.target_workday_ix:

                if self.target_trip_ix == -1:
                    origin_workday.trips.append(subseq_to_ex)
                    if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)

                else:

                    origin_workday.trips.insert(self.target_trip_ix, subseq_to_ex)
                    if self.origin_trip_empty == True:
                        if self.target_trip_ix <= self.origin_trip_ix: origin_workday.trips.pop(self.origin_trip_ix + 1)
                        else: origin_workday.trips.pop(self.origin_trip_ix)

                self.intra_workday_solution_update(solution)

            else:

                if self.target_trip_ix == -1: target_workday.trips.append(subseq_to_ex)
                else: target_workday.trips.insert(self.target_trip_ix, subseq_to_ex)

                if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)
                self.inter_workday_solution_update(solution)

            return

        target_trip = target_workday.trips[self.target_trip_ix]

        if self.origin_workday_ix == self.target_workday_ix:

            if self.origin_trip_ix == self.target_trip_ix:

                first_part, second_part, third_part, last_part = None, None, None, None

                if self.origin_node_ix < self.target_node_ix:

                    first_part = origin_trip[: self.origin_node_ix] # (start, origin_previous).
                    second_part = origin_trip[self.origin_node_ix + 2: self.target_node_ix + 1] # (origin + 2, target).
                    third_part = origin_trip[self.origin_node_ix: self.origin_node_ix + 2] # (origin, origin + 1).
                    last_part = origin_trip[self.target_node_ix + 1: ] # (target_next, end).

                else:

                    first_part = origin_trip[: self.target_node_ix + 1] # (start, target).
                    second_part = origin_trip[self.origin_node_ix: self.origin_node_ix + 2] # (origin, origin + 1).
                    third_part = origin_trip[self.target_node_ix + 1: self.origin_node_ix] # (target_next, origin_previous).
                    last_part = origin_trip[self.origin_node_ix + 2: ] # (origin + 2, end).

                origin_workday.trips[self.origin_trip_ix] = first_part
                origin_workday.trips[self.origin_trip_ix].extend(second_part)
                origin_workday.trips[self.origin_trip_ix].extend(third_part)
                origin_workday.trips[self.origin_trip_ix].extend(last_part)

            else:

                temp_origin_trip = origin_trip[:]
                temp_target_trip = target_trip[:]

                origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end),

                origin_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix + 1] # (start, target).
                origin_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
                origin_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 1: ]) # (target_next, end)

            if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)        
            self.intra_workday_solution_update(solution) 

        else:

            temp_origin_trip = origin_trip[:]
            temp_target_trip = target_trip[:]

            origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
            origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end),

            target_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix + 1] # (start, target).
            target_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
            target_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 1: ]) # (target_next, end)

            if self.origin_trip_empty == True: origin_workday.trips.pop(self.origin_trip_ix)        
            self.inter_workday_solution_update(solution)


class Exchange11Move(Move):
     
    def __init__(self) -> None:
        super().__init__()

    def store_move(self, or_w_ix: int, ta_w_ix: int, or_t_ix: int, ta_t_ix: int, or_n_ix: int, ta_n_ix: int, new_s_pc: int, new_or_w_d: int, new_or_w_ewl: int, new_or_w_esl: int, new_or_w_tw: int,
                        new_ta_w_d: int, new_ta_w_ewl: int, new_ta_w_esl: int, new_ta_w_tw: int, found: bool):

        self.origin_workday_ix = or_w_ix
        self.target_workday_ix = ta_w_ix
        self.origin_trip_ix = or_t_ix
        self.target_trip_ix = ta_t_ix
        self.origin_node_ix = or_n_ix
        self.target_node_ix = ta_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_origin_workday_distance = new_or_w_d
        self.new_origin_workday_excess_weight_load = new_or_w_ewl
        self.new_origin_workday_excess_spatial_load = new_or_w_esl
        self.new_origin_workday_time_warp = new_or_w_tw
        self.new_target_workday_distance = new_ta_w_d
        self.new_target_workday_excess_weight_load = new_ta_w_ewl
        self.new_target_workday_excess_spatial_load = new_ta_w_esl
        self.new_target_workday_time_warp = new_ta_w_tw
        self.found_move = found

    def apply_move(self, solution):
        
        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]
        origin_trip = origin_workday.trips[self.origin_trip_ix]
        target_trip = target_workday.trips[self.target_trip_ix]
        origin_node_id = origin_trip[self.origin_node_ix]
        target_node_id = target_trip[self.target_node_ix]

        if self.origin_workday_ix == self.target_workday_ix:

            origin_trip[self.origin_node_ix] = target_node_id
            target_trip[self.target_node_ix] = origin_node_id
            self.intra_workday_solution_update(solution)

        else:

            origin_trip[self.origin_node_ix] = target_node_id
            target_trip[self.target_node_ix] = origin_node_id
            self.inter_workday_solution_update(solution)


class Exchange21Move(Move):

    def __init__(self) -> None:
        super().__init__()

    def store_move(self, or_w_ix: int, ta_w_ix: int, or_t_ix: int, ta_t_ix: int, or_n_ix: int, ta_n_ix: int, new_s_pc: int, new_or_w_d: int, new_or_w_ewl: int, new_or_w_esl: int, new_or_w_tw: int,
                        new_ta_w_d: int, new_ta_w_ewl: int, new_ta_w_esl: int, new_ta_w_tw: int, found: bool):

        self.origin_workday_ix = or_w_ix
        self.target_workday_ix = ta_w_ix
        self.origin_trip_ix = or_t_ix
        self.target_trip_ix = ta_t_ix
        self.origin_node_ix = or_n_ix
        self.target_node_ix = ta_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_origin_workday_distance = new_or_w_d
        self.new_origin_workday_excess_weight_load = new_or_w_ewl
        self.new_origin_workday_excess_spatial_load = new_or_w_esl
        self.new_origin_workday_time_warp = new_or_w_tw
        self.new_target_workday_distance = new_ta_w_d
        self.new_target_workday_excess_weight_load = new_ta_w_ewl
        self.new_target_workday_excess_spatial_load = new_ta_w_esl
        self.new_target_workday_time_warp = new_ta_w_tw
        self.found_move = found

    def apply_move(self, solution):
        
        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]
        origin_trip = origin_workday.trips[self.origin_trip_ix]
        target_trip = target_workday.trips[self.target_trip_ix]

        if self.origin_workday_ix == self.target_workday_ix:

            if self.origin_trip_ix == self.target_trip_ix:

                first_part, second_part, third_part, fourth_part, last_part = None, None, None, None, None

                if self.origin_node_ix < self.target_node_ix:

                    first_part = origin_trip[: self.origin_node_ix] # (start, origin_previous).
                    second_part = origin_trip[self.target_node_ix: self.target_node_ix + 1] # (target).
                    third_part = origin_trip[self.origin_node_ix + 2: self.target_node_ix] # (origin + 2, target_previous).
                    fourth_part = origin_trip[self.origin_node_ix: self.origin_node_ix + 2] # (origin, origin + 1).
                    last_part = origin_trip[self.target_node_ix + 1: ] # (target_next, end).

                else:

                    first_part = origin_trip[: self.target_node_ix] # (start, target_previous).
                    second_part = origin_trip[self.origin_node_ix: self.origin_node_ix + 2] # (origin, origin + 1).
                    third_part = origin_trip[self.target_node_ix + 1: self.origin_node_ix] # (target_next, origin_previous).
                    fourth_part = origin_trip[self.target_node_ix: self.target_node_ix + 1] # (target).
                    last_part = origin_trip[self.origin_node_ix + 2: ] # (origin + 2, end).

                origin_workday.trips[self.origin_trip_ix] = first_part
                origin_workday.trips[self.origin_trip_ix].extend(second_part)
                origin_workday.trips[self.origin_trip_ix].extend(third_part)
                origin_workday.trips[self.origin_trip_ix].extend(fourth_part)
                origin_workday.trips[self.origin_trip_ix].extend(last_part)

            else:

                temp_origin_trip = origin_trip[:]
                temp_target_trip = target_trip[:]

                origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
                origin_workday.trips[self.origin_trip_ix].extend(temp_target_trip[self.target_node_ix: self.target_node_ix + 1]) # (target).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end).

                target_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix] # (start, target_previous).
                target_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
                target_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 1: ]) # (target_next, end).

            self.intra_workday_solution_update(solution)

        else:

            temp_origin_trip = origin_trip[:]
            temp_target_trip = target_trip[:]

            origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
            origin_workday.trips[self.origin_trip_ix].extend(temp_target_trip[self.target_node_ix: self.target_node_ix + 1]) # (target).
            origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end).

            target_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix] # (start, target_previous).
            target_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
            target_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 1: ]) # (target_next, end).

            self.inter_workday_solution_update(solution)


class Exchange22Move(Move):

    def __init__(self) -> None:
        super().__init__()

    def store_move(self, or_w_ix: int, ta_w_ix: int, or_t_ix: int, ta_t_ix: int, or_n_ix: int, ta_n_ix: int, new_s_pc: int, new_or_w_d: int, new_or_w_ewl: int, new_or_w_esl: int, new_or_w_tw: int,
                        new_ta_w_d: int, new_ta_w_ewl: int, new_ta_w_esl: int, new_ta_w_tw: int, found: bool):

        self.origin_workday_ix = or_w_ix
        self.target_workday_ix = ta_w_ix
        self.origin_trip_ix = or_t_ix
        self.target_trip_ix = ta_t_ix
        self.origin_node_ix = or_n_ix
        self.target_node_ix = ta_n_ix
        self.new_solution_penalized_cost = new_s_pc
        self.new_origin_workday_distance = new_or_w_d
        self.new_origin_workday_excess_weight_load = new_or_w_ewl
        self.new_origin_workday_excess_spatial_load = new_or_w_esl
        self.new_origin_workday_time_warp = new_or_w_tw
        self.new_target_workday_distance = new_ta_w_d
        self.new_target_workday_excess_weight_load = new_ta_w_ewl
        self.new_target_workday_excess_spatial_load = new_ta_w_esl
        self.new_target_workday_time_warp = new_ta_w_tw
        self.found_move = found

    def apply_move(self, solution):
        
        origin_workday = solution.workdays[self.origin_workday_ix]
        target_workday = solution.workdays[self.target_workday_ix]
        origin_trip = origin_workday.trips[self.origin_trip_ix]
        target_trip = target_workday.trips[self.target_trip_ix]

        if self.origin_workday_ix == self.target_workday_ix:

            if self.origin_trip_ix == self.target_trip_ix:

                temp_origin_trip = origin_trip[:]
                
                origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.target_node_ix: self.target_node_ix + 2]) # (target, target + 1).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: self.target_node_ix]) # (origin + 2, target_previous).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.target_node_ix + 2: ]) # (target + 2, end).

            else:

                temp_origin_trip = origin_trip[:]
                temp_target_trip = target_trip[:]

                origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
                origin_workday.trips[self.origin_trip_ix].extend(temp_target_trip[self.target_node_ix: self.target_node_ix + 2]) # (target, target + 1).
                origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end).

                target_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix] # (start, target_previous).
                target_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
                target_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 2: ]) # (target + 2, end).

            self.intra_workday_solution_update(solution)

        else:

            temp_origin_trip = origin_trip[:]
            temp_target_trip = target_trip[:]

            origin_workday.trips[self.origin_trip_ix] = temp_origin_trip[: self.origin_node_ix] # (start, origin_previous).
            origin_workday.trips[self.origin_trip_ix].extend(temp_target_trip[self.target_node_ix: self.target_node_ix + 2]) # (target, target + 1).
            origin_workday.trips[self.origin_trip_ix].extend(temp_origin_trip[self.origin_node_ix + 2: ]) # (origin + 2, end).

            target_workday.trips[self.target_trip_ix] = temp_target_trip[: self.target_node_ix] # (start, target_previous).
            target_workday.trips[self.target_trip_ix].extend(temp_origin_trip[self.origin_node_ix: self.origin_node_ix + 2]) # (origin, origin + 1).
            target_workday.trips[self.target_trip_ix].extend(temp_target_trip[self.target_node_ix + 2: ]) # (target + 2, end).

            self.inter_workday_solution_update(solution)
