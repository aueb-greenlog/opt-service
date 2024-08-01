from datetime import *
import numpy as np
import warnings
warnings.filterwarnings("ignore")
import run

def solve_routing(filename, route, depot, travelTimes, locations_info, orders_info, orders_time, vehicles_info, eligibleTypes, subroutes, vId, usedVehicles, serviceTime):
	listNodes = []
	for i in range(len(locations_info)):
		if locations_info[i, 0] == route[depot]["location"]:
			listNodes.append(("depot", "depot", locations_info[i, 0]))
	for n in route[depot]['pickups']:
		if locations_info[orders_info[n, 4], 0] != route[depot]['location']:
			listNodes.append((n, "pickup", locations_info[orders_info[n, 4], 0]))
	for n in route[depot]['deliveries']:
		if locations_info[orders_info[n, 5], 0] != route[depot]['location']:
			listNodes.append((n, "delivery", locations_info[orders_info[n, 5], 0]))
	run.execute_vrp(filename)

	trips = getTrips(listNodes, filename, route, depot)
	timeHorizon = getEndServices(filename, trips)

	if timeHorizon > route[depot]['timeWindow'][1]:
		delay = int(timeHorizon - route[depot]['timeWindow'][1])
		route[depot]['timeWindow'][1] += delay
	else:
		delay = 0
	
	numVehicles = 0
	for v in range(len(vehicles_info)):
		if "last-mile" in vehicles_info[v, 1] and v not in usedVehicles and numVehicles < len([key for key in route[depot]['vehicles']]):
			if len(trips[str(numVehicles)]['route']) > 0:
				if "carrier" not in vehicles_info[v, 1]:
					vehicleId = ""
					for char in vehicles_info[v, 0][0]:
						if char != "*":
							vehicleId += char
						else:
							break
				else:
					vehicleId = vId
				if vehicleId not in [key for key in subroutes.keys()]:
					subroutes[vehicleId], nTrips = {}, 0
				else:
					nTrips = len([j for j in subroutes[vehicleId].keys()])
				subroutes[vehicleId][nTrips] = {"location": trips[str(numVehicles)]['route'][0][2], "pickups": [], "deliveries": [], "timeWindow": [route[depot]['timeWindow'][0], route[depot]['timeWindow'][0]], "vehicles" : {}, "customers": 0, "operator": vehicles_info[v, 6], "duplicates": [nTrips]}
				if nTrips > 0:
					for loc1 in range(len(locations_info)):
						if locations_info[loc1, 0] == subroutes[vehicleId][nTrips-1]['location']:
							break
					for loc2 in range(len(locations_info)):
						if locations_info[loc2, 0] == subroutes[vehicleId][nTrips]['location']:
							break
					for t in range(len(eligibleTypes)):
						if eligibleTypes[t] in vehicles_info[v, 1]:
							break
					if subroutes[vehicleId][nTrips]['timeWindow'][0] - travelTimes[loc1, loc2, t] > subroutes[vehicleId][nTrips-1]['timeWindow'][1]:
						subroutes[vehicleId][nTrips-1]['timeWindow'][1] = int(subroutes[vehicleId][nTrips]['timeWindow'][0] - travelTimes[loc1, loc2, t])
				timeHorizon, collection, dropoff, lastStop = route[depot]['timeWindow'][0], [], [], nTrips
				for j in range(1, len(trips[str(numVehicles)]['route'])):
					arrival, departure, pickups, deliveries = 0, 0, [], []
					for loc1 in range(len(locations_info)):
						if locations_info[loc1, 0] == trips[str(numVehicles)]['route'][j-1][2]:
							break
					for loc2 in range(len(locations_info)):
						if locations_info[loc2, 0] == trips[str(numVehicles)]['route'][j][2]:
							break
					for t in range(len(eligibleTypes)):
						if eligibleTypes[t] in vehicles_info[v, 1]:
							break
					arrival = int(timeHorizon + travelTimes[loc1, loc2, t])
					departure = int(arrival + serviceTime*int(bool(locations_info[loc2, 1] == "customer") + 5*serviceTime*int(bool(locations_info[loc2, 1] == "depot"))))
					if locations_info[loc2, 1] == "customer":
						for n in route[depot]['pickups']:
							if n == trips[str(numVehicles)]['route'][j][0] and "pickup" == trips[str(numVehicles)]['route'][j][1]:
								pickups.append(n)
								dropoff.append(n)
								if orders_time[n, 0] > arrival:
									departure = int(orders_time[n, 0] + serviceTime)
						for n in route[depot]['deliveries']:
							if n == trips[str(numVehicles)]['route'][j][0] and "delivery" == trips[str(numVehicles)]['route'][j][1]:
								deliveries.append(n)
								collection.append(n)
								if orders_time[n, 1] > arrival:
									departure = int(orders_time[n, 1] + serviceTime)
					timeHorizon = departure
					subroutes[vehicleId][nTrips+j] = {"location": trips[str(numVehicles)]['route'][j][2], "pickups": [n for n in pickups], "deliveries": [n for n in deliveries], "timeWindow": [arrival, departure], "vehicles" : {}, "customers": 0, "operator": vehicles_info[v, 6], "duplicates": [nTrips+j]}
					if locations_info[loc2, 1] == "depot" or locations_info[loc2, 1] == "hub":
						subroutes[vehicleId][lastStop]['pickups'] = [n for n in collection]
						subroutes[vehicleId][nTrips+j]['deliveries'] = [n for n in dropoff]
						collection, dropoff = [], []
						lastStop = nTrips + j
			numVehicles += 1
	return filename, route, subroutes, delay

def getTrips(listNodes, filename, route, depot):
	toPlot = ""
	for char in filename:
		if char != ".":
			toPlot += char
		else:
			toPlot += "_to_plot.txt"
			break
	with open(f"./toPlot/{toPlot}", 'r') as infile:
		trips = {}
		for v in route[depot]['vehicles'].keys():
			trips[v] = {'route': [], 'endTime': None}
		content = infile.readlines()
		for j in range(2, len(content)):
			newRoute = content[j].split(":")
			newRoute[1] = newRoute[1].strip()
			newTrip = newRoute[1].split(" ")
			if "-" not in newTrip:
				for node in newTrip:
					trips[newRoute[0]]['route'].append(listNodes[int(node)])
		infile.close()
	
	return trips

def getEndServices(filename, trips):
	endServices = ""
	for char in filename:
		if char != ".":
			endServices += char
		else:
			endServices += "_end_service.txt"
			break
	timeHorizon = 0
	with open(f"./vehicles/{endServices}", 'r') as infile:
		content = infile.readlines()
		for j in range(2, len(content)):
			newRoute = content[j].split(":")
			newRoute[1] = newRoute[1].strip()
			if "(" in newRoute[1]:
				endTime = newRoute[1].split("(")
				trips[newRoute[0]]['endTime'] = int(endTime[1].replace(")", ""))
				if trips[newRoute[0]]['endTime'] > timeHorizon:
					timeHorizon = trips[newRoute[0]]['endTime']
		infile.close()
	
	return timeHorizon

def addNewRequest(n, orders_info, routes, subroutes, vehicles_info, eligibleTypes, orders_time, locations_info, travelTimes, serviceTime):
	minDistance, incVeh, incStop = 100000, None, None
	d0, d1, d2 = minDistance, minDistance, minDistance
	for r in subroutes.keys():
		for v in range(len(vehicles_info)):
			if r in vehicles_info[v, 0][0]:
				for t in eligibleTypes:
					if t in vehicles_info[v, 1]:
						typesOfLM = eligibleTypes.index(t)
						break
				break
		for stop in subroutes[r].keys():
			if subroutes[r][stop]['timeWindow'][0] >= orders_time[n, 0]:
				if stop > 1:
					stop2 = orders_info[n, 4]
					for j in range(len(locations_info)):
						if locations_info[j, 0] == subroutes[r][stop]['location']:
							stop3 = j
						if locations_info[j, 0] == subroutes[r][stop-1]['location']:
							stop1 = j
					if minDistance > travelTimes[stop1, stop2, typesOfLM] + travelTimes[stop2, stop3, typesOfLM]:
						minDistance, incVeh, incStop = travelTimes[stop1, stop2, typesOfLM] + travelTimes[stop2, stop3, typesOfLM], r, stop
						d0, d1, d2 = travelTimes[stop1, stop3, typesOfLM], travelTimes[stop1, stop2, typesOfLM], travelTimes[stop2, stop3, typesOfLM]
	storedAt = None
	for stop in subroutes[incVeh].keys():
		if subroutes[incVeh][stop]['timeWindow'][0] > subroutes[incVeh][incStop]['timeWindow'][0]:
			subroutes[incVeh][stop]['timeWindow'][0] += int(minDistance + serviceTime - d0)
			subroutes[incVeh][stop]['timeWindow'][1] += int(minDistance + serviceTime - d0)
			if storedAt == None:
				for j in range(len(locations_info)):
					if locations_info[j, 0] == subroutes[incVeh][stop]['location'] and locations_info[j, 1] in ['depot', 'hub']:
						storedAt = subroutes[incVeh][stop]['timeWindow'][0]
						subroutes[incVeh][stop]['deliveries'].append(n)
						break
	subroutes[incVeh]["new"] = {'location': locations_info[orders_info[n, 4], 0], 'timeWindow': [int(subroutes[incVeh][incStop-1]['timeWindow'][1] + d1), int(subroutes[incVeh][incStop-1]['timeWindow'][1] + d1 + serviceTime)], 'pickups': [n], 'deliveries': [], 'vehicles': {}, 'customers': 0, 'mobile': subroutes[incVeh][incStop-1]['mobile'], 'stop': subroutes[incVeh][incStop-1]['stop']}
	
	newRoute, nTrips = {}, 0
	for t in range(24*60):
		for stop in subroutes[incVeh].keys():
			if subroutes[incVeh][stop]['timeWindow'][0] == t:
				newRoute[nTrips] = subroutes[incVeh][stop]
				nTrips += 1
				break
	subroutes[incVeh] = newRoute

	if locations_info[orders_info[n, 5], 1] != "depot":
		minDistance, incVeh, incStop = 100000, None, None
		d0, d1, d2, firstLoad = minDistance, minDistance, minDistance, None
		for r in subroutes.keys():
			for v in range(len(vehicles_info)):
				if r in vehicles_info[v, 0][0]:
					for t in eligibleTypes:
						if t in vehicles_info[v, 1]:
							typesOfLM = eligibleTypes.index(t)
							break
					break
			for stop in subroutes[r].keys():
				if firstLoad == None:
					for j in range(len(locations_info)):
						if locations_info[j, 0] == subroutes[r][stop]['location'] and locations_info[j, 1] in ['depot', 'hub'] and subroutes[r][stop]['timeWindow'][1] >= storedAt:
							firstLoad = subroutes[r][stop]['timeWindow'][1]
							subroutes[r][stop]['pickups'].append(n)
							break
				if firstLoad != None:
					if subroutes[r][stop]['timeWindow'][0] >= firstLoad:
						if stop > 1:
							stop2 = orders_info[n, 5]
							for j in range(len(locations_info)):
								if locations_info[j, 0] == subroutes[r][stop]['location']:
									stop3 = j
								if locations_info[j, 0] == subroutes[r][stop-1]['location']:
									stop1 = j
							if minDistance > travelTimes[stop1, stop2, typesOfLM] + travelTimes[stop2, stop3, typesOfLM]:
								minDistance, incVeh, incStop = travelTimes[stop1, stop2, typesOfLM] + travelTimes[stop2, stop3, typesOfLM], r, stop
								d0, d1, d2 = travelTimes[stop1, stop3, typesOfLM], travelTimes[stop1, stop2, typesOfLM], travelTimes[stop2, stop3, typesOfLM]
		for stop in subroutes[incVeh].keys():
			if subroutes[incVeh][stop]['timeWindow'][0] > subroutes[incVeh][incStop]['timeWindow'][0]:
				subroutes[incVeh][stop]['timeWindow'][0] += int(minDistance + serviceTime - d0)
				subroutes[incVeh][stop]['timeWindow'][1] += int(minDistance + serviceTime - d0)
		subroutes[incVeh]["new"] = {'location': locations_info[orders_info[n, 5], 0], 'timeWindow': [int(subroutes[incVeh][incStop-1]['timeWindow'][1] + d1), int(subroutes[incVeh][incStop-1]['timeWindow'][1] + d1 + serviceTime)], 'pickups': [], 'deliveries': [n], 'vehicles': {}, 'customers': 0, 'mobile': subroutes[incVeh][incStop-1]['mobile'], 'stop': subroutes[incVeh][incStop-1]['stop']}

		newRoute, nTrips = {}, 0
		for t in range(24*60):
			for stop in subroutes[incVeh].keys():
				if subroutes[incVeh][stop]['timeWindow'][0] == t:
					newRoute[nTrips] = subroutes[incVeh][stop]
					nTrips += 1
					break
		subroutes[incVeh] = newRoute

	for r in routes.keys():
		delay = 0
		for stop in routes[r].keys():
			routes[r][stop]['timeWindow'][0] += delay
			for k in subroutes.keys():
				for l in subroutes[k].keys():
					if r == subroutes[k][l]['mobile'] and stop == subroutes[k][l]['stop'] and subroutes[k][l]['location'] == routes[r][stop]['location']:
						for n in subroutes[k][l]['pickups']:
							if n not in routes[r][stop]['deliveries']:
								routes[r][stop]['deliveries'].append(n)
						for n in subroutes[k][l]['deliveries']:
							if n not in routes[r][stop]['pickups']:
								routes[r][stop]['pickups'].append(n)
						if subroutes[k][l]['timeWindow'][0] > routes[r][stop]['timeWindow'][1]:
							delay += subroutes[k][l]['timeWindow'][0] - routes[r][stop]['timeWindow'][1]
			routes[r][stop]['timeWindow'][1] += delay
	
	for r in subroutes.keys():
		delay = 0
		for stop in subroutes[r].keys():
			subroutes[r][stop]['timeWindow'][0] += delay
			if subroutes[r][stop]['mobile'] != None:
				if subroutes[r][stop]['location'] == routes[subroutes[r][stop]['mobile']][subroutes[r][stop]['stop']]['location']:
					if subroutes[r][stop]['timeWindow'][1] < routes[subroutes[r][stop]['mobile']][subroutes[r][stop]['stop']]['timeWindow'][0]:
						delay += routes[subroutes[r][stop]['mobile']][subroutes[r][stop]['stop']]['timeWindow'][0] - subroutes[r][stop]['timeWindow'][1]
				subroutes[r][stop]['timeWindow'][1] += delay

	return routes, subroutes

def urgentPickup(order, orders_info, orders_size, vehicles_info, vehicles_size, locations_info, subroutes, routes, serviceTime, eligibleTypes, travelTimes):
	candidateSequences = {}
	for r in subroutes.keys():
		candidateSequences[r] = {}
		for k in subroutes[r].keys():
			for j in range(len(locations_info)):
				if locations_info[j, 0] == subroutes[r][k]['location']:
					break
			candidateSequences[r][k] = subroutes[r][k]
			if locations_info[j, 1] == "hub":
				if len(candidateSequences[r].keys()) == 1:
					candidateSequences[r][k+1] = subroutes[r][k]
					candidateSequences[r][k+1]['pickups'], candidateSequences[r][k+1]['deliveries'] = [], []
				break
	incR, incS, minDistance = None, None, 10000
	for r in candidateSequences.keys():
		startRouting, load = False, []
		for v in range(len(vehicles_info)):
			if r in vehicles_info[v, 0][0]:
				break
		for t in eligibleTypes:
			if t in vehicles_info[v, 1]:
				typeOfLM = eligibleTypes.index(t)
		for k in candidateSequences[r].keys():
			availableWeight, availableVol = vehicles_size[v, 0], vehicles_size[v, 1]
			minWeight, minVol = availableWeight, availableVol
			for n in load:
				availableWeight -= orders_size[n, 0]
				availableVol -= orders_size[n, 1]
			for l in range(k, 100):
				if l > k:
					try:
						for n in candidateSequences[r][l]['pickups']:
							availableWeight -= orders_size[n, 0]
							availableVol -= orders_size[n, 1]
						for n in candidateSequences[r][l]['deliveries']:
							availableWeight += orders_size[n, 0]
							availableVol += orders_size[n, 1]
						if availableWeight < minWeight:
							minWeight = availableWeight
						if availableVol < minVol:
							minVol = availableVol
					except Exception:
						break
			if startRouting:
				if minWeight >= orders_size[order, 0] and minVol >= orders_size[order, 1]:
					for j in range(len(locations_info)):
						if locations_info[j, 0] == candidateSequences[r][k-1]['location']:
							node1 = j
						if locations_info[j, 0] == candidateSequences[r][k]['location']:
							node3 = j
					node2 = orders_info[order, 4]
					if travelTimes[node1, node2, typeOfLM] + travelTimes[node2, node3, typeOfLM] - travelTimes[node1, node3, typeOfLM] < minDistance:
						incR, incS, minDistance = r, k, travelTimes[node1, node2, typeOfLM] + travelTimes[node2, node3, typeOfLM] - travelTimes[node1, node3, typeOfLM]
						d1, d2 = travelTimes[node1, node2, typeOfLM], travelTimes[node2, node3, typeOfLM]
			else:
				startRouting = True
			for n in candidateSequences[r][k]['pickups']:
				load.append(n)
			for n in candidateSequences[r][k]['deliveries']:
				if n not in load:
					load.remove(n)
	if incR != None and incS != None:
		subroutes[incR]["newStop"] = {'location': locations_info[orders_info[order, 4], 0], 'timeWindow': [subroutes[incR][incS-1]['timeWindow'][1] + int(d1), subroutes[incR][incS-1]['timeWindow'][1] + int(d1) + serviceTime], 'pickups': [order], 'deliveries': [], 'vehicles': {}, "customers": 0, 'mobile': subroutes[incR][incS]['mobile'], 'stop': subroutes[incR][incS]['stop']}
		delay = int(subroutes[incR]["newStop"]['timeWindow'][1] + d2 - subroutes[incR][incS]['timeWindow'][0])
		subroutes[incR][incS]['timeWindow'] = [subroutes[incR]["newStop"]['timeWindow'][1] + int(d2), subroutes[incR][incS]['timeWindow'][1] + int(delay)]
		sorted_keys, sortedRoute, nTrips = [], {}, 0
		for t in range(24*60):
			for j in subroutes[incR].keys():
				if subroutes[incR][j]['timeWindow'][0] >= t and subroutes[incR][j]['timeWindow'][0] < t+1 and j not in sorted_keys:
					sorted_keys.append(j)
		for j in sorted_keys:
			sortedRoute[nTrips] = subroutes[incR][j]
			nTrips += 1
		subroutes[incR] = sortedRoute
		startDelay = False
		for k in subroutes[incR].keys():
			if startDelay:
				subroutes[incR][k]['timeWindow'][0] = int(delay + subroutes[incR][k]['timeWindow'][0])
				subroutes[incR][k]['timeWindow'][1] = int(delay + subroutes[incR][k]['timeWindow'][1])
				if subroutes[incR][k]['location'] == routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['location']:
					subroutes[incR][k]['deliveries'].append(order)
					if order not in routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['pickups']:
						routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['pickups'].append(order)
						if order in routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['deliveries']:
							routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['deliveries'].remove(order)
					if routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['timeWindow'][1] < subroutes[incR][k]['timeWindow'][1]:
						routes[subroutes[incR][incS]['mobile']][subroutes[incR][incS]['stop']]['timeWindow'][1] = subroutes[incR][k]['timeWindow'][1]
			else:
				if subroutes[incR][k]['location'] == locations_info[orders_info[order, 4], 0]:
					startDelay = True	
		if orders_info[order, 2] == 1.0:
			startCounting, minDistance, newR, newS = False, 10000, None, None
			for k in routes[subroutes[incR][incS]['mobile']].keys():
				if startCounting:
					for j in range(len(locations_info)):
						if routes[subroutes[incR][incS]['mobile']][k]['location'] == locations_info[j, 0]:
							break
					if locations_info[j, 1] != "depot":
						if travelTimes[j, orders_info[order, 5], typeOfLM] < minDistance:
							minDistance, newR, newS = travelTimes[j, orders_info[order, 5], typeOfLM], subroutes[incR][incS]['mobile'], k
				if k == subroutes[incR][incS]['stop']:
					startCounting = True
			if newR != None and newS != None:
				routes[newR][newS]['deliveries'].append(order)

	return subroutes, routes
