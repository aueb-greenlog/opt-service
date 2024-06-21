from datetime import datetime, date, timedelta
import warnings
warnings.filterwarnings("ignore")
from datetime import *
import numpy as np
import math
import random

def extract_subroutes(previousPlan, orders_info, orders_time, orders_size, locations_info, vehicles_info, vehicles_size, timeHorizon, operators, eligibleTypes, travelTimes, event):
	routes, subroutes, completedOrders = {}, {}, []
	for r in previousPlan['routes'].keys():
		for v in range(len(vehicles_info)):
			if previousPlan['routes'][r]['vehicle'] in vehicles_info[v, 0][0]:
				vehicleId = previousPlan['routes'][r]['vehicle']
				break
		if "mobile" in vehicles_info[v, 1]:
			routes[vehicleId], nTrips, loaded = {}, 0, []
			for j in previousPlan['routes'][r]['sequence'].keys():
				duplicates = []
				arrivalTime = 60*int(previousPlan['routes'][r]['sequence'][j]['arrivalTime'][0] + previousPlan['routes'][r]['sequence'][j]['arrivalTime'][1]) + int(previousPlan['routes'][r]['sequence'][j]['arrivalTime'][3] + previousPlan['routes'][r]['sequence'][j]['arrivalTime'][4])
				departureTime = 60*int(previousPlan['routes'][r]['sequence'][j]['departureTime'][0] + previousPlan['routes'][r]['sequence'][j]['departureTime'][1]) + int(previousPlan['routes'][r]['sequence'][j]['departureTime'][3] + previousPlan['routes'][r]['sequence'][j]['departureTime'][4])
				for i in range(len(locations_info)):
					if str(locations_info[i, 0]) == str(previousPlan['routes'][r]['sequence'][j]['location']):
						locationId = i
						break
				if locations_info[locationId, 1] == "depot":
					for o in operators:
						routes[vehicleId][nTrips] = {"location" : locations_info[locationId, 0], "pickups" : [], "deliveries" : [], "timeWindow" : [arrivalTime, departureTime], "vehicles" : {}, "customers": 0, "operator": o, "duplicates": []}
						for n in previousPlan['routes'][r]['sequence'][j]['associatedOrders']:
							for m in range(len(orders_info)):
								if orders_info[m, 9] == n:
									break
							if orders_info[m, 8] == o:
								if orders_info[m, 4] == locationId:
									routes[vehicleId][nTrips]['pickups'].append(m)
									loaded.append(m)
								if orders_info[m, 5] == locationId:
									routes[vehicleId][nTrips]['deliveries'].append(m)
						duplicates.append(nTrips)
						nTrips += 1
					for c in duplicates:
						routes[vehicleId][c]['duplicates'] = [k for k in duplicates]
				if locations_info[locationId, 1] == "hub":
					for o in operators:
						routes[vehicleId][nTrips] = {"location" : locations_info[locationId, 0], "pickups" : [], "deliveries" : [], "timeWindow" : [arrivalTime, departureTime], "vehicles" : {}, "customers": 0, "operator": o, "duplicates": []}
						for n in previousPlan['routes'][r]['sequence'][j]['associatedOrders']:
							for m in range(len(orders_info)):
								if orders_info[m, 9] == n:
									break
							if orders_info[m, 8] == o:
								if m in loaded:
									routes[vehicleId][nTrips]['deliveries'].append(m)
									routes[vehicleId][nTrips]['customers'] += 1
									loaded.remove(m)
									if orders_info[m, 2] == 1:
										completedOrders.append(m)
								else:
									routes[vehicleId][nTrips]['pickups'].append(m)
									loaded.append(m)
									routes[vehicleId][nTrips]['customers'] += 1
									if orders_info[m, 3] == 1 and orders_info[m, 2] == 0:
										completedOrders.append(m)
						numVehicles = 0
						for v in range(len(vehicles_info)):
							if "last-mile" in vehicles_info[v, 1] and vehicles_info[v, 6] == o:
								if "scooter" in vehicles_info[v, 1]:			
									for t in range(len(eligibleTypes)):
										if eligibleTypes[t] == "scooter":
											break
								if "bike" in vehicles_info[v, 1]:			
									for t in range(len(eligibleTypes)):
										if eligibleTypes[t] == "bike":
											break
								if "droid" in vehicles_info[v, 1]:			
									for t in range(len(eligibleTypes)):
										if eligibleTypes[t] == "droid":
											break
								vId = ""
								for char in vehicles_info[v, 0][0]:
									if char != "*":
										vId += char
									else:
										break
								routes[vehicleId][nTrips]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[v, 5]), "capacity1" : vehicles_size[v, 0], "capacity2" : vehicles_size[v, 1], "type": eligibleTypes[t]}
								numVehicles += 1
						duplicates.append(nTrips)
						nTrips += 1
					for c in duplicates:
						routes[vehicleId][c]['duplicates'] = [k for k in duplicates]
	
	for r in previousPlan['routes'].keys():
		for v in range(len(vehicles_info)):
			if previousPlan['routes'][r]['vehicle'] in vehicles_info[v, 0][0]:
				vehicleId = previousPlan['routes'][r]['vehicle']
				break
		if "last-mile" in vehicles_info[v, 1]:
			subroutes[vehicleId], nTrips, loaded = {}, 0, []
			for j in previousPlan['routes'][r]['sequence'].keys():
				arrivalTime = 60*int(previousPlan['routes'][r]['sequence'][j]['arrivalTime'][0] + previousPlan['routes'][r]['sequence'][j]['arrivalTime'][1]) + int(previousPlan['routes'][r]['sequence'][j]['arrivalTime'][3] + previousPlan['routes'][r]['sequence'][j]['arrivalTime'][4])
				departureTime = 60*int(previousPlan['routes'][r]['sequence'][j]['departureTime'][0] + previousPlan['routes'][r]['sequence'][j]['departureTime'][1]) + int(previousPlan['routes'][r]['sequence'][j]['departureTime'][3] + previousPlan['routes'][r]['sequence'][j]['departureTime'][4])
				for i in range(len(locations_info)):
					if locations_info[i, 0] == previousPlan['routes'][r]['sequence'][j]['location']:
						locationId = i
						break
				if locations_info[locationId, 1] == "depot" or locations_info[locationId, 1] == "hub":
					subroutes[vehicleId][nTrips] = {"location" : locations_info[locationId, 0], "pickups" : [], "deliveries" : [], "timeWindow" : [arrivalTime, departureTime], "vehicles" : {}, "customers": 0, "operator": o, "duplicates": [nTrips]}
					for k in routes.keys():
						for l in routes[k].keys():
							if routes[k][l]['location'] == locations_info[locationId, 0]:
								for n in routes[k][l]['pickups']:
									if n in loaded:
										loaded.remove(n)
								for n in routes[k][l]['deliveries']:
									loaded.append(n)
				if locations_info[locationId, 1] == "customer":
					subroutes[vehicleId][nTrips] = {"location" : locations_info[locationId, 0], "pickups" : [], "deliveries" : [], "timeWindow" : [arrivalTime, departureTime], "vehicles" : {}, "customers": 0, "operator": o, "duplicates": [nTrips]}
					for n in previousPlan['routes'][r]['sequence'][j]['associatedOrders']:
						for m in range(len(orders_info)):
							if orders_info[m, 9] == n:
								break
						if orders_info[m, 5] == locationId:
							subroutes[vehicleId][nTrips]['deliveries'].append(m)
							subroutes[vehicleId][nTrips]['customers'] += 1
							if m in loaded:
								loaded.remove(m)
							if orders_info[m, 2] == 1:
								completedOrders.append(m)
						if orders_info[m, 4] == locationId:
							subroutes[vehicleId][nTrips]['pickups'].append(m)
							loaded.append(m)
							subroutes[vehicleId][nTrips]['customers'] += 1
							if orders_info[m, 3] == 1 and orders_info[m, 2] == 0:
								completedOrders.append(m)
				nTrips += 1

	if event == "new-request":
		newOrders = []
		for n in range(len(orders_info)):
			if n not in completedOrders:
				newOrders.append(n)
		sortedOrders = [n for _,n in sorted(zip([orders_time[m, 0] for m in newOrders], newOrders))]
		newOrders = [n for n in sortedOrders]
		for n in newOrders:
			minDistance, incAssignment = 100000, None
			for r in routes.keys():
				for j in routes[r].keys():
					if timeHorizon <= routes[r][j]['timeWindow'][1] and orders_time[n, 0] <= routes[r][j]['timeWindow'][1] and j != [key for key in routes[r].keys()][len([key for key in routes[r].keys()])-1]:
						for loc in range(len(locations_info)):
							if locations_info[loc, 0] == routes[r][j]['location']:
								break
						for v in range(len(vehicles_info)):
							if r in vehicles_info[v, 0][0]:
								break
						if sum([orders_size[m, 0] for m in routes[r][j]['pickups']]) + orders_size[n, 0] <= vehicles_size[v, 0] and sum([orders_size[m, 1] for m in routes[r][j]['pickups']]) + orders_size[n, 1] <= vehicles_size[v, 1]:
							if "scooter" in vehicles_info[v, 1]:			
								for t in range(len(eligibleTypes)):
									if eligibleTypes[t] == "scooter":
										break
							if "bike" in vehicles_info[v, 1]:			
								for t in range(len(eligibleTypes)):
									if eligibleTypes[t] == "bike":
										break
							if travelTimes[loc, orders_info[n, 4], t] < minDistance and travelTimes[loc, orders_info[n, 4], t] + travelTimes[orders_info[n, 4], loc, t] + 3 <= routes[r][j]['timeWindow'][1] - max([routes[r][j]['timeWindow'][0], timeHorizon]) + 15:
								minDistance, incAssignment = travelTimes[loc, orders_info[n, 4], t], (r, j)
			if incAssignment != None:	
				if locations_info[orders_info[n, 5], 1] != "depot":
					minDistance, newAssignment, r = 100000, None, incAssignment[0]
					for j in routes[r].keys():
						if routes[incAssignment[0]][incAssignment[1]]['timeWindow'][1] < routes[r][j]['timeWindow'][0]:
							for loc in range(len(locations_info)):
								if locations_info[loc, 0] == routes[r][j]['location']:
									break
							for v in range(len(vehicles_info)):
								if r in vehicles_info[v, 0][0]:
									break
							if sum([orders_size[m, 0] for m in routes[r][j]['pickups']]) + orders_size[n, 0] <= vehicles_size[v, 0] and sum([orders_size[m, 1] for m in routes[r][j]['pickups']]) + orders_size[n, 1] <= vehicles_size[v, 1]:
								if "scooter" in vehicles_info[v, 1]:			
									for t in range(len(eligibleTypes)):
										if eligibleTypes[t] == "scooter":
											break
								if "bike" in vehicles_info[v, 1]:			
									for t in range(len(eligibleTypes)):
										if eligibleTypes[t] == "bike":
											break
								if travelTimes[loc, orders_info[n, 5], t] < minDistance and travelTimes[loc, orders_info[n, 5], t] + travelTimes[orders_info[n, 5], loc, t] + 3 <= routes[r][j]['timeWindow'][1] - max([routes[r][j]['timeWindow'][0], timeHorizon]) + 15:
									minDistance, newAssignment = travelTimes[loc, orders_info[n, 5], t], (r, j)
				if newAssignment != None:
					routes[incAssignment[0]][incAssignment[1]]['pickups'].append(n)
					routes[newAssignment[0]][newAssignment[1]]['deliveries'].append(n)
	if event == "unavailable-vehicle":
		newOrders = []
		for r in routes.keys():
			for j in routes[r].keys():
				for v in routes[r][j]['vehicles'].keys():
					key = routes[r][j]['vehicles'][v]['id']
					if key in subroutes.keys():
						for i in subroutes[key].keys():
							if subroutes[key][i]['timeWindow'][1] < timeHorizon:
								for n in subroutes[key][i]['deliveries']:
									for k in routes[r].keys():
										if n in routes[r][k]['deliveries']:
											routes[r][k]['deliveries'].remove(n)
							else:
								if subroutes[key][i]['timeWindow'][0] < timeHorizon:
									for n in subroutes[key][i]['deliveries']:
										for k in routes[r].keys():
											if n in routes[r][k]['deliveries']:
												routes[r][k]['deliveries'].remove(n)
								if routes[r][j]['vehicles'][v]['releaseTime'] < routes[r][j]['timeWindow'][1]:
									lastReload = None
									for loc in range(len(locations_info)):
										if locations_info[loc, 0] == subroutes[key][i]['location']:
											break
									if locations_info[loc, 1] != "hub":
										for n in subroutes[key][i]['deliveries']:
											for k in routes[r].keys():
												if n in routes[r][k]['deliveries']:
													routes[r][k]['deliveries'].remove(n)
									else:
										routes[r][j]['vehicles'][v]['releaseTime'] = subroutes[key][i]['timeWindow'][0]
										break

								
				
	return routes, subroutes, newOrders