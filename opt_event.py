import pandas as pd
from datetime import *
import warnings
warnings.filterwarnings("ignore")

def newIntegration(order, routes, subroutes, orders_info, orders_size, locations_info, vehicles_info, vehicles_size, travelTimes, timeOfEvent, eligibleTypes, serviceTime):
	minTime, assignedVehicle, assignedStop = 10000, None, None
	for r in subroutes.keys():
		for v in range(len(vehicles_info)):
			if r in vehicles_info[v, 0][0]:
				break
		for t in eligibleTypes:
			if t in vehicles_info[v, 1]:
				typesOfLM = eligibleTypes.index(t)
		for k in subroutes[r].keys():
			if subroutes[r][k]['timeWindow'][0] >= timeOfEvent and k > 0:
				totalWeight, totalVol = 0, 0
				for j in range(len(locations_info)):
					if locations_info[j, 0] == subroutes[r][k-1]['location']:
						node1 = j
					if locations_info[j, 0] == subroutes[r][k]['location']:
						node3 = j
				node2 = orders_info[order, 4]
				test1, test2 = True, True
				for l in range(k+1, len(subroutes[r].keys())-1):
					for n in subroutes[r][l]['deliveries']:
						totalWeight += orders_size[n, 0]
						totalVol += orders_size[n, 1]
					for i in range(len(locations_info)):
						if locations_info[i, 0] == subroutes[r][l]['location']:
							break
					if totalWeight > vehicles_size[v, 0] + orders_size[order, 0] or totalVol > vehicles_size[v, 1] + orders_size[order, 1]:
						test1 = False
					if locations_info[i, 1] == "hub":
						newWeight, newVol = 0, 0
						for m in routes.keys():
							if m != "depot":
								for p in routes[m].keys():
									if routes[m][p]['location'] == locations_info[i, 0] and routes[m][p]['timeWindow'][1] >= subroutes[r][l]['timeWindow'][0]:
										for n in routes[m][p]['deliveries']:
											newWeight += orders_size[n, 0]
											newVol += orders_size[n, 1]
										for o in range(len(locations_info)):
											if locations_info[o, 0] == routes[m][p]['location']:
												break
										if locations_info[o, 1] == "depot":
											break
								for u in range(len(vehicles_info)):
									if m in vehicles_info[u, 0][0]:
										break
								if newWeight > vehicles_size[u, 0] + orders_size[order, 0] or newVol > vehicles_size[u, 1] + orders_size[order, 1]:
									test2 = False
						break
				if test1 == True and test2 == True:
					if travelTimes[node1, node2, typesOfLM] + travelTimes[node2, node3, typesOfLM] - travelTimes[node1, node3, typesOfLM] < minTime:
						minTime = travelTimes[node1, node2, typesOfLM] + travelTimes[node2, node3, typesOfLM] - travelTimes[node1, node3, typesOfLM]
						assignedVehicle, assignedStop = r, k
	if assignedVehicle != None and assignedStop != None:
		for j in range(len(locations_info)):
			if locations_info[j, 0] == subroutes[assignedVehicle][assignedStop-1]['location']:
				node1 = j
			if locations_info[j, 0] == subroutes[assignedVehicle][assignedStop]['location']:
				node3 = j
		node2 = orders_info[order, 4]
		delay = int(travelTimes[node2, node3, typesOfLM] + travelTimes[node1, node2, typesOfLM] - travelTimes[node1, node3, typesOfLM] + serviceTime)
		subroutes[assignedVehicle]['newStop'] = {'location': locations_info[orders_info[order, 4], 0], 'timeWindow': [int(subroutes[assignedVehicle][assignedStop-1]['timeWindow'][1] + travelTimes[node1, node2, typesOfLM]), int(subroutes[assignedVehicle][assignedStop-1]['timeWindow'][1] + travelTimes[node1, node2, typesOfLM]) + serviceTime], 'pickups': [order], 'deliveries': []}
		for k in subroutes[assignedVehicle].keys():
			if k != "newStop":
				if k >= assignedStop:
					subroutes[assignedVehicle][k]['timeWindow'][0] += delay
					subroutes[assignedVehicle][k]['timeWindow'][1] += delay
					for j in range(len(locations_info)):
						if locations_info[j, 0] == subroutes[assignedVehicle][k]['location']:
							break
					if locations_info[j, 1] in ["hub", "depot"]:
						subroutes[assignedVehicle][k]['deliveries'].append(order)
						for l in routes.keys():
							for m in routes[l].keys():
								if subroutes[assignedVehicle][assignedStop]['timeWindow'][0] in range(routes[l][m]['timeWindow'][0], routes[l][m]['timeWindow'][1]+1) and subroutes[assignedVehicle][k]['location'] == routes[l][m]['location']:
									if routes[l][m]['timeWindow'][1] < subroutes[assignedVehicle][k]['timeWindow'][1]:
										routes[l][m]['timeWindow'][1] = subroutes[assignedVehicle][k]['timeWindow'][1]
									routes[l][m]['pickups'].append(order)
									for p in routes[l].keys():
										if p >= m:
											for i in range(len(locations_info)):
												if locations_info[i, 0] == routes[l][p]['location']:
													break
											if locations_info[i, 1] == "depot":
												routes[l][p]['deliveries'].append(order)
									break
						break
	for r in subroutes.keys():
		sorted_keys, sortedRoute, nTrips = [], {}, 0
		for t in range(24*60):
			for j in subroutes[r].keys():
				if subroutes[r][j]['timeWindow'][0] >= t and subroutes[r][j]['timeWindow'][0] < t+1 and j not in sorted_keys:
					sorted_keys.append(j)
		for j in sorted_keys:
			sortedRoute[nTrips] = subroutes[r][j]
			nTrips += 1
		subroutes[r] = sortedRoute
	return routes, subroutes

def reSchedule(routes, subroutes, timeOfEvent, orders_info, locations_info, orders_time):
	selectedRoute, selectedStop = None, None
	for r in routes.keys():
		if selectedRoute == None:
			for k in routes[r].keys():
				if selectedStop == None:
					if timeOfEvent in range(routes[r][k]['timeWindow'][0], routes[r][k]['timeWindow'][1]+1):
						for l in routes[r][k]['vehicles'].keys():
							if routes[r][k]['vehicles'][l]['releaseTime'] > timeOfEvent:
								selectedRoute, selectedStop = r, k
	if selectedRoute != None and selectedStop != None:
		startTW = 0
		for l in routes[selectedRoute][selectedStop]['vehicles'].keys():
			if routes[selectedRoute][selectedStop]['vehicles'][l]['releaseTime'] <= timeOfEvent:
				if routes[selectedRoute][selectedStop]['vehicles'][l]['id'] in subroutes.keys():
					r = routes[selectedRoute][selectedStop]['vehicles'][l]['id']
					for k in subroutes[r].keys():
						if subroutes[r][k]['timeWindow'][0] in range(routes[selectedRoute][selectedStop]['timeWindow'][0], routes[selectedRoute][selectedStop]['timeWindow'][1]+1):
							if subroutes[r][k]['location'] != routes[selectedRoute][selectedStop]['location']:
								for n in subroutes[r][k]['pickups']:
									if n in routes[selectedRoute][selectedStop]['pickups']:
										routes[selectedRoute][selectedStop]['pickups'].remove(n)
								for n in subroutes[r][k]['deliveries']:
									if n in routes[selectedRoute][selectedStop]['deliveries']:
										routes[selectedRoute][selectedStop]['deliveries'].remove(n)
							else:
								if (timeOfEvent in range(subroutes[r][k]['timeWindow'][0], subroutes[r][k]['timeWindow'][1]+1)) or timeOfEvent <= subroutes[r][k]['timeWindow'][0]:
									if subroutes[r][k]['timeWindow'][0] > startTW:
										startTW = subroutes[r][k]['timeWindow'][0]
									break
			else:
				if routes[selectedRoute][selectedStop]['vehicles'][l]['id'] in subroutes.keys():
					r = routes[selectedRoute][selectedStop]['vehicles'][l]['id']
					loaded, toDeliver = [], []
					for k in subroutes[r].keys():
						if subroutes[r][k]['timeWindow'][0] in range(routes[selectedRoute][selectedStop]['timeWindow'][0], routes[selectedRoute][selectedStop]['timeWindow'][1]+1):
							if timeOfEvent in range(subroutes[r][k]['timeWindow'][0], subroutes[r][k]['timeWindow'][1]+1) or timeOfEvent <= subroutes[r][k]['timeWindow'][0]:
								if timeOfEvent <= subroutes[r][k]['timeWindow'][0]:
									for n in loaded:
										if n not in routes[selectedRoute][selectedStop]['pickups']:
											routes[selectedRoute][selectedStop]['pickups'].append(n)
										if n in routes[selectedRoute][selectedStop]['deliveries']:
											routes[selectedRoute][selectedStop]['deliveries'].remove(n)
											toDeliver.append(n)
										orders_info[n, 3] = 1.0
										for j in range(len(locations_info)):
											if locations_info[j, 0] == subroutes[r][k]['location']:
												orders_info[n, 4] = j
									break
								if timeOfEvent in range(subroutes[r][k]['timeWindow'][0], subroutes[r][k]['timeWindow'][1]+1):
									for n in subroutes[r][k]['deliveries']:
										if n in loaded:
											loaded.remove(n)
										if n in routes[selectedRoute][selectedStop]['deliveries']:
											routes[selectedRoute][selectedStop]['deliveries'].remove(n)
									for n in loaded:
										if n not in routes[selectedRoute][selectedStop]['pickups']:
											routes[selectedRoute][selectedStop]['pickups'].append(n)
										if n in routes[selectedRoute][selectedStop]['deliveries']:
											routes[selectedRoute][selectedStop]['deliveries'].remove(n)
										orders_info[n, 2], orders_info[n, 3] = 0.0, 1.0
										for j in range(len(locations_info)):
											if locations_info[j, 1] == "depot":
												orders_info[n, 5] = j
											if locations_info[j, 0] == subroutes[r][k]['location']:
												orders_info[n, 4] = j
									break
							else:
								for n in subroutes[r][k]['pickups']:
									loaded.append(n)
								for n in subroutes[r][k]['deliveries']:
									if n in loaded:
										loaded.remove(n)
									if n in routes[selectedRoute][selectedStop]['deliveries']:
										routes[selectedRoute][selectedStop]['deliveries'].remove(n)
		if len(toDeliver) > 0:
			routes[selectedRoute]['newStop'] = {'location': routes[selectedRoute][selectedStop]['location'], 'timeWindow': [routes[selectedRoute][selectedStop]['timeWindow'][1]+1, routes[selectedRoute][selectedStop]['timeWindow'][1]+1], 'pickups': [], 'deliveries': toDeliver, 'vehicles': routes[selectedRoute][selectedStop]['vehicles'], 'customers': len(toDeliver)}
		if startTW > 0:
			routes[selectedRoute][selectedStop]['timeWindow'][0] = startTW
		for r in routes.keys():
			sorted_keys, sortedRoute, nTrips = [], {}, 0
			for t in range(24*60):
				for j in routes[r].keys():
					if routes[r][j]['timeWindow'][0] >= t and routes[r][j]['timeWindow'][0] < t+1 and j not in sorted_keys:
						sorted_keys.append(j)
			for j in sorted_keys:
				sortedRoute[nTrips] = routes[r][j]
				nTrips += 1
			routes[r] = sortedRoute			
	return routes, orders_info, orders_time