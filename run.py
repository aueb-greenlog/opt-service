
from model import Model
from solver import Solver
from time import time
from os import listdir


def run_one(instance_path: str, instance_type: str, dir_reports: str, dir_to_plot: str, dir_vehicles:str, return_to_depot: bool, sanity_check: bool, print_final_solution: bool= False):
     
    model = Model(instance_file_path=instance_path, instance_type=instance_type)
    solver = Solver(m=model, return_depot=return_to_depot, verbose=False, sanity_check=sanity_check)

    s_t = time()
    best_solution_restarts = solver.solve_with_restarts()
    e_t = time()
    exec_time = e_t - s_t

    if print_final_solution == True:    
        print(f"Average execution time per restart = {exec_time / solver.num_restarts}")
        best_solution_restarts.print_solution()

    if dir_reports != None: to_report_file(dir_reports=dir_reports, solver=solver, exec_time=exec_time, solution=best_solution_restarts)
    if dir_to_plot != None: to_plot_file(dir_to_plot=dir_to_plot, instance_name=model.name, solution=best_solution_restarts)
    if dir_vehicles != None: store_vehicle_end_service_times(dir_vehicles=dir_vehicles, instance_name=model.name, solution=best_solution_restarts)

def run_all(dir_instances: str, instance_type: str, dir_reports: str, dir_to_plot: str, dir_vehicles: str, return_to_depot: bool, sanity_check: bool):
     
    for instance in sorted(listdir(dir_instances)):

        instance_path = f"{dir_instances}/{instance}"
        run_one(instance_path=instance_path,
                instance_type=instance_type,
                dir_reports=dir_reports,
                dir_to_plot=dir_to_plot,
                dir_vehicles=dir_vehicles,
                return_to_depot=return_to_depot,
                sanity_check=sanity_check)

        print(f"{instance} ... DONE")

def to_report_file(dir_reports, solver: Solver, exec_time, solution):

        total_time_restarts = exec_time
        avg_restart_time = total_time_restarts / solver.num_restarts
        best_penalized_cost = solver.penalized_cost(solution.distance, solution.time_warp, solution.excess_weight_load, solution.excess_spatial_load)
        best_feasibility = solution.is_feasible()
        best_num_wds, best_num_trips = solution.count_workdays_and_trips()

        with open(f"{dir_reports}/{solver.model.name}_report.txt", "w") as f:

            f.write(f"------------------------- {solver.model.name} -------------------------\n")
            f.write(f"Parameters: Restarts = {solver.num_restarts} TW Penalty = {solver.time_warp_penalty} EWL Penalty = {solver.excess_weight_load_penalty} ESL Penalty = {solver.excess_spatial_load_penalty}\n")
            f.write(f"Best solution penalized cost = {best_penalized_cost}\n")
            f.write(f"Best solution feasibility = {best_feasibility}\n")
            f.write(f"Average restart execution time = {avg_restart_time}\n")
            f.write(f"Number of workdays utilized = {best_num_wds}\n")
            f.write(f"Number of trips utilized = {best_num_trips}\n\n")

def to_plot_file(dir_to_plot, instance_name, solution):
     
     lines = [f"{instance_name}\n\n"]
     lines.extend(solution.get_representation_for_plot())

     with open(f"{dir_to_plot}/{instance_name}_to_plot.txt", "w") as f: f.writelines(lines)

def store_vehicle_end_service_times(dir_vehicles, instance_name, solution):

     lines = [f"{instance_name}\n\n"]
     lines.extend(solution.get_end_service_time_vehicles())

     with open(f"{dir_vehicles}/{instance_name}_end_service.txt", "w") as f: f.writelines(lines)


# run_one(instance_path="./INSTANCES/SLMN_25/RC201.txt",
#         instance_type="SLMN",
#         dir_reports=None,
#         dir_to_plot=None,
#         dir_vehicles=None,
#         return_to_depot=True,
#         sanity_check=True,
#         print_final_solution=True)
def execute_vrp(filename):
    run_one(instance_path=f"./files/{filename}",
             instance_type="GL",
             dir_reports="./reports/",
             dir_to_plot="./toPlot/",
             dir_vehicles="./vehicles/",
             return_to_depot=True,
             sanity_check=False,
             print_final_solution=False)

'''
run_all(dir_instances="./INSTANCES/SLMN_25",
        instance_type="SLMN",
        dir_reports=None,
        dir_to_plot=None,
        dir_vehicles=None,
        return_to_depot=True,
        sanity_check=True)
'''
# run_all(dir_instances="./INSTANCES/OX",
#         instance_type="GL",
#         dir_reports="../MTVRPTW_REPORTS/REPORTS_VND/OX",
#         dir_to_plot="../MTVRPTW_REPORTS/TO_PLOT/OX",
#         dir_vehicles="../MTVRPTW_REPORTS/VEHICLES/OX",
#         return_to_depot=True,
#         sanity_check=False)
