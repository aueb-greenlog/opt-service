from __future__ import division
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
				  canBeTransferredWith, objective, eligibleTypes, warmDelivery, warmPickup, warmY, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders, serviceTime):
	allMobile = [k for n in range(len(vehicles_info)) for k in vehicles_info[n, 0] if 'mobile' in vehicles_info[n, 1]]
	copies = [[k for k in vehicles_info[n, 0]] for n in range(len(vehicles_info)) if 'mobile' in vehicles_info[n, 1]]

	typeOfMDH, typesOfLM = None, None
	for k in allMobile:
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				for t in eligibleTypes:
					if t in vehicles_info[v, 1]:
						typeOfMDH = eligibleTypes.index(t)
						break
	if any("carrier" in vehicles_info[v, 1] for v in range(len(vehicles_info))):
		typesOfLM = eligibleTypes.index("carrier")
	else:
		for v in range(len(vehicles_info)):
			if "last-mile" in vehicles_info[v, 1]:
				for t in eligibleTypes:
					if t in vehicles_info[v, 1]:
						typesOfLM = eligibleTypes.index(t)
	numLm = len([v for v in range(len(vehicles_info)) if "last-mile" in vehicles_info[v, 1]])

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
	model.y = Var(model.Locations, model.Mobile, within = Binary)
	model.t = Var(model.Mobile, within = Binary)
	model.l = Var(model.Locations, model.Locations, model.Mobile, within = Binary)
	def operating_hours(model, j, k):
		return int(locations_time[j, 0]), int((locations_time[j, 1]))
	model.Arrival = Var(model.Locations, model.Mobile, within = NonNegativeIntegers, bounds = operating_hours)
	model.Departure = Var(model.Locations, model.Mobile, within = NonNegativeIntegers, bounds = operating_hours)
	model.Waiting = Var(model.Locations, model.Mobile, within = NonNegativeIntegers)
	def capacitated(model, j, k):
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				break
		return (0, 0.9*vehicles_size[v, 0])
	model.Weight = Var(model.Locations, model.Mobile, within = NonNegativeReals, bounds = capacitated)
	def capacitated(model, j, k):
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				break
		return (0, 0.9*vehicles_size[v, 1])
	model.Volume = Var(model.Locations, model.Mobile, within = NonNegativeReals, bounds = capacitated)
	model.Loaded = Var(model.Orders, within = NonNegativeIntegers)
	model.Released = Var(model.Orders, within = NonNegativeIntegers)

	model.z = Var(within = NonNegativeReals)

	try:
		if warmL != None:
			for i in model.Orders:
				for j in model.Locations:
					for k in model.Mobile:
						model.xPickup[i, j, k], model.xDelivery[i, j, k] = warmPickup[i][j][k], warmDelivery[i][j][k]
			for j in model.Locations:
				for k in model.Mobile:
					model.y[j, k] = warmY[j][k]
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

	def obj_rule(model):
		return model.z
	if "min" in objective:
		model.obj = Objective(rule = obj_rule, sense = minimize)
	if "max" in objective:
		model.obj = Objective(rule = obj_rule, sense = maximize)

	model.constraints = ConstraintList()

	if "min" in objective:
		model.constraints.add(model.z >= sum((travelTimes[orders_info[n, 4], j, typesOfLM] + travelTimes[j, orders_info[n, 4], typesOfLM])*model.xPickup[n, j, k] for j in model.Locations for k in model.Mobile for n in model.Orders) + 
						sum((travelTimes[orders_info[n, 5], j, typesOfLM] + travelTimes[j, orders_info[n, 5], typesOfLM])*model.xDelivery[n, j, k] for j in model.Locations for k in model.Mobile for n in model.Orders) + 
						sum(travelTimes[i, j, typeOfMDH]*numLm*model.l[i, j, k] for i in model.Locations for j in model.Locations for k in model.Mobile))
	else:
		model.constraints.add(model.z <= sum(model.xPickup[n, j, k] + model.xDelivery[n, j, k] for n in model.Orders for j in model.Locations for k in model.Mobile))

	# All orders are picked-up and delivered to exactly one stop.
	if "min" in objective:
		model.constraints.add(sum(model.xPickup[n, j, k] + model.xDelivery[n, j, k] for n in model.Orders for j in model.Locations for k in model.Mobile) == 2*maxOrders)
	for n in model.Orders:
		model.constraints.add(model.Loaded[n] <= model.Released[n])
		if orders_info[n, 4] in model.Depots:
			model.constraints.add(sum(model.xPickup[n, j, k] for k in model.Mobile for j in model.Locations if j != orders_info[n, 4]) == 0.0)
		if orders_info[n, 5] in model.Depots:
			model.constraints.add(sum(model.xDelivery[n, j, k] for k in model.Mobile for j in model.Locations if j != orders_info[n, 5]) == 0.0)
		if orders_info[n, 10] == 1.0:
			for j in model.Depots:
				for k in model.Mobile:
					model.constraints.add(model.xDelivery[n, j, k] == 0.0)
		model.constraints.add(sum(model.xPickup[n, j, k] for j in model.Locations for k in model.Mobile) <= 1.0)
		model.constraints.add(sum(model.xDelivery[n, j, k] for j in model.Locations for k in model.Mobile) <= 1.0)
		# The mobile depot will visit any assigned stop.
		for k in model.Mobile:
			model.constraints.add(sum(model.xPickup[n, j, k] for j in model.Locations) == sum(model.xDelivery[n, j, k] for j in model.Locations))
			for j in model.Locations:
				model.constraints.add(model.y[j, k] >= model.xPickup[n, j, k])
				model.constraints.add(model.y[j, k] >= model.xDelivery[n, j, k])
				#if eligibleTypes[typesOfLM] == "carrier" and travelTimes[j, orders_info[n, 5], typesOfLM] > 10:
				#	model.constraints.add(model.xDelivery[n, j, k] == 0.0)
	
	# Route assigned vehicles
	for k in model.Mobile:
		for j in model.Hubs:
			for v in range(len(vehicles_info)):
				if k in vehicles_info[v, 0]:
					model.constraints.add(model.y[vehicles_info[v, 4], k] >= model.y[j, k])
					break
			#if "carrier" in vehicles_info[v, 1]:
			#	for i in model.Hubs:
			#		model.constraints.add(model.l[i, j, k] == 0.0)
		for j in model.Locations:
			model.constraints.add(sum(model.l[i, j, k] for i in model.Locations if i != j) == model.y[j, k])
			model.constraints.add(sum(model.l[j, i, k] for i in model.Locations if i != j) == model.y[j, k])
	
	# Scheduling constraints
	for k in model.Mobile:
		for i in model.Hubs:
			model.constraints.add(model.Departure[i, k] == model.Arrival[i, k] + model.Waiting[i, k])
			for j in model.Locations:
				model.constraints.add(model.Weight[i, k] + sum(orders_size[n, 0]*model.xPickup[n, i, k] for n in model.Orders) + sum(orders_size[n, 0]*model.xPickup[n, j, k] for n in model.Orders) - sum(orders_size[n, 0]*model.xDelivery[n, i, k] for n in model.Orders) - model.Weight[j, k] <= 2000*(1 - model.l[i, j, k]))
				model.constraints.add(model.Volume[i, k] + sum(orders_size[n, 1]*model.xPickup[n, i, k] for n in model.Orders) + sum(orders_size[n, 1]*model.xPickup[n, j, k] for n in model.Orders) - sum(orders_size[n, 1]*model.xDelivery[n, i, k] for n in model.Orders) - model.Weight[j, k] <= 2000*(1 - model.l[i, j, k]))
				model.constraints.add(model.Departure[i, k] + travelTimes[i, j, typeOfMDH] - model.Arrival[j, k] <= 24*60*(1 - model.l[i, j, k]))
				model.constraints.add(- model.Departure[i, k] - travelTimes[i, j, typeOfMDH] + model.Arrival[j, k] <= 24*60*(1 - model.l[i, j, k]))
		for i in model.Depots:
			model.constraints.add(model.Weight[i, k] >= sum(orders_size[n, 0]*model.xPickup[n, i, k] for n in model.Orders))
			model.constraints.add(model.Volume[i, k] >= sum(orders_size[n, 1]*model.xPickup[n, i, k] for n in model.Orders))
			for j in model.Locations:
				model.constraints.add(model.Arrival[j, k] - model.Departure[i, k] - travelTimes[i, j, typeOfMDH] <= 24*60*(1 - model.l[i, j, k]))
				model.constraints.add(- model.Arrival[j, k] + model.Departure[i, k] + travelTimes[i, j, typeOfMDH] <= 24*60*(1 - model.l[i, j, k]))
		
		for j in model.Locations:
			for n in model.Orders:
				model.constraints.add(model.Waiting[j, k] >= (travelTimes[orders_info[n, 4], j, typesOfLM] + travelTimes[j, orders_info[n, 4], typesOfLM] + serviceTime)*model.xPickup[n, j, k] + int(bool(locations_info[j, 1] != "depot"))*sum(serviceTime*(model.xPickup[i, j, k] + model.xDelivery[i, j, k]) for i in model.Orders))
				model.constraints.add(model.Departure[j, k] >= (travelTimes[orders_info[n, 4], j, typesOfLM] + orders_time[n, 0])*model.xPickup[n, j, k])
				# model.constraints.add(orders_time[n, 0] - travelTimes[j, orders_info[n, 4], typesOfLM] - model.Arrival[j, k] <= 24*60*(1 - model.xPickup[n, j, k]))
				model.constraints.add(model.Waiting[j, k] >= (travelTimes[orders_info[n, 5], j, typesOfLM] + travelTimes[j, orders_info[n, 5], typesOfLM] + serviceTime)*model.xDelivery[n, j, k] + int(bool(locations_info[j, 1] != "depot"))*sum(serviceTime*(model.xPickup[i, j, k] + model.xDelivery[i, j, k]) for i in model.Orders))
				model.constraints.add(model.Departure[j, k] >= (travelTimes[orders_info[n, 5], j, typesOfLM] + orders_time[n, 1])*model.xDelivery[n, j, k])
				#model.constraints.add(orders_time[n, 1] - travelTimes[j, orders_info[n, 5], typesOfLM] - model.Arrival[j, k] <= 24*60*(1 - model.xDelivery[n, j, k]))
				model.constraints.add(model.Arrival[j, k] + travelTimes[orders_info[n, 5], j, typesOfLM] - orders_time[n, 2] <= 24*60*(1 - model.xDelivery[n, j, k]))
				#model.constraints.add(model.Departure[j, k] + travelTimes[orders_info[n, 5], j, typesOfLM] - orders_time[n, 2] <= 24*60*(1 - model.xDelivery[n, j, k]))
				model.constraints.add(model.Departure[j, k] - model.Loaded[n] <= 24*60*(1 - model.xPickup[n, j, k]))
				model.constraints.add(- model.Departure[j, k] + model.Loaded[n] <= 24*60*(1 - model.xPickup[n, j, k]))
				model.constraints.add(model.Arrival[j, k] - model.Released[n] <= 24*60*(1 - model.xDelivery[n, j, k]))
				model.constraints.add(- model.Arrival[j, k] + model.Released[n] <= 24*60*(1 - model.xDelivery[n, j, k]))
		
		for v in range(len(vehicles_info)):
			if k in vehicles_info[v, 0]:
				break
	
	for k in range(nMobile):
		for c in range(len(copies[k])):
			for v in range(len(vehicles_info)):
				if copies[k][c] in vehicles_info[v, 0]:
					break
			if c > 0:
				model.constraints.add(model.Departure[vehicles_info[v, 4], copies[k][c]] >= model.Arrival[vehicles_info[v, 4], copies[k][c-1]] + sum(model.xDelivery[n, j, copies[k][c-1]] for n in model.Orders) + sum(model.xPickup[n, j, copies[k][c]] for n in model.Orders))
				
	return model

def solve_mcc(model, timelimit, solver, locations_info, locations_time, routes, orders_info, vehicles_info, vehicles_size, eligibleTypes, travelTimes):
	if model != None:
		slv, slv.options['timelimit']  = SolverFactory(solver), timelimit
		try:
			results_obj = slv.solve(model, tee = False, warmstart = True)

			if results_obj.solver.termination_condition != TerminationCondition.infeasible and results_obj.solver.status != SolverStatus.unknown:
				routes = {}
				for k in model.Mobile:
					for v in range(len(vehicles_info)):
						if k in vehicles_info[v, 0]:
							break
					if value(model.y[vehicles_info[v, 4], k]) > 0.9:
						mdh, hasCarriers = "", bool("carrier" in vehicles_info[v, 1])
						for char in vehicles_info[v, 0][0]:
							if char != "*":
								mdh += char
							else:
								break
						if mdh not in [key for key in routes.keys()]:
							routes[mdh], nTrips, lastLoad, arrivalTime = {}, 0, [], locations_time[vehicles_info[v, 4], 0]
						else:
							nTrips = len([key for key in routes[mdh].keys()])-1 
							lastLoad = [n for n in routes[mdh][nTrips]['deliveries']]
						
						startNode, nextNode = vehicles_info[v, 4], None
						routes[mdh][nTrips] = {"location": locations_info[startNode, 0], "pickups": [n for n in model.Orders if value(model.xPickup[n, startNode, k]) > 0.9], "deliveries": [n for n in lastLoad], "timeWindow": [arrivalTime, int(value(model.Departure[startNode, k]))], "vehicles" : {}, "customers": 0}
						nTrips += 1
						while(nextNode != vehicles_info[v, 4]):
							for j in model.Locations:
								if value(model.l[startNode, j, k]) > 0.9:
									pickups, deliveries, nCustomers = [], [], 0
									if j != vehicles_info[v, 4]:
										for n in model.Orders:
											if value(model.xPickup[n, j, k]) > 0.9:
												pickups.append(n)
												if j != orders_info[n, 4]:
													nCustomers += 1
											if value(model.xDelivery[n, j, k]) > 0.9:
												deliveries.append(n)
												if j != orders_info[n, 5]:
													nCustomers += 1
										if len(pickups) + len(deliveries) > 0:
											numVehicles, routes[mdh][nTrips] = 0, {"location": locations_info[j, 0], "pickups": [n for n in pickups], "deliveries": [n for n in deliveries], "timeWindow": [int(value(model.Arrival[j, k])), int(value(model.Departure[j, k]))], "vehicles" : {}, "customers": nCustomers}
											if hasCarriers == False:
												for p in range(len(vehicles_info)):
													if "last-mile" in vehicles_info[p, 1]:
														vType = [l for l in vehicles_info[p, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
														vId = ""
														for char in vehicles_info[p, 0][0]:
															if char != "*":
																vId += char
															else:
																break
														routes[mdh][nTrips]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
														numVehicles += 1
											else:
												for p in range(len(vehicles_info)):
													if k in vehicles_info[p, 0][0]:
														vType = "carrier"
														routes[mdh][nTrips]['vehicles']['0'] = {"id": k, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
											nTrips += 1
									nextNode = j
									startNode = nextNode
									if nextNode == vehicles_info[v, 4]:
										routes[mdh][nTrips] = {"location": locations_info[nextNode, 0], "pickups": [], "deliveries": [n for n in model.Orders if value(model.xDelivery[n, nextNode, k]) > 0.9], "timeWindow": [int(value(model.Arrival[nextNode, k])), int(value(model.Arrival[nextNode, k]))+60], "vehicles" : {}, "customers": 0}
										for n in routes[mdh][nTrips]['deliveries']:
											if orders_info[n, 5] != nextNode:
												routes[mdh][nTrips]['customers'] += 1
										for n in routes[mdh][nTrips]['pickups']:
											if orders_info[n, 4] != nextNode:
												routes[mdh][nTrips]['customers'] += 1
										arrivalTime = int(value(model.Arrival[nextNode, k]))
										if routes[mdh][nTrips]['customers'] > 0:
											numVehicles = 0
											if hasCarriers == False:
												for p in range(len(vehicles_info)):
													if "last-mile" in vehicles_info[p, 1]:
														vType = [l for l in vehicles_info[p, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
														vId = ""
														for char in vehicles_info[p, 0][0]:
															if char != "*":
																vId += char
															else:
																break
														routes[mdh][nTrips]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
														numVehicles += 1
											else:
												for p in range(len(vehicles_info)):
													if k in vehicles_info[p, 0][0]:
														vType = "carrier"
														routes[mdh][nTrips]['vehicles']['0'] = {"id": k, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
										nTrips += 1
									break
				print(datetime.now(), f" - Computation of MDH schedule completed.")
			else:
				routes = False
				print(datetime.now(), f" - Algorithm killed: Infeasible solution.")
		except Exception:
			routes = False
			print(datetime.now(), f" - Algorithm killed: Infeasible solution.")
	else:
		routes = {}
		for j in range(len(locations_info)):
			if locations_info[j, 1] == "depot":
				routes['depot'] = {}
				routes['depot'][0] = {'location': locations_info[j, 0], "pickups": [n for n in range(len(orders_info)) if orders_info[n, 3] == 1], "deliveries": [n for n in range(len(orders_info)) if orders_info[n, 2] == 1]}
				routes['depot'][0]['timeWindow'] = [locations_time[j, 0], locations_time[j, 1]]
				routes['depot'][0]['vehicles'] = {}
				routes['depot'][0]['customers'] = len(orders_info)
				numVehicles = 0
				for v in range(len(vehicles_info)):
					if "last-mile" in vehicles_info[v, 1]:
						vType = [l for l in vehicles_info[v, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
						vId = ""
						for char in vehicles_info[v, 0][0]:
							if char != "*":
								vId += char
							else:
								break
						routes['depot'][0]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[v, 5]), "capacity1" : vehicles_size[v, 0], "capacity2" : vehicles_size[v, 1], "type": vType}
						numVehicles += 1
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
		for j in model.Locations:
			warmY[j] = {}
			for k in model.Mobile:
				try:
					warmY[j][k] = value(model.y[j, k])
				except Exception:
					warmY[j][k] = 0.0
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
		warmDelivery, warmPickup, warmY, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders = None, None, None, None, None, None, None, None, 0
	return warmDelivery, warmPickup, warmY, warmL, warmArrival, warmDeparture, warmWaiting, maxOrders