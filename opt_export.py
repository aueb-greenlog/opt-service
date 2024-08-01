from pyproj import Transformer
import math
#import csv

def export_json(livingLab, vehicles_info, routes, subroutes, orders_info, orders_time, locations_info, travelTimes, uuid, maxOrders, newOrders):
	eligibleTypes = list(set([type for v in range(len(vehicles_info)) for type in vehicles_info[v, 1] if type not in ['mobile', 'last-mile']]))
	operators = list(set(orders_info[n, 8] for n in range(len(orders_info))))
	json_dict = {}
	json_dict['general'], json_dict['routes'] = {}, {}
	json_dict['general']['KPIs'] = {'numRoutes': 0, 'totalDistance': 0.0, 'parcelsPerRoute': 0.0, 'totalEmissions': 0.0, 'totalDelay': 0.0}

	distances = {}
	for i in range(len(locations_info)):
		distances[locations_info[i, 0]] = {}
		for j in range(len(locations_info)):
			if livingLab == "Ispra, Italy":
				transformer = Transformer.from_crs("EPSG:4326", "EPSG:7794")
				coordinates1 = transformer.transform(locations_info[i, 2], locations_info[i, 3])
				coordinates2 = transformer.transform(locations_info[j, 2], locations_info[j, 3])
				distance = int(math.ceil(abs(coordinates1[1] - coordinates2[1]) + abs(coordinates1[0] - coordinates2[0])))
			else:
				distance = abs(locations_info[i, 2] - locations_info[j, 2]) + abs(locations_info[i, 3] - locations_info[j, 3])
			if livingLab == "Barcelona, Spain":
				if (locations_info[i, 1] == "depot" and locations_info[j, 1] == "hub") or (locations_info[i, 1] == "hub" and locations_info[j, 1] == "depot"):
					distance = 1700
				if locations_info[i, 1] == "hub" and locations_info[j, 1] == "hub":
					distance = 0
			distances[locations_info[i, 0]][locations_info[j, 0]] = int(distance)

	for r in subroutes.keys():
		if r in [key for key in routes.keys()]:
			for v in range(len(vehicles_info)):
				if r in vehicles_info[v, 0][0]:
					if "mobile" in vehicles_info[v, 1] and "last-mile" in vehicles_info[v, 1]:
						isCarrier = True
						lastKey = routes[r][len(routes[r].keys())-1]
					else:
						isCarrier = False
					break
			nTrips = len([key for key in routes[r].keys()]) - 2*int(bool(isCarrier))
			for j in subroutes[r].keys():
				routes[r][nTrips] = subroutes[r][j]
				#if isCarrier == True and nTrips == len([key for key in routes[r].keys()]) - 1:
				#	routes[r][nTrips]['pickups'] = []
				nTrips += 1
			if isCarrier:
				routes[r][nTrips] = lastKey
				for i in range(len(locations_info)):
					for j in range(len(locations_info)):
						for t in range(len(eligibleTypes)):
							if locations_info[i, 0] == routes[r][nTrips-1]['location'] and locations_info[j, 0] == routes[r][nTrips]['location']:
								routes[r][nTrips]['timeWindow'][0] = routes[r][nTrips]['timeWindow'][1] = int(routes[r][nTrips-1]['timeWindow'][1] + travelTimes[i, j, t])
		else:
			routes[r], nTrips = {}, 0
			for j in subroutes[r].keys():
				routes[r][nTrips] = subroutes[r][j]
				nTrips += 1
	
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

	for r in routes.keys():
		for v in range(len(vehicles_info)):
			if r in vehicles_info[v, 0][0]:
				break
		for j in routes[r].keys():
			if j > 0:
				if routes[r][j]['timeWindow'][0] < routes[r][j-1]['timeWindow'][1]:
					for loc1 in range(len(locations_info)):
						if locations_info[loc1, 0] == routes[r][j-1]['location']:
							break
					for loc2 in range(len(locations_info)):
						if locations_info[loc2, 0] == routes[r][j]['location']:
							break
					for t in range(len(eligibleTypes)):
						if eligibleTypes[t] in vehicles_info[v, 1]:
							break
					routes[r][j-1]['timeWindow'][1] = int(routes[r][j]['timeWindow'][0] - travelTimes[loc1, loc2, t])
	
	numRoutes = 0
	for r in routes.keys():
		if r != "depot":
			json_dict['routes'][numRoutes], nParcels, nStops = {'vehicle': r, 'KPIs': {'totalDistance': 0.0, 'parcels': 0.0, 'totalEmissions': 0.0, 'totalDelay': 0.0}, 'sequence': {}}, 0, 0
			for j in routes[r].keys():
				hour = int(routes[r][j]['timeWindow'][0]/60)
				minutes = routes[r][j]['timeWindow'][0] - hour*60
				if hour >= 10:
					hour = str(hour)
				else:
					hour = "0"+str(hour)
				if minutes >= 10:
					minutes = str(minutes)
				else:
					minutes = "0"+str(minutes)
				timeFloor = hour+":"+minutes
				hour = int(routes[r][j]['timeWindow'][1]/60)
				minutes = routes[r][j]['timeWindow'][1] - hour*60
				if hour >= 10:
					hour = str(hour)
				else:
					hour = "0"+str(hour)
				if minutes >= 10:
					minutes = str(minutes)
				else:
					minutes = "0"+str(minutes)
				timeCeil = hour+":"+minutes

				json_dict['routes'][numRoutes]['sequence'][nStops] = {'location': routes[r][j]['location'], 'arrivalTime': timeFloor, 'departureTime': timeCeil, 'pickUps': [], 'dropOffs': []}
				for n in routes[r][j]['pickups']:
					if orders_info[n, 9] not in json_dict['routes'][numRoutes]['sequence'][nStops]['pickUps']:
						json_dict['routes'][numRoutes]['sequence'][nStops]['pickUps'].append(orders_info[n, 9])
						if orders_info[n, 3] == 1:
							nParcels += 1
				for n in routes[r][j]['deliveries']:
					if orders_info[n, 9] not in json_dict['routes'][numRoutes]['sequence'][nStops]['dropOffs']:
						json_dict['routes'][numRoutes]['sequence'][nStops]['dropOffs'].append(orders_info[n, 9])
						if orders_info[n, 2] == 1:
							if routes[r][j]['timeWindow'][0] > orders_time[n, 2]:
								json_dict['general']['KPIs']['totalDelay'] += int(routes[r][j]['timeWindow'][0] - orders_time[n, 2])
								json_dict['routes'][numRoutes]['KPIs']['totalDelay'] += int(routes[r][j]['timeWindow'][0] - orders_time[n, 2])
							nParcels += 1
				if nStops == 0:
					previousPoint = routes[r][j]['location']
				else:
					incumbentPoint = routes[r][j]['location']
					newDistance = round(int(distances[previousPoint][incumbentPoint])/1000, 2)
					previousPoint = incumbentPoint
					json_dict['routes'][numRoutes]['KPIs']['totalDistance'] += newDistance
					json_dict['general']['KPIs']['totalDistance'] += newDistance
					json_dict['routes'][numRoutes]['KPIs']['parcels'] = nParcels
					for v in range(len(vehicles_info)):
						if r in vehicles_info[v, 0]:
							json_dict['general']['KPIs']['totalEmissions'] += vehicles_info[v, 2]*newDistance
							json_dict['routes'][numRoutes]['KPIs']['totalDistance'] += vehicles_info[v, 2]*newDistance
				nStops += 1
			json_dict['routes'][numRoutes]['KPIs']['totalDistance'] = round(json_dict['routes'][numRoutes]['KPIs']['totalDistance'], 2)
			numRoutes += 1
	json_dict['general']['KPIs']['totalDistance'] = round(json_dict['general']['KPIs']['totalDistance'], 2)
	json_dict['general']['KPIs']['numRoutes'] = numRoutes
	try:
		json_dict['general']['KPIs']['parcelsPerRoute'] = round(maxOrders/(json_dict['general']['KPIs']['numRoutes'] - int(bool(any("mobile" in vehicles_info[v, 1] for v in range(len(vehicles_info)) if "last-mile" not in vehicles_info[v, 1])))), 2)
	except Exception:
		json_dict['general']['KPIs']['parcelsPerRoute'] = None

	'''
	for r in routes.keys():
		filename = f"routes_{r}.csv"
		counter = 1
		with open(filename, 'w') as outfile:
			outfile.write("id;x;y;new;order\n")
			for k in routes[r].keys():
				for j in range(len(locations_info)):
					if locations_info[j, 0] == routes[r][k]['location']:
						break
				outfile.write(f"{locations_info[j, 0]};{locations_info[j, 2]};{locations_info[j, 3]};{bool(any(n in routes[r][k]['pickups'] or n in routes[r][k]['deliveries'] for n in newOrders))};{counter}\n")
				counter += 1
			outfile.close()
	'''
	return json_dict, routes

'''
def aimsun_json(livingLab, routeDate, vehicles_info, routes, orders_info, locations_info):
	objects = {"Oxford, England": "Redbridge_P&R_P&PDepot", "Barcelona, Spain": "Vanapedal_depot"}
	names = {"Oxford, England": "P&P Operation Emulator, Oxford, UK", "Barcelona, Spain": "Vanapedal Operation Emulator, Barcelona, ESP"}

	json_dict, definition = {}, {}
	json_dict["name"], json_dict["vehicles"] = f"Ride Fleet Schedule Input for {livingLab}", []
	newUuid = uuid.uuid4()
	definition['id'], definition['name'], definition['type'], definition['address'], definition['vehicle_type'], definition['fleet'] = str(newUuid), names[livingLab], "external", "localhost:45001", 152, []

	for r in routes.keys():
		if r != "0":
			vUuid = uuid.uuid4()
			definition['fleet'].append({"id": str(vUuid), "name": str(r), "origin": {"object": objects[livingLab]}})
			keys = [key for key in routes[r].keys()]
			keys.sort()
			for k in keys:
				if k == keys[0]:
					startTime = int(routes[r][k]['timeWindow'][1]*60000)
					json_dict["vehicles"].append({"vehId": str(vUuid), "schedule": {"scheduleStartTime": startTime, "scheduleItems": []}})
				for v in range(len(vehicles_info)):
					if r in vehicles_info[v, 0][0]:
						if "mobile" in vehicles_info[v, 1] and k > keys[0]:
							itemId = uuid.uuid4()
							for j in range(len(locations_info)):
								if locations_info[j, 0] == routes[r][k]['location']:
									selectedLoc = j
									break
							if len(json_dict["vehicles"][len(json_dict["vehicles"])-1]["schedule"]["scheduleItems"]) == 0 and "depot" == locations_info[selectedLoc, 1]:
								pass
							else:
								json_dict["vehicles"][len(json_dict["vehicles"])-1]["schedule"]["scheduleItems"].append({"itemId": str(itemId), "requestId": str(itemId), "itemOperationType": "Relocation", "itemOperationDuration": 60000*int(routes[r][k]['timeWindow'][1] - routes[r][k]['timeWindow'][0]), "itemOperationDestination": {"x": locations_info[selectedLoc, 2], "y": locations_info[selectedLoc, 3]}})
						elif "last-mile" in vehicles_info[v, 1]:
							for j in range(len(locations_info)):
								if locations_info[j, 0] == routes[r][k]['location']:
									selectedLoc = j
									break
							if "depot" == locations_info[selectedLoc, 1] or "hub" == locations_info[selectedLoc, 1]:
								if len(routes[r][k]['pickups']) > 0:
									operation = "Collection"
									for n in routes[r][k]['pickups']:
										associatedOrder = orders_info[n, 9]
								if len(routes[r][k]['deliveries']) > 0:
									operation = "DropOff"
									for n in routes[r][k]['deliveries']:
										associatedOrder = orders_info[n, 9]
								if len(routes[r][k]['deliveries']) == 0 and len(routes[r][k]['pickups']) == 0:
									operation = "Relocation"
									itemId = uuid.uuid4()
									associatedOrder = str(itemId)
							else:
								if len(routes[r][k]['pickups']) > 0:
									operation = "Pickup"
									for n in routes[r][k]['pickups']:
										associatedOrder = orders_info[n, 9]
								if len(routes[r][k]['deliveries']) > 0:
									operation = "Delivery"
									for n in routes[r][k]['deliveries']:
										associatedOrder = orders_info[n, 9]
							if len(json_dict["vehicles"][len(json_dict["vehicles"])-1]["schedule"]["scheduleItems"]) == 0 and "depot" == locations_info[selectedLoc, 1]:
								pass
							else:
								json_dict["vehicles"][len(json_dict["vehicles"])-1]["schedule"]["scheduleItems"].append({"itemId": str(associatedOrder), "requestId": str(associatedOrder), "itemOperationType": operation, "itemOperationDuration": 60000*int(routes[r][k]['timeWindow'][1] - routes[r][k]['timeWindow'][0]), "itemOperationDestination": {"x": locations_info[selectedLoc, 2], "y": locations_info[selectedLoc, 3]}})
			if "depot" != locations_info[selectedLoc, 1]:
				for j in range(len(locations_info)):
					if locations_info[j, 1] == "depot":
						randomUuid = uuid.uuid4()
						json_dict["vehicles"][len(json_dict["vehicles"])-1]["schedule"]["scheduleItems"].append({"itemId": str(randomUuid), "requestId": str(randomUuid), "itemOperationType": "GoingToPark", "itemOperationDuration": 0, "itemOperationDestination": {"x": locations_info[j, 2], "y": locations_info[j, 3]}})
						break

	return json_dict, definition
'''