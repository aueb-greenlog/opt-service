
class Node:
    
    def __init__(self, id: int, x: int, y: int, wd: int, sd:int, tws: int, twe: int, st: int, isd: bool) -> None:
        
        self.id = id
        self.x_coord = x
        self.y_coord = y
        self.weight_demand = wd
        self.spatial_demand = sd
        self.tw_start = tws
        self.tw_end = twe
        self.service_time = st
        self.is_depot = isd

    def print_node(self):

        print(f"ID = {self.id} X = {self.x_coord} Y = {self.y_coord} WD = {self.weight_demand} SD = {self.spatial_demand} TWS = {self.tw_start} TWE = {self.tw_end} ST = {self.service_time} ISD = {self.is_depot}")
