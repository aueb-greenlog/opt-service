
from node import Node
from math import sqrt

class Model:

    def __init__(self, instance_file_path: str, instance_type: str) -> None:
        
        self.file_path = instance_file_path
        self.instance_type = instance_type
        self.name = None
        self.nodes: list[Node] = None
        self.distance_matrix: list[list[int]] = None
        self.vehicles = None
        self.weight_capacity = None
        self.spatial_capacity = None
        self.vehicle_release_times: list[int] = None
        self.num_clients = None

        if instance_type == "SLMN": self.read_SLMN_instance()
        if instance_type == "GL": self.read_GL_instance()

    def read_SLMN_instance(self):

        with open(self.file_path, "r") as instance_file:

            instance_lines = instance_file.readlines()

        name = instance_lines[0].strip()

        veh, w_cap = [int(e) for e in instance_lines[4].strip().split()]

        nodes = []
        n: Node = None

        depot = [int(x) for x in instance_lines[9].strip().split()]

        n = Node(id=depot[0],
                 x=depot[1],
                 y=depot[2],
                 wd=depot[3],
                 sd=0,
                 tws=depot[4],
                 twe=depot[5],
                 st=depot[6],
                 isd=True)

        nodes.append(n)

        for line in instance_lines[10:]:

            client = [int(x) for x in line.strip().split()]

            n = Node(id=client[0],
                    x=client[1],
                    y=client[2],
                    wd=client[3],
                    sd=0,
                    tws=client[4],
                    twe=client[5],
                    st=client[6],
                    isd=False)
            
            nodes.append(n)

        self.name = name
        self.nodes = nodes
        self.vehicles = veh
        self.weight_capacity = w_cap
        self.num_clients = len(nodes) - 1

        self.compute_distance_matrix()

        # Add the vehicle release times equal to the depot's time window start.
        self.vehicle_release_times = [self.nodes[0].tw_start for _ in range(self.vehicles)]

        # Add the spatial capacity equal to a positive number. All spatial demands are 0.
        self.spatial_capacity = 66

    def compute_distance_matrix(self):

        self.distance_matrix = [[0.0 for _ in range(len(self.nodes))] for _ in range(len(self.nodes))]

        for i in range(len(self.nodes)):
            for j in range(len(self.nodes)):
                d = sqrt((self.nodes[i].x_coord - self.nodes[j].x_coord)**2 + (self.nodes[i].y_coord - self.nodes[j].y_coord)**2)
                self.distance_matrix[i][j] = round(d)

    def read_GL_instance(self):

        with open(self.file_path, "r") as f:
            instance_lines = f.readlines()

        name = instance_lines[0].strip()
        num_clients = int(instance_lines[3].strip())
        num_vehicles, vehicle_weight_capacity, vehicle_spatial_capacity = [int(x) for x in instance_lines[7].strip().split()]

        veh_rel_t = []
        for line in instance_lines[10: 10 + num_vehicles]: veh_rel_t.append(int(line.strip().split()[1]))

        nodes_after = 10 + num_vehicles + 3

        nodes = []
        n: Node = None

        depot = [int(x) for x in instance_lines[nodes_after].strip().split()]

        n = Node(id=depot[0],
                 x=0,
                 y=0,
                 wd=depot[1],
                 sd=depot[2],
                 tws=depot[3],
                 twe=depot[4],
                 st=depot[5],
                 isd=True)
        
        nodes.append(n)

        for i in range(1, num_clients + 1):

            client = [int(x) for x in instance_lines[nodes_after + i].strip().split()]

            n = Node(id=client[0],
                    x=0,
                    y=0,
                    wd=client[1],
                    sd=client[2],
                    tws=client[3],
                    twe=client[4],
                    st=client[5],
                    isd=False)

            nodes.append(n)

        travel_times_after = nodes_after + num_clients + 4
        dm = [[0 for _ in range(num_clients + 1)] for _ in range(num_clients + 1)]

        for i in range(0, num_clients + 1):

            distances_with_id = [int(x) for x in instance_lines[travel_times_after + i].strip().split()]
            dm[distances_with_id[0]] = distances_with_id[1:]

        self.name = name
        self.num_clients = num_clients
        self.vehicles = num_vehicles
        self.weight_capacity = vehicle_weight_capacity
        self.spatial_capacity = vehicle_spatial_capacity
        self.vehicle_release_times = veh_rel_t
        self.nodes = nodes
        self.distance_matrix = dm
