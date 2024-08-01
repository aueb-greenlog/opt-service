import pandas as pd
from datetime import *
import warnings
warnings.filterwarnings("ignore")

import opt_mcc
import opt_routing
import opt_preprocessing
import opt_event

def optimizer(event, livingLab, nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, eligibleTypes, serviceTime, canBeTransferredWith, objective, previousPlan, timeOfEvent):
	timeLimit = 180
	newOrders = []
	if event == None:
		routes, subroutes, maxOrders =  dayToDayOptimisation(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith,
					   		 								objective, eligibleTypes, serviceTime, timeLimit, livingLab)
	else:
		routes, subroutes, maxOrders, newOrders = eventTriggeredOptimisation(orders_info, orders_time, orders_size, locations_info, vehicles_info, vehicles_size, travelTimes,
							   									eligibleTypes, serviceTime, livingLab, event, previousPlan, timeOfEvent)
	
	return routes, subroutes, maxOrders, newOrders

def dayToDayOptimisation(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith,
						 objective, eligibleTypes, serviceTime, timeLimit, livingLab):
	print(datetime.now(), f" - Start of Day-to-Day Optimisation module")
	routes, subroutes, delay, maxOrders = {}, {}, 0, nOrders
	if any("mobile" in vehicles_info[v, 1] for v in range(len(vehicles_info))):
		print(datetime.now(), f" - Start of MCC Deployment.")
		warmstart = opt_mcc.formulate_mcc(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes,
										  canBeTransferredWith, "max-coveredDemand", eligibleTypes, None, None, None, None, None, None, None, nOrders, serviceTime)
		print(datetime.now(), f" - Computation of a warm-start solution.")
		warmDelivery, warmPickup, warmY, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders = opt_mcc.get_warmstart(warmstart, timeLimit, "gurobi")
		milp = opt_mcc.formulate_mcc(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes,
							   canBeTransferredWith, objective, eligibleTypes, warmDelivery, warmPickup, warmY, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders, serviceTime)
		print(datetime.now(), f" - Mobile depots scheduling.")
		routes = opt_mcc.solve_mcc(milp, timeLimit, "gurobi", locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, eligibleTypes, travelTimes)
		print(datetime.now(), f" - End of MCC Deployment.")
	else:
		routes = opt_mcc.solve_mcc(None, None, None, locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, eligibleTypes, travelTimes)
	if all(orders_info[n, 10] == 0.0 for n in range(nOrders)):
		if routes != False:
			print(datetime.now(), f" - Start of Routing.")
			for r in routes.keys():
				for stop in routes[r].keys():
					if routes[r][stop]['customers'] > 0:
						filename = fileGenerator(livingLab, stop, routes[r][stop]['customers'], routes[r], locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, None, None)
						filename, routes[r], subroutes, delay = opt_routing.solve_routing(filename, routes[r], stop, travelTimes, locations_info, orders_info, orders_time, vehicles_info, eligibleTypes, subroutes, r, [], serviceTime)
						startDelay = False
						for k in routes[r].keys():
							if k == stop:
								startDelay = True
							if startDelay == True:
								if k != stop:
									routes[r][k]['timeWindow'][0] += delay
									routes[r][k]['timeWindow'][1] += delay
			print(datetime.now(), f" - End of Routing.")
	return routes, subroutes, maxOrders

def eventTriggeredOptimisation(orders_info, orders_time, orders_size, locations_info, vehicles_info, vehicles_size, travelTimes,
							   eligibleTypes, serviceTime, livingLab, event, previousPlan, timeOfEvent):
	print(datetime.now(), f" - Start of Event-triggered Optimisation module")
	timeOfEvent = int(timeOfEvent[0])*60*10 + int(timeOfEvent[1])*60 + int(timeOfEvent[3])*10 + int(timeOfEvent[4])
	routes, subroutes, newOrders = opt_preprocessing.loadPreviousPlan(previousPlan, vehicles_info, vehicles_size, timeOfEvent, orders_info, locations_info)
	if event == "new-request":
		timeOfEvent += 5
		for n in newOrders:
			routes, subroutes = opt_event.newIntegration(n, routes, subroutes, orders_info, orders_size, locations_info, vehicles_info, vehicles_size, travelTimes, timeOfEvent, eligibleTypes, serviceTime)
	if event == "unavailable-vehicle":
		routes, orders_info, orders_time = opt_event.reSchedule(routes, subroutes, timeOfEvent, orders_info, locations_info, orders_time)
		subroutes = {}
		print(datetime.now(), f" - Start of Routing.")
		for r in routes.keys():
			for stop in routes[r].keys():
				if routes[r][stop]['customers'] > 0 and timeOfEvent <= routes[r][stop]['timeWindow'][1]:
					filename = fileGenerator(livingLab, stop, routes[r][stop]['customers'], routes[r], locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, None, None)
					filename, routes[r], subroutes, delay = opt_routing.solve_routing(filename, routes[r], stop, travelTimes, locations_info, orders_info, orders_time, vehicles_info, eligibleTypes, subroutes, r, [], serviceTime)
					startDelay = False
					for k in routes[r].keys():
						if k == stop:
							startDelay = True
						if startDelay == True:
							if k != stop:
								routes[r][k]['timeWindow'][0] += delay
								routes[r][k]['timeWindow'][1] += delay
		print(datetime.now(), f" - End of Routing.")
	return routes, subroutes, len(orders_info), newOrders

def fileGenerator(livingLab, key, nCustomers, route, locations_info, orders_info, serviceTime, orders_size, orders_time, eligibleTypes, travelTimes, oldPlan, timeOfEvent):
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
	if livingLab == "Terrassa, Spain":
		filename = f"TRS_{key}_{nCustomers}.txt"

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
		outfile.write("VEHICLE\n")
		outfile.write("NUMBER	CAPACITY1	CAPACITY2\n")
		numVehicles = 0
		for v in route[key]['vehicles'].keys():
			numVehicles += 1
		for v in route[key]['vehicles'].keys():
			cap1, cap2 = int(100*route[key]['vehicles'][v]['capacity1']), int(1000*route[key]['vehicles'][v]['capacity2'])
			break
		outfile.write(f"{numVehicles}	{cap1}		{cap2}\n\n")
		if numVehicles > 0:
			outfile.write("VEHICLE	RELEASE\n")
			numVehicles = 0
			for v in route[key]['vehicles'].keys():
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
							listNodes.append(("depot", "depot", locations_info[i, 0]))
							num += 1
					break
			for n in route[key]['pickups']:
				if locations_info[orders_info[n, 4], 0] != route[key]['location']:
					outfile.write(f"{num}		{int(100*orders_size[n, 0])}	{int(1000*orders_size[n, 1])}	{int(orders_time[n, 0])}		{int(orders_time[n, 2])}		{serviceTime}		1\n")
					listNodes.append((n, "pickup", locations_info[orders_info[n, 4], 0]))
					num += 1
			for n in route[key]['deliveries']:
				if locations_info[orders_info[n, 5], 0] != route[key]['location']:
					outfile.write(f"{num}		{int(100*orders_size[n, 0])}	{int(1000*orders_size[n, 1])}	{int(orders_time[n, 1])}		{int(orders_time[n, 2])}		{serviceTime}		0\n")
					listNodes.append((n, "delivery", locations_info[orders_info[n, 5], 0]))
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
					if locations_info[a, 0] == listNodes[i][2]:
						for j in range(len(listNodes)):
							if i == j:
								outfile.write(f"{0}	")
							else:
								for b in range(len(locations_info)):
									if locations_info[b, 0] == listNodes[j][2]:
										outfile.write(f"{int(travelTimes[a, b, selectedType])}	")
				outfile.write("\n")
	
	
	return filename