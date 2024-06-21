import pandas as pd
from datetime import *
import warnings
warnings.filterwarnings("ignore")

import opt_mcc
import opt_routing

def optimizer(event, livingLab, nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith, objective):
	eligibleTypes = list(set([type for v in range(len(vehicles_info)) for type in vehicles_info[v, 1] if type not in ['mobile', 'last-mile']]))
	operators = list(set(orders_info[n, 8] for n in range(nOrders)))
	serviceTime, timeLimit = 3, 300
	if livingLab == "Ispra, Italy":
		serviceTime = 1
	if event == None:
		routes, subroutes, maxOrders =  dayToDayOptimisation(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith,
					   		 								objective, eligibleTypes, serviceTime, timeLimit, operators, livingLab)
	
	return routes, subroutes, maxOrders

def dayToDayOptimisation(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith,
						 objective, eligibleTypes, serviceTime, timeLimit, operators, livingLab):
	print(datetime.now(), f" - Start of Day-to-Day Optimisation module")
	pickupCompleted, deliveryCompleted, completed, usedVehicles = [], [], [], []
	routes, subroutes, delay, maxOrders = {}, {}, 0, nOrders
	if any("mobile" in vehicles_info[v, 1] for v in range(len(vehicles_info))):
		print(datetime.now(), f" - Start of MCC Deployment.")
		warmstart = opt_mcc.formulate_mcc(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes,
										  canBeTransferredWith, "max-coveredDemand", eligibleTypes, None, None, None, None, None, None, None, None, nOrders, serviceTime)
		print(datetime.now(), f" - Computation of a warm-start solution (max timelimit : {timeLimit} seconds).")
		warmDelivery, warmPickup, warmY, warmT, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders = opt_mcc.get_warmstart(warmstart, timeLimit, "gurobi")
		milp = opt_mcc.formulate_mcc(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes,
							   canBeTransferredWith, objective, eligibleTypes, warmDelivery, warmPickup, warmY, warmT, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders, serviceTime)
		print(datetime.now(), f" - Mobile depots scheduling (max timelimit : {timeLimit} seconds).")
		routes = opt_mcc.solve_mcc(milp, timeLimit, "gurobi", locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, None, [])
		print(datetime.now(), f" - End of MCC Deployment.")
		if routes != False:
			print(datetime.now(), f" - Start of Routing.")
			for r in routes.keys():
				for stop in routes[r].keys():
					for o in operators:
						if routes[r][stop]['operator'] == o and routes[r][stop]['customers'] > 0:
							for n in routes[r][stop]['pickups']:
								pickupCompleted.append(n)
								if orders_info[n, 2] == 1:
									if n in deliveryCompleted:
										completed.append(n)
								else:
									completed.append(n)
							for n in routes[r][stop]['deliveries']:
								deliveryCompleted.append(n)
								if orders_info[n, 3] == 1:
									if n in pickupCompleted:
										completed.append(n)
								else:
									completed.append(n)
							filename = fileGenerator(livingLab, stop, routes[r][stop]['customers'], routes[r], locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, None)
							filename, routes[r], subroutes, delay = opt_routing.solve_routing(filename, routes[r], stop, travelTimes, locations_info, orders_info, orders_time, vehicles_info, eligibleTypes, subroutes, r, [], serviceTime)
							startDelay = False
							for k in routes[r].keys():
								if k == stop:
									startDelay = True
								if startDelay == True:
									if k != stop:
										routes[r][k]['timeWindow'][0] += delay
										routes[r][k]['timeWindow'][1] += delay
							start, end = routes[r][stop]['timeWindow'][0], routes[r][stop]['timeWindow'][1]
							for c in routes[r][stop]['duplicates']:
								routes[r][c]['timeWindow'][0], routes[r][c]['timeWindow'][1] = routes[r][stop]['timeWindow'][0], routes[r][stop]['timeWindow'][1]						
				for v in range(len(vehicles_info)):
					if "carrier" in vehicles_info[v, 1]:
						usedVehicles.append(v)
	else:
		print(datetime.now(), f" - Start of Routing.")
	if (routes != False and len(eligibleTypes) > 1 and "carrier" in eligibleTypes) or all("mobile" not in vehicles_info[v, 1] for v in range(len(vehicles_info))):
		for t in eligibleTypes:
			if t != "carrier":
				for o in operators:
					if any((t in vehicles_info[v, 1] and "last-mile" in vehicles_info[v, 1] and vehicles_info[v, 6] == o) for v in range(len(vehicles_info))):
						routes = opt_mcc.solve_mcc(None, timeLimit, "gurobi", locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, t, completed)
						for n in routes[f'Depot_{t}_{o}'][0]['pickups']:
							pickupCompleted.append(n)
							if orders_info[n, 2] == 1:
								if n in deliveryCompleted:
									completed.append(n)
							else:
								completed.append(n)
						for n in routes[f'Depot_{t}_{o}'][0]['deliveries']:
							deliveryCompleted.append(n)
							if orders_info[n, 3] == 1:
								if n in pickupCompleted:
									completed.append(n)
							else:
								completed.append(n)
						filename = fileGenerator(livingLab, stop, routes[r][stop]['customers'], routes[r], locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, None)
						filename, routes[f'Depot_{t}_{o}'], subroutes, delay = opt_routing.solve_routing(filename, routes[f'Depot_{t}_{o}'], 0, travelTimes, locations_info, orders_info, orders_time, vehicles_info, eligibleTypes, subroutes, f'Depot_{t}_{o}', usedVehicles, serviceTime)				
		deletedKeys = []
		for r in routes.keys():
			toBeDeleted = True
			for v in range(len(vehicles_info)):
				if r in vehicles_info[v, 0][0]:
					toBeDeleted = False
					break
			if toBeDeleted:
				deletedKeys.append(r)
		for key in deletedKeys:
			del routes[key]
	if routes != False:
		print(datetime.now(), f" - End of Routing.")

	return routes, subroutes, maxOrders

def fileGenerator(livingLab, key, nCustomers, route, locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, oldPlan):
	if livingLab == "Oxford, England":
		filename = f"OX_{key}_{nCustomers}.txt"
	if livingLab == "Barcelona, Spain":
		filename = f"BCN_{key}_{nCustomers}.txt"
	if livingLab == "Ispra, Italy":
		filename = f"ISP_{key}_{nCustomers}.txt"
	if livingLab == "Athens, Greece":
		filename = f"ATH_{key}_{nCustomers}.txt"
	if livingLab == "Flanders, Belgium":
		filename = f"FLN_{key}_{nCustomers}.txt"

	nCustomers, listNodes = 0, []
	for n in route[key]['pickups']:
		if route[key]['location'] != locations_info[orders_info[n, 4], 0]:
			nCustomers += 1
	for n in route[key]['deliveries']:
		if route[key]['location'] != locations_info[orders_info[n, 5], 0]:
			nCustomers += 1

	with open(f"./files/{filename}", 'w') as outfile:
		for char in filename:
			if char != ".":
				outfile.write(char)
			else:
				outfile.write("\n\n")
				break
		outfile.write("NUMBER CLIENTS\n")
		outfile.write(f"{nCustomers}\n\n")
		#outfile.write("NUMBER NEW REQUESTS\n")
		#outfile.write(f"{len(newOrders)}\n\n")
		outfile.write("VEHICLE\n")
		outfile.write("NUMBER	CAPACITY1	CAPACITY2\n")
		numVehicles = 0
		for v in route[key]['vehicles'].keys():
			if route[key]['vehicles'][v]['releaseTime'] <= route[key]['timeWindow'][1]:
				numVehicles += 1
		for v in route[key]['vehicles'].keys():
			cap1, cap2 = int(100*route[key]['vehicles'][v]['capacity1']), int(1000*route[key]['vehicles'][v]['capacity2'])
			break
		outfile.write(f"{numVehicles}	{cap1}		{cap2}\n\n")
		if numVehicles > 0:
			outfile.write("VEHICLE	RELEASE\n")
			numVehicles = 0
			for v in route[key]['vehicles'].keys():
				if route[key]['vehicles'][v]['releaseTime'] <= route[key]['timeWindow'][1]:
					outfile.write(f"{numVehicles}	{int(max([route[key]['vehicles'][v]['releaseTime'], route[key]['timeWindow'][0]]))}\n")
					numVehicles += 1
			outfile.write("\n")
			outfile.write(f"CUSTOMER\n")
			outfile.write(f"CUST NO.	DEMAND1	DEMAND2	READY TIME	DUE DATE	SERVICE TIME	PICKUP\n")
			startTyping, num = False, 0
			for j in route.keys():
				if j == key:
					startTyping = True
				if startTyping:
					for i in range(len(locations_info)):
						if locations_info[i, 0] == route[j]["location"]:
							outfile.write(f"{num}		0	0	{route[j]['timeWindow'][0]}		{route[j]['timeWindow'][1]}		0		0\n")
							listNodes.append(locations_info[i, 0])
							num += 1
					break
			for n in route[key]['pickups']:
				if locations_info[orders_info[n, 4], 0] != route[key]['location']:
					outfile.write(f"{num}		{int(100*orders_size[n, 0])}	{int(1000*orders_size[n, 1])}	{int(orders_time[n, 0])}		{int(orders_time[n, 2])}		{serviceTime}		1\n")
					listNodes.append(locations_info[orders_info[n, 4], 0])
					num += 1
			for n in route[key]['deliveries']:
				if locations_info[orders_info[n, 5], 0] != route[key]['location']:
					outfile.write(f"{num}		{int(100*orders_size[n, 0])}	{int(1000*orders_size[n, 1])}	{int(orders_time[n, 1])}		{int(orders_time[n, 2])}		{serviceTime}		0\n")
					listNodes.append(locations_info[orders_info[n, 5], 0])
					num += 1
			outfile.write("\nTRAVEL TIMES\n\n")
			selectedType = None
			for v in route[key]['vehicles'].keys():
				for t in range(len(eligibleTypes)):
					if eligibleTypes[t] == route[key]['vehicles'][v]['type']:
						selectedType = t
						break
			for i in range(len(listNodes)):
				outfile.write(f"{i}	")
				for a in range(len(locations_info)):
					if locations_info[a, 0] == listNodes[i]:
						for j in range(len(listNodes)):
							if i == j:
								outfile.write(f"{0}	")
							else:
								for b in range(len(locations_info)):
									if locations_info[b, 0] == listNodes[j]:
										outfile.write(f"{int(travelTimes[a, b, selectedType])}	")
				outfile.write("\n")
	
	if oldPlan != None:
		newFile = ""
		for char in filename:
			if char != ".":
				newFile += char
			else:
				newFile += "_previous.txt"
				break

		with open(f"./files/{newFile}", 'w') as outfile:
			for char in filename:
				if char != ".":
					outfile.write(char)
				else:
					outfile.write("\n\n")
					break
			numVehicles = 0
			for v in route[key]['vehicles'].keys():
				if route[key]['vehicles'][v]['releaseTime'] <= route[key]['timeWindow'][1]:
					sequence = f"{numVehicles}: "
					for r in oldPlan.keys():
						if r == route[key]['vehicles'][v]['id']:
							for j in oldPlan[r].keys():
								if oldPlan[r][j]['timeWindow'][0] <= route[key]['vehicles'][v]['releaseTime']:
									for i in range(len(listNodes)):
										if listNodes[i] == oldPlan[r][j]['location']:
											sequence += f"{i} "
											break
									if oldPlan[r][j]['timeWindow'][1] >= route[key]['vehicles'][v]['releaseTime']:
										break
							break
					if sequence == f"{numVehicles}: ":
						sequence += "-\n"
					else:
						sequence += "\n"
					outfile.write(sequence)
					numVehicles += 1
	return filename
