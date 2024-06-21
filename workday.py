
class Workday:

    def __init__(self) -> None:
        
        self.trips = []
        self.distance = 0
        self.time_warp = 0
        self.excess_weight_load = 0
        self.excess_spatial_load = 0

    def copy_workday(self, other):

        self.trips = [t[:] for t in other.trips]
        self.distance = other.distance
        self.time_warp = other.time_warp
        self.excess_weight_load = other.excess_weight_load
        self.excess_spatial_load = other.excess_spatial_load

    def print_workday(self, ix: int=None):

        if ix == None: print("Workday:")
        else: print(f"Workday {ix}:")
        print(f"Distance = {self.distance} Time Wrap = {self.time_warp} Excess Weight Load = {self.excess_weight_load} Excess Spatial Load = {self.excess_spatial_load}")
        for i, t in enumerate(self.trips): print(f"Trip {i}: {t}")
        print()
