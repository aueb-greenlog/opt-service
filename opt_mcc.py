from __future__ import division
import math
from pyomo.environ import *
import pandas as pd
from csv import reader
import logging
logging.getLogger('pyomo.core').setLevel(logging.ERROR)
from datetime import *
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def formulate_mcc(nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes,
				  canBeTransferredWith, objective, eligibleTypes, warmDelivery, warmPickup, warmY, warmT, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders, serviceTime):
	allMobile = [k for n in range(len(vehicles_info)) for k in vehicles_info[n, 0] if 'mobile' in vehicles_info[n, 1]]
	copies = [[k for k in vehicles_info[n, 0]] for n in range(len(vehicles_info)) if 'mobile' in vehicles_info[n, 1]]

	typeOfMDH, typesOfLM = None, None
	for k in allMobile:
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				for t in eligibleTypes:
					typeOfMDH = eligibleTypes.index(t)
					break
	if any("carrier" in vehicles_info[v, 1] for v in range(len(vehicles_info))):
		typesOfLM = eligibleTypes.index("carrier")
	else:
		for v in range(len(vehicles_info)):
			if "last-mile" in vehicles_info[v, 1]:
				for t in eligibleTypes:
					typesOfLM = eligibleTypes.index(t)		
	minInterval = 5

	model = ConcreteModel()
	# Sets
	model.Orders = [n for n in range(nOrders)]
	model.Mobile = allMobile
	model.Hubs = [j for j in range(nLocations) if locations_info[j, 1] == 'hub']
	model.Depots = [j for j in range(nLocations) if locations_info[j, 1] == 'depot']
	model.Locations = [j for j in range(nLocations) if (locations_info[j, 1] == 'depot' or locations_info[j, 1] == 'hub')]
	# Variables
	model.xDelivery = Var(model.Orders, model.Locations, model.Mobile, within = Binary)
	model.xPickup = Var(model.Orders, model.Locations, model.Mobile, within = Binary)
	model.y = Var(model.Hubs, model.Mobile, within = Binary)
	model.t = Var(model.Mobile, within = Binary)
	model.l = Var(model.Locations, model.Locations, model.Mobile, within = Binary)
	def operating_hours(model, j, k):
		return (int(locations_time[j, 0]/minInterval), int((locations_time[j, 1])/minInterval))
	model.Arrival = Var(model.Locations, model.Mobile, within = NonNegativeIntegers, bounds = operating_hours)
	model.Departure = Var(model.Locations, model.Mobile, within = NonNegativeIntegers, bounds = operating_hours)
	model.Waiting = Var(model.Locations, model.Mobile, within = NonNegativeIntegers)
	try:
		if warmL != None:
			for i in model.Orders:
				for j in model.Locations:
					for k in model.Mobile:
						model.xPickup[i, j, k], model.xDelivery[i, j, k] = warmPickup[i][j][k], warmDelivery[i][j][k]
			for j in model.Hubs:
				for k in model.Mobile:
					model.y[j, k] = warmY[j][k]
			for k in model.Mobile:
				model.t[k] = warmT[k]
			for i in model.Locations:
				for j in model.Locations:
					for k in model.Mobile:
						model.l[i, j, k] = warmL[i][j][k]
			for j in model.Locations:
				for k in model.Mobile:
					model.Arrival[j, k], model.Departure[j, k], model.Waiting[j, k] = warmArrival[j][k], warmDeparture[j][k], warmWaiting[j][k]
			model.z = 100000000
	except Exception:
		pass

	for k in model.Mobile:
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				if maxOrders == nOrders:
					nTrips = max([math.ceil(sum([orders_size[i, 0] for i in model.Orders])/vehicles_size[v, 0]), math.ceil(sum([orders_size[i, 1] for i in model.Orders])/vehicles_size[v, 1]), math.ceil(sum([orders_size[i, 5] for i in model.Orders])/vehicles_size[v, 5])])
				else:
					nTrips = 0
	model.z = Var(within = NonNegativeReals)

	def obj_rule(model):
		return model.z
	if "min" in objective:
		model.obj = Objective(rule = obj_rule, sense = minimize)
	if "max" in objective:
		model.obj = Objective(rule = obj_rule, sense = maximize)

	model.constraints = ConstraintList()

	if objective == "min-travelTime": # Minimisation of total travel time
		model.constraints.add(model.z >= sum(travelTimes[i, j, typeOfMDH]*model.l[i, j, k] for i in model.Locations for j in model.Locations for k in model.Mobile) +
										sum((travelTimes[j, orders_info[i, 5], typesOfLM] + travelTimes[orders_info[i, 5], j, typesOfLM])*model.xDelivery[i, j, k] for i in model.Orders for j in model.Locations for k in model.Mobile) + 
										sum((travelTimes[j, orders_info[i, 4], typesOfLM] + travelTimes[orders_info[i, 4], j, typesOfLM])*model.xPickup[i, j, k] for i in model.Orders for j in model.Locations for k in model.Mobile))
		model.constraints.add(sum(model.xDelivery[i, j, k] for i in model.Orders for j in model.Locations for k in model.Mobile) == maxOrders) # Each order is assigned to a location from which the delivery will begin.
		model.constraints.add(sum(model.xPickup[i, j, k] for i in model.Orders for j in model.Locations for k in model.Mobile) == maxOrders) # Each order is assigned to a location from which the pickup will begin.
		model.constraints.add(sum(model.t[k] for k in model.Mobile) >= nTrips) # The weight/volume of demand indicates the minimum required number of trips.
	if objective == "max-coveredDemand": # Maximisation of covered demand
		model.constraints.add(model.z <= sum(model.xDelivery[i, j, k] + model.xPickup[i, j, k] for i in model.Orders for j in model.Locations for k in model.Mobile))
	for i in model.Orders:
		if orders_info[i, 4] not in model.Depots:
			model.constraints.add(sum(model.xPickup[i, j, k] for j in model.Depots for k in model.Mobile) == 0.0)
		if orders_info[i, 5] not in model.Depots:
			model.constraints.add(sum(model.xDelivery[i, j, k] for j in model.Depots for k in model.Mobile) == 0.0)
		model.constraints.add(sum(model.xDelivery[i, j, k] for j in model.Locations for k in model.Mobile) <= 1) # Each order is assigned to no more than one location from which the delivery will begin.
		model.constraints.add(sum(model.xPickup[i, j, k] for j in model.Locations for k in model.Mobile) <= 1) # Each order is assigned to no more than one location from which the pickup will begin.
		for k in model.Mobile:
			model.constraints.add(sum(model.xPickup[i, j, k] for j in model.Locations) == sum(model.xDelivery[i, j, k] for j in model.Locations)) # If an order is picked up, it will also be delivered.
			for j in model.Locations:
				model.constraints.add(model.xPickup[i, j, k] + model.xDelivery[i, j, k] <= 1.0)
				if eligibleTypes[typesOfLM] == "carrier" and travelTimes[j, orders_info[i, 5], typesOfLM] > 10:
					model.constraints.add(model.xDelivery[i, j, k] == 0.0)
				if j not in model.Depots:
					model.constraints.add(model.xDelivery[i, j, k] <= model.y[j, k]) #An order can be assigned for delivery to an open location.
					model.constraints.add(model.xPickup[i, j, k] <= model.y[j, k]) #An order can be assigned for pickup to an open location.
				# Constraints to respect time windows/release times
				model.constraints.add(minInterval*model.Arrival[j, k] + travelTimes[j, orders_info[i, 5], typesOfLM] - orders_time[i, 2] <= (locations_time[j, 1] + travelTimes[j, orders_info[i, 5], typesOfLM])*(1 - model.xDelivery[i, j, k]))
				if j not in model.Depots:
					model.constraints.add(minInterval*model.Waiting[j, k] >= (travelTimes[j, orders_info[i, 5], typesOfLM] + travelTimes[orders_info[i, 5], j, typesOfLM] + serviceTime)*model.xDelivery[i, j, k])
					model.constraints.add(minInterval*model.Waiting[j, k] >= (travelTimes[j, orders_info[i, 4], typesOfLM] + travelTimes[orders_info[i, 4], j, typesOfLM] + serviceTime)*model.xPickup[i, j, k])
				else:
					model.constraints.add(minInterval*model.Waiting[j, k] >= (serviceTime)*model.xPickup[i, j, k])
				model.constraints.add(orders_time[i, 1] - travelTimes[j, orders_info[i, 5], typesOfLM] - minInterval*model.Departure[j, k] <= orders_time[i, 1]*(1 - model.xDelivery[i, j, k]))
				model.constraints.add(orders_time[i, 1] + travelTimes[j, orders_info[i, 5], typesOfLM] + serviceTime + travelTimes[orders_info[i, 5], j, typesOfLM] - minInterval*model.Departure[j, k] <= (orders_time[i, 1] + travelTimes[j, orders_info[i, 5], typesOfLM] + serviceTime)*(1 - model.xDelivery[i, j, k]))
				if orders_info[i, 3] == 1:
					model.constraints.add(orders_time[i, 0] + travelTimes[orders_info[i, 4], j, typesOfLM] - minInterval*model.Departure[j, k] <= (orders_time[i, 0] + travelTimes[orders_info[i, 4], j, typesOfLM])*(1 - model.xPickup[i, j, k]))
				for l in model.Locations:
					for m in model.Mobile:
						model.constraints.add(model.Departure[l, k] - model.Arrival[j, m] <= (locations_time[l, 1])*(2 - model.xPickup[i, l, k] - model.xDelivery[i, j, m])) # Precedence constraint: The pickup location should be visited before the delivery location for all orders.
	for k in model.Mobile:
		for i in model.Orders:
			for j in model.Orders:
				if i != j and (canBeTransferredWith[i, j] == 0 or canBeTransferredWith[j, i] == 0):
					model.constraints.add(sum(model.xDelivery[i, l, k] for l in model.Locations) + sum(model.xDelivery[j, l, k] for l in model.Locations) <= 1)
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				for j in model.Locations:
					if len(model.Hubs) > 0:
						model.constraints.add(model.l[j, j, k] == 0.0) #Invalid route 'j'-->'j' is not permitted.
					if vehicles_info[v, 4] == j: # All mobile hubs will start from the current location, if used.
						model.constraints.add(sum(model.l[j, i, k] for i in model.Hubs) == model.t[k])
						model.constraints.add(sum(model.l[i, j, k] for i in model.Hubs) == model.t[k])
					if j not in model.Depots:
						# Constraints to define the sequence of locations visited by all mobile hubs, with respect to capacity.
						model.constraints.add(sum(model.l[i, j, k] for i in model.Locations) == model.y[j, k])
						model.constraints.add(sum(model.l[j, i, k] for i in model.Locations) == model.y[j, k])
						model.constraints.add(model.Departure[j, k] >= model.Arrival[j, k] + model.Waiting[j, k])
					for i in model.Locations:
						if i != j:
							model.constraints.add(minInterval*model.Departure[j, k] + travelTimes[j, i, typeOfMDH] - minInterval*model.Arrival[i, k] <= (locations_time[j, 1] + travelTimes[j, i, typeOfMDH])*(1 - model.l[j, i, k]))
							model.constraints.add(minInterval*model.Arrival[i, k] - minInterval - minInterval*model.Departure[j, k] - travelTimes[j, i, typeOfMDH] <= (locations_time[i, 1])*(1 - model.l[j, i, k]))
							if "carrier" in vehicles_info[v, 1]:
								if i in model.Hubs and j in model.Hubs:
									model.constraints.add(model.l[i, j, k] == 0.0)
				break
		for j in model.Hubs:
			model.constraints.add(model.t[k] >= model.y[j, k])
	for k in range(nMobile):
		for c in range(len(copies[k])):
			for v in range(len(vehicles_info)):
				if copies[k][c] in vehicles_info[v, 0]:
					# Capacity constraints for mobile hubs.
					model.constraints.add(sum(orders_size[i, 0]*model.xPickup[i, j, copies[k][c]] for i in model.Orders for j in model.Locations) <= vehicles_size[v, 0])
					model.constraints.add(sum(orders_size[i, 1]*model.xPickup[i, j, copies[k][c]] for i in model.Orders for j in model.Locations) <= vehicles_size[v, 1])
					model.constraints.add(sum(model.xPickup[i, j, copies[k][c]] for i in model.Orders for j in model.Locations) <= vehicles_size[v, 5])
			if c > 0:
				for j in model.Depots:
					# No overlap constraints for mobile hubs to perform multiple trips
					model.constraints.add(model.Departure[j, copies[k][c]] >= model.Arrival[j, copies[k][c-1]] + 2)
					model.constraints.add(minInterval*model.Departure[j, copies[k][c]] >= minInterval*model.Arrival[j, copies[k][c-1]] + minInterval*model.Waiting[j, copies[k][c]])

	return model

def solve_mcc(model, timelimit, solver, locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, incType, completed):
	minInterval, allOperators = 5, list(set([vehicles_info[v, 6] for v in range(len(vehicles_info)) if "last-mile" in vehicles_info[v, 1]]))
	if model != None:
		slv, slv.options['timelimit']  = SolverFactory(solver), timelimit
		try:
			results_obj = slv.solve(model, tee = False, warmstart = True)
			if results_obj.solver.termination_condition != TerminationCondition.infeasible and results_obj.solver.status != SolverStatus.unknown:
				routes, toUnload = {}, {}
				for o in allOperators:
					toUnload[o] = []
				for k in model.Mobile:
					if value(model.t[k]) > 0.9:
						for v in range(len(vehicles_info)):
							if k in vehicles_info[v, 0]:
								mdh, hasCarriers = "", bool("carrier" in vehicles_info[v, 1])
								for char in vehicles_info[v, 0][0]:
									if char != "*":
										mdh += char
									else:
										break
								break
						if mdh not in [key for key in routes.keys()]:
							routes[mdh], nTrips, reLoad = {}, 0, locations_time[int(vehicles_info[v, 4]), 0]
						else:
							nTrips = len([key for key in routes[mdh].keys()])
						if hasCarriers == False:
							for t in range(24*60):
								for i in model.Locations:
									for j in model.Locations:
										if value(model.l[i, j, k]) > 0.9 and minInterval*value(model.Departure[i, k]) >= t and minInterval*value(model.Departure[i, k]) < t+1:
											if i in model.Depots:
												startTime = reLoad
											else:
												startTime = minInterval*int(value(model.Arrival[i, k]))
											if j in model.Depots:
												reLoad = minInterval*int(value(model.Arrival[j, k]))
											duplicates = []
											for o in allOperators:
												pickups, deliveries, nCustomers = [], [], 0
												for n in model.Orders:
													if value(model.xPickup[n, i, k]) > 0.9 and orders_info[n, 8] == o:
														pickups.append(n)
														if locations_info[orders_info[n, 4], 0] != locations_info[i, 0]:
															toUnload[o].append(n)
															nCustomers += 1
													if value(model.xDelivery[n, i, k]) > 0.9 and orders_info[n, 8] == o:
														deliveries.append(n)
														if locations_info[orders_info[n, 5], 0] != locations_info[i, 0]:
															nCustomers += 1
												if len(pickups) + len(deliveries) > 0:
													duplicates.append(nTrips)
													if i in model.Depots:
														numVehicles, routes[mdh][nTrips] = 0, {"location": locations_info[i, 0], "pickups": [n for n in pickups], "deliveries": [n for n in toUnload[o]], "timeWindow": [startTime, minInterval*int(value(model.Departure[i, k]))], "vehicles" : {}, "customers": nCustomers, "operator": o, "duplicates": []}
													else:
														numVehicles, routes[mdh][nTrips] = 0, {"location": locations_info[i, 0], "pickups": [n for n in pickups], "deliveries": [n for n in deliveries], "timeWindow": [startTime, minInterval*int(value(model.Departure[i, k]))], "vehicles" : {}, "customers": nCustomers, "operator": o, "duplicates": []}
													for c in duplicates:
														routes[mdh][c]["duplicates"] = duplicates
													for v in range(len(vehicles_info)):
														if "last-mile" in vehicles_info[v, 1] and vehicles_info[v, 6] == o:
															vType = [l for l in vehicles_info[v, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
															vId = ""
															for char in vehicles_info[v, 0][0]:
																if char != "*":
																	vId += char
																else:
																	break
															routes[mdh][nTrips]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[v, 5]), "capacity1" : vehicles_size[v, 0], "capacity2" : vehicles_size[v, 1], "type": vType}
															numVehicles += 1
													nTrips += 1
						else:
							for t in range(24*60):
								for i in model.Locations:
									for j in model.Locations:
										if value(model.l[i, j, k]) > 0.9 and minInterval*value(model.Departure[i, k]) >= t and minInterval*value(model.Departure[i, k]) < t+1:
											if i in model.Depots:
												startTime = reLoad
											else:
												startTime = minInterval*int(value(model.Arrival[i, k]))
											if j in model.Depots:
												reLoad = minInterval*int(value(model.Arrival[j, k]))
											for o in allOperators:
												pickups, deliveries, duplicates, nCustomers = [], [], [], 0
												for n in model.Orders:
													if value(model.xPickup[n, i, k]) > 0.9 and orders_info[n, 8] == o:
														pickups.append(n)
														if locations_info[orders_info[n, 4], 0] != locations_info[i, 0]:
															toUnload[o].append(n)
															nCustomers += 1
													if value(model.xDelivery[n, i, k]) > 0.9 and orders_info[n, 8] == o:
														deliveries.append(n)
														if locations_info[orders_info[n, 5], 0] != locations_info[i, 0]:
															nCustomers += 1
												if len(pickups) + len(deliveries) > 0:
													duplicates.append(nTrips)
													if i in model.Depots:
														numVehicles, routes[mdh][nTrips] = 0, {"location": locations_info[i, 0], "pickups": [n for n in pickups], "deliveries": [n for n in toUnload[o]], "timeWindow": [startTime, minInterval*int(value(model.Departure[i, k]))], "vehicles" : {}, "customers": nCustomers, "operator": o, "duplicates": [nTrips]}
													else:
														numVehicles, routes[mdh][nTrips] = 0, {"location": locations_info[i, 0], "pickups": [n for n in pickups], "deliveries": [n for n in deliveries], "timeWindow": [startTime, minInterval*int(value(model.Departure[i, k]))], "vehicles" : {}, "customers": nCustomers, "operator": o, "duplicates": [nTrips]}
													for c in duplicates:
														routes[mdh][c]["duplicates"] = duplicates
													for v in range(len(vehicles_info)):
														if k in vehicles_info[v, 0][0] and vehicles_info[v, 6] == o:
															vType = "carrier"
															routes[mdh][nTrips]['vehicles']['0'] = {"id": k, "releaseTime" : int(vehicles_info[v, 5]), "capacity1" : vehicles_size[v, 0], "capacity2" : vehicles_size[v, 1], "type": vType}
													nTrips += 1
				print(datetime.now(), f" - Computation of MDH schedule completed.")
			else:
				routes = False
				print(datetime.now(), f" - Algorithm killed: Infeasible solution.")
		except Exception:
			routes = False
			print(datetime.now(), f" - Algorithm killed: Infeasible solution.")
	else:
		for o in allOperators:
			routes[f"Depot_{incType}_{o}"], numVehicles = {}, 0
			for i in range(len(locations_info)):
				if locations_info[i, 1] == "depot":
					routes[f"Depot_{incType}_{o}"][0] = {"location" : locations_info[i, 0], "pickups" : [], "deliveries" : [n for n in range(len(orders_info)) if n not in completed], "timeWindow" : [locations_time[i, 0], locations_time[i, 1]], "vehicles" : {}, 'customers' : len(orders_info), 'operator': o, "duplicates": [0]}
					for v in range(len(vehicles_info)):
						if "last-mile" in vehicles_info[v, 1] and incType in vehicles_info[v, 1] and "mobile" not in vehicles_info[v, 1] and vehicles_info[v, 6] == o:
							routes[f"Depot_{incType}_{o}"][0]["vehicles"][str(numVehicles)] = {"releaseTime" : 0, "capacity1" : vehicles_size[v, 0], "capacity2" : vehicles_size[v, 1], "type": incType}
							numVehicles += 1
					break

	return routes

def get_warmstart(model, timelimit, solver):
	try:
		slv, slv.options['timelimit']  = SolverFactory(solver), timelimit
		results_obj = slv.solve(model, tee = False)
		print(datetime.now(), f" - Warm start solution completed.")
		warmDelivery, warmPickup, obj = {}, {}, value(model.z)
		for i in model.Orders:
			warmDelivery[i], warmPickup[i] = {}, {}
			for j in model.Locations:
				warmDelivery[i][j], warmPickup[i][j] = {}, {}
				for k in model.Mobile:
					try:
						warmDelivery[i][j][k] = value(model.xDelivery[i, j, k])
					except Exception:
						warmDelivery[i][j][k] = 0.0
					try:
						warmPickup[i][j][k] = value(model.xPickup[i, j, k])
					except Exception:
						warmPickup[i][j][k] = 0.0
		warmY = {}
		for j in model.Hubs:
			warmY[j] = {}
			for k in model.Mobile:
				try:
					warmY[j][k] = value(model.y[j, k])
				except Exception:
					warmY[j][k] = 0.0
		warmT = {}
		for k in model.Mobile:
			try:
				warmT[k] = value(model.t[k])
			except Exception:
				warmT[k] = 0.0
		warmL = {}
		for i in model.Locations:
			warmL[i] = {}
			for j in model.Locations:
				warmL[i][j] = {}
				for k in model.Mobile:
					try:
						warmL[i][j][k] = value(model.l[i, j, k])
					except Exception:
						warmL[i][j][k] = 0.0
		warmArrival, warmDeparture, warmWaiting = {}, {}, {}
		for j in model.Locations:
			warmArrival[j], warmDeparture[j], warmWaiting[j] = {}, {}, {}
			for k in model.Mobile:
				try:
					warmArrival[j][k] = value(model.Arrival[j, k])
				except Exception:
					warmArrival[j][k] = 0.0
				try:
					warmDeparture[j][k] = value(model.Departure[j, k])
				except Exception:
					warmDeparture[j][k] = 0.0
				try:
					warmWaiting[j][k] = value(model.Waiting[j, k])
				except Exception:
					warmWaiting[j][k] = 0.0
		maxOrders = int(0.5*value(model.z))
	except Exception:
		print(datetime.now(), f" - Computation of warm start solution failed.")
		warmDelivery, warmPickup, warmY, warmT, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders = None, None, None, None, None, None, None, None, 0
	return warmDelivery, warmPickup, warmY, warmT, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders