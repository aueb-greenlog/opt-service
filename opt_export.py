from datetime import *
import warnings
import math
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import osmnx as ox, networkx as nx, pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
ox.config(use_cache = True, log_console = False)
from bng_latlon import OSGB36toWGS84
from PIL import Image, ImageFont, ImageDraw
from pyproj import Transformer
import uuid

def export_json(livingLab, vehicles_info, routes, subroutes, orders_info, orders_time, locations_info, travelTimes, uuid, user, maxOrders):
	eligibleTypes = list(set([type for v in range(len(vehicles_info)) for type in vehicles_info[v, 1] if type not in ['mobile', 'last-mile']]))
	operators = list(set(orders_info[n, 8] for n in range(len(orders_info))))
	json_dict = {}
	json_dict['general'], json_dict['routes'] = {}, {}
	json_dict['general']['KPIs'] = {'numRoutes': 0, 'totalDistance': 0.0, 'parcelsPerRoute': 0.0, 'totalEmissions': 0.0, 'totalDelay': 0.0}

	if livingLab == "Oxford, England":
		network = ox.graph_from_point(ox.geocode(livingLab), dist = 5000, network_type = 'bike')
	if livingLab == "Barcelona, Spain":
		network = ox.graph_from_point(ox.geocode(livingLab), dist = 6000, network_type = 'walk')
	if livingLab == "Athens, Greece":
		network = ox.graph_from_point(ox.geocode(livingLab), dist = 3000, network_type = 'drive')

	for r in subroutes.keys():
		if r in [key for key in routes.keys()]:
			for v in range(len(vehicles_info)):
				if r in vehicles_info[v, 0][0]:
					if "carrier" in vehicles_info[v, 1]:
						isCarrier = True
					else:
						isCarrier = False
					break
			nTrips = len([key for key in routes[r].keys()]) - int(bool(isCarrier))
			for j in subroutes[r].keys():
				routes[r][nTrips] = subroutes[r][j]
				if isCarrier == True and nTrips == len([key for key in routes[r].keys()]) - 1:
					routes[r][nTrips]['pickups'] = []
				nTrips += 1
		else:
			routes[r], nTrips = {}, 0
			for j in subroutes[r].keys():
				if any(routes[r][i]['timeWindow'] == subroutes[r][j]['timeWindow'] for i in range(nTrips)):
					pass
				else:
					routes[r][nTrips] = subroutes[r][j]
					nTrips += 1
	if len(operators) > 1:
		consolidatedMDH = {}
		for r in routes.keys():
			for v in range(len(vehicles_info)):
				if r in vehicles_info[v, 0][0]:
					nTrips, ignored = 0, []
					consolidatedMDH[r] = {}
					for k in routes[r].keys():
						pickups, deliveries = [], []
						if k not in ignored:
							for c in routes[r][k]['duplicates']:
								for n in routes[r][c]['pickups']:
									if n not in pickups:
										pickups.append(n)
								for n in routes[r][c]['deliveries']:
									if n not in deliveries:
										deliveries.append(n)
								ignored.append(c)
							consolidatedMDH[r][nTrips] = routes[r][k]
							consolidatedMDH[r][nTrips]['pickups'], consolidatedMDH[r][nTrips]['deliveries'] = pickups, deliveries
							nTrips += 1
					routes[r] = consolidatedMDH[r]

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

			json_dict['routes'][numRoutes]['sequence'][nStops] = {'location': routes[r][j]['location'], 'arrivalTime': timeFloor, 'departureTime': timeCeil, 'associatedOrders': []}
			for n in routes[r][j]['pickups']:
				if orders_info[n, 9] not in json_dict['routes'][numRoutes]['sequence'][nStops]['associatedOrders']:
					json_dict['routes'][numRoutes]['sequence'][nStops]['associatedOrders'].append(orders_info[n, 9])
					if orders_info[n, 3] == 1:
						nParcels += 1
			for n in routes[r][j]['deliveries']:
				if orders_info[n, 9] not in json_dict['routes'][numRoutes]['sequence'][nStops]['associatedOrders']:
					json_dict['routes'][numRoutes]['sequence'][nStops]['associatedOrders'].append(orders_info[n, 9])
					if orders_info[n, 2] == 1:
						if routes[r][j]['timeWindow'][0] > orders_time[n, 2]:
							json_dict['general']['KPIs']['totalDelay'] += int(routes[r][j]['timeWindow'][0] - orders_time[n, 2])
							json_dict['routes'][numRoutes]['KPIs']['totalDelay'] += int(routes[r][j]['timeWindow'][0] - orders_time[n, 2])
						nParcels += 1
			if nStops == 0:
				previousPoint = routes[r][j]['location']
			else:
				incumbentPoint = routes[r][j]['location']
				if livingLab == "Oxford, England":
					for i in range(len(locations_info)):
						if locations_info[i, 0] == incumbentPoint:
							coordinates = OSGB36toWGS84(locations_info[i, 2], locations_info[i, 3])
							destination = ox.nearest_nodes(network, coordinates[1], coordinates[0])
						if locations_info[i, 0] == previousPoint:
							coordinates = OSGB36toWGS84(locations_info[i, 2], locations_info[i, 3])
							origin = ox.nearest_nodes(network, coordinates[1], coordinates[0])
				if livingLab == "Barcelona, Spain":
					transformer = Transformer.from_crs("IGNF:ETRS89UTM31", "EPSG:4326")
					for i in range(len(locations_info)):
						if locations_info[i, 0] == incumbentPoint:
							coordinates = transformer.transform(locations_info[i, 2], locations_info[i, 3])
							destination = ox.nearest_nodes(network, coordinates[1], coordinates[0])
						if locations_info[i, 0] == previousPoint:
							coordinates = transformer.transform(locations_info[i, 2], locations_info[i, 3])
							origin = ox.nearest_nodes(network, coordinates[1], coordinates[0])
				if livingLab == "Athens, Greece":
					transformer = Transformer.from_crs("EPSG:2100", "EPSG:4326")
					for i in range(len(locations_info)):
						if locations_info[i, 0] == incumbentPoint:
							coordinates = transformer.transform(locations_info[i, 2], locations_info[i, 3])
							destination = ox.nearest_nodes(network, coordinates[1], coordinates[0])
						if locations_info[i, 0] == previousPoint:
							coordinates = transformer.transform(locations_info[i, 2], locations_info[i, 3])
							origin = ox.nearest_nodes(network, coordinates[1], coordinates[0])
				if livingLab == "Ispra, Italy":
					for i in range(len(locations_info)):
						if locations_info[i, 0] == incumbentPoint:
							lat1, lon1 = locations_info[i, 3]*0.0174532925, locations_info[i, 2]*0.0174532925
						if locations_info[i, 0] == previousPoint:
							lat2, lon2 = locations_info[i, 3]*0.0174532925, locations_info[i, 2]*0.0174532925
				try:
					if livingLab != "Ispra, Italy":
						newDistance = round(0.001*nx.shortest_path_length(network, source=origin, target=destination, weight='length', method='dijkstra'), 2)
					else:
						newDistance = round(math.acos(math.sin(lat1)*math.sin(lat2)+math.cos(lat1)*math.cos(lat2)*math.cos(lon2-lon1))*6371, 2)
				except Exception:
					newDistance = 200
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
		json_dict['general']['KPIs']['parcelsPerRoute'] = round(maxOrders/(json_dict['general']['KPIs']['numRoutes'] - int(bool(any("mobile" in vehicles_info[v, 1] for v in range(len(vehicles_info)))))), 2)
	except Exception:
		json_dict['general']['KPIs']['parcelsPerRoute'] = None
	return json_dict, routes


def aimsun_json(livingLab, routeDate, vehicles_info, routes, orders_info, locations_info):
	json_dict, definition = {}, {}
	json_dict["name"], json_dict["vehicles"] = f"Ride Fleet Schedule Input for {livingLab}", []
	newUuid = uuid.uuid4()
	definition['id'], definition['name'], definition['type'], definition['address'], definition['vehicle_type'], definition['fleet'] = str(newUuid), "P&P Operation Emulator, Oxford, UK", "external", "localhost:45001", 152, []
	
	for r in routes.keys():
		vUuid = uuid.uuid4()
		definition['fleet'].append({"id": str(vUuid), "name": str(r), "origin": {"object": "Redbridge_P&R_P&PDepot"}})
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