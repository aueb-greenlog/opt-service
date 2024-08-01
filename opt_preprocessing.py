from datetime import datetime, date, timedelta
import warnings
warnings.filterwarnings("ignore")
from datetime import *
import numpy as np
import math
from pyproj import Transformer

def import_data(input_data):
	tens, units = int(input_data['general']['availableBefore'][11]), int(input_data['general']['availableBefore'][12])
	now = (tens*10 + units)*60
	isValid = True
	
	orders_info, orders_size, orders_time = np.empty(shape=(0, 11)), np.empty(shape=(0, 6)), np.empty(shape=(0, 3))
	locations_info, locations_time = np.empty(shape=(0, 4)), np.empty(shape=(0, 3))
	vehicles_info, vehicles_size = np.empty(shape=(0, 7)), np.empty(shape = (0, 6))

	mode, objective = None, None
	mode = input_data['general']['service']['mode']
	if mode == 'eventTriggered':
		event = input_data['general']['service']['event']
		timeOfEvent = input_data['general']['service']['time']
	else:
		event = None
		timeOfEvent = None
	objective = input_data['general']['objective']
	routeDate = input_data['general']['date']
	livingLab = input_data['general']['livingLab']

	nLocations, nHubs, nDepots = 0, 0, 0
	for key, item in input_data['locations'].items():
		tags = item['tags']
		if item['tags'] == 'depot':
			nDepots += 1
		if item['tags'] == 'hub':
			nHubs += 1
		x, y = item['coordinates']['x'], item['coordinates']['y']
		locations_info = np.append(locations_info, np.array([[key, tags, x, y]], dtype='object'), axis=0)
		startTime = 60*(10*int(item['operatingHours']['start'][0]) + int(item['operatingHours']['start'][1])) + 10*int(item['operatingHours']['start'][3]) + int(item['operatingHours']['start'][4])
		endTime = 60*(10*int(item['operatingHours']['end'][0]) + int(item['operatingHours']['end'][1])) + 10*int(item['operatingHours']['end'][3]) + int(item['operatingHours']['end'][4])
		try:
			timeTables = item['timeTables']
		except Exception:
			timeTables = []
		locations_time = np.append(locations_time, np.array([[startTime, endTime, timeTables]], dtype='object'), axis=0)
		nLocations += 1
		
	if nDepots == 0:
		print(datetime.now(), f" - Algorithm killed: No depots are available.")
		isValid = False
	else:
		nOrders = 0
		for key, item in input_data['orders'].items():
			parcels = [parcel for parcel in item['parcels'].keys()]
			isDelivery, isPickup, isCollected = int(bool('Delivery' in item['operation'])), int(bool('Pickup' in item['operation'])), int(bool('Click-and-Collect' in item['operation']))
			pickupLocation, index = str(item['location']['Pickup']), None
			for j in range(nLocations):
				if str(locations_info[j, 0]) == str(pickupLocation):
					index = j
					pickupLocation = index
					break			
			deliveryLocation, index = str(item['location']['Delivery']), None
			for j in range(nLocations):
				if str(locations_info[j, 0]) == str(deliveryLocation):
					index = j
					deliveryLocation = index
					break
			eligibleAssignments = item['canBeTransferredWith']
			tags = []
			for parcel in item['parcels'].keys():
				try:
					for type in item['parcels'][parcel]['tags']:
						if type not in tags:
							tags.append(type)
				except Exception:
					pass
			operator = item['operator']
			orders_info = np.append(orders_info, np.array([[int(nOrders), parcels, isDelivery, isPickup, pickupLocation, deliveryLocation, eligibleAssignments, tags, operator, key, isCollected]], dtype='object'), axis=0)
			weight, volume, length, width, height, numParcels = 0.0, 0.0, 0.0, 0.0, 0.0, 0
			for parcel in item['parcels'].keys():
				weight += item['parcels'][parcel]['weight']
				volume += item['parcels'][parcel]['volume']
				length += item['parcels'][parcel]['length']
				width += item['parcels'][parcel]['width']
				height += item['parcels'][parcel]['height']
				numParcels += 1
			orders_size = np.append(orders_size, np.array([[weight, volume, length, width, height, numParcels]], dtype='object'), axis=0)
			release = (10*int(item['availableAfter'][0]) + int(item['availableAfter'][1]))*60 + int(item['availableAfter'][3])*10 + int(item['availableAfter'][4])
			after = 60*(10*int(item['timeWindow']['After'][0]) + int(item['timeWindow']['After'][1])) + 10*int(item['timeWindow']['After'][3]) + int(item['timeWindow']['After'][4])
			before = 60*(10*int(item['timeWindow']['Before'][0]) + int(item['timeWindow']['Before'][1])) + 10*int(item['timeWindow']['Before'][3]) + int(item['timeWindow']['Before'][4])
			orders_time = np.append(orders_time, np.array([[release, after, before]]), axis=0)
			nOrders += 1

		if nOrders == 0:
			print(datetime.now(), f" - Algorithm killed: No orders are available.")
			isValid = False
		else:
			canBeTransferredWith = np.ones(shape = [nOrders, nOrders])
			for i in range(nOrders):
				for type_i in orders_info[i, 7]:
					for j in range(nOrders):
						for type_j in orders_info[j, 7]:
							if type_j in [key for key in orders_info[i, 6].keys()]:
								if orders_info[i, 6][type_j] == 0:
									canBeTransferredWith[i, j] = 0
							if type_i in [key for key in orders_info[j, 6].keys()]:
								if orders_info[j, 6][type_i] == 0:
									canBeTransferredWith[i, j] = 0
		nLastmile, nMobile, nVehicles = 0, 0, 0
		for key, item in input_data['vehicles'].items():
			tags = [item['tags'][j] for j in range(len(item['tags']))]
			if "mobile" in tags:
				if "carrier" not in tags:
					copies = 2
				else:
					copies = 1
			else:
				copies = 1
			emissions = item['CO2_emissions']
			maxTime = item['maxTime']
			currentLocation, index = item['currentLocation'], None
			for j in range(nLocations):
				if locations_info[j, 0] == currentLocation:
					index = j
					currentLocation = index
					break
			release = 60*(10*int(item['availableAfter'][0]) + int(item['availableAfter'][1])) + 10*int(item['availableAfter'][3]) + int(item['availableAfter'][4])
			operator = item['operator']
			vehicles_info = np.append(vehicles_info, np.array([[[str(key)+"*"+str(c+1) for c in range(copies)], tags, emissions, maxTime, currentLocation, release, operator]], dtype='object'), axis=0)
			weight, volume, length, width, height, numParcels = 0.0, 0.0, 0.0, 0.0, 0.0, 0
			for compartment in range(len(item['capacity'])):
				weight += item['capacity'][compartment]['maxWeight']
				volume += item['capacity'][compartment]['maxVolume']
				length += item['capacity'][compartment]['maxLength']
				width += item['capacity'][compartment]['maxWidth']
				height += item['capacity'][compartment]['maxHeight']
				numParcels += item['capacity'][compartment]['numParcels']	
			vehicles_size = np.append(vehicles_size, np.array([[weight, volume, length, width, height, numParcels]], dtype='object'), axis=0)
			if 'last-mile' in tags:
				nLastmile += 1
			if 'mobile' in tags:
				nMobile += 1
			nVehicles += 1

		eligible_types, speeds = [], []
		for v in range(len(vehicles_info)):
			if "carrier" in vehicles_info[v, 1] and "carrier" not in eligible_types:
				eligible_types.append("carrier")
				speeds.append(65)
				serviceTime = 3
			if "bike" in vehicles_info[v, 1] and "bike" not in eligible_types:
				eligible_types.append("bike")
				speeds.append(250)
				serviceTime = 3
			if "scooter" in vehicles_info[v, 1] and "scooter" not in eligible_types:
				eligible_types.append("scooter")
				speeds.append(350)
				serviceTime = 3
			if "van" in vehicles_info[v, 1] and "van" not in eligible_types:
				eligible_types.append("van")
				if livingLab != "Athens, Greece":
					speeds.append(350)
				else:
					speeds.append(250)
				serviceTime = 3
			if "droid" in vehicles_info[v, 1] and "droid" not in eligible_types:
				eligible_types.append("droid")
				speeds.append(60)
				serviceTime = 0

		travelTimes = np.zeros(shape = [nLocations, nLocations, len(eligible_types)])
		for i in range(nLocations):
			for j in range(nLocations):
				if livingLab == "Ispra, Italy":
					transformer = Transformer.from_crs("EPSG:4326", "EPSG:7794")
					coordinates1 = transformer.transform(locations_info[i, 2], locations_info[i, 3])
					coordinates2 = transformer.transform(locations_info[j, 2], locations_info[j, 3])
					distance = int(math.ceil(abs(coordinates1[1] - coordinates2[1]) + abs(coordinates1[0] - coordinates2[0])))
				else:
					distance = abs(locations_info[i, 2] - locations_info[j, 2]) + abs(locations_info[i, 3] - locations_info[j, 3])
				for t in range(len(eligible_types)):
					try:
						#travelTimes[i, j, t] = int(math.ceil(input_data['locations'][locations_info[i, 0]]['travelTime'][eligible_types[t]][locations_info[j, 0]]))
						if 'Spain' in livingLab and locations_info[i, 1] in ["depot", "hub"] and locations_info[j, 1] in ["depot", "hub"] and eligible_types[t] == "carrier":
							if livingLab == "Barcelona, Spain":
								travelTimes[i, j, t] = int(math.ceil(distance/500))
								if locations_info[i, 1] == "depot" or locations_info[j, 1] == "depot":
									travelTimes[i, j, t] += 20
								if locations_info[i, 1] == "hub" and locations_info[j, 1] == "hub":
									distance = 0
							if livingLab == "Terrassa, Spain":
								travelTimes[i, j, t] = int(math.ceil(distance/500))
								if (locations_info[i, 1] == "depot" or locations_info[j, 1] == "depot") and travelTimes[i, j, t] > 0:
									travelTimes[i, j, t] += 11
								if locations_info[i, 1] == "hub" and locations_info[j, 1] == "hub":
									distance = 0
						else:
							travelTimes[i, j, t] = int(math.ceil(distance/speeds[t]))
					except Exception:
						travelTimes[i, j, t] = 300

		allOperators = []
		for n in range(len(orders_info)):
			if orders_info[n, 8] not in allOperators:
				allOperators.append(orders_info[n, 8])
		if len(allOperators) == 0:
			randomLSP = "newLSP"
			for n in range(len(orders_info)):
				orders_info[n, 8] = randomLSP
			for v in range(len(vehicles_info)):
				vehicles_info[v, 6] = randomLSP
			allOperators.append(randomLSP)
		uuid = input_data['general']['uuid']
	
	if event != None:
		previousPlan = input_data['previousPlan']
	else:
		previousPlan = None
	return uuid, isValid, routeDate, nOrders, nLocations, nDepots, nHubs, nMobile, nLastmile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith, mode, event, objective, eligible_types, allOperators, serviceTime, livingLab, previousPlan, timeOfEvent

def loadPreviousPlan(previousPlan, vehicles_info, vehicles_size, timeOfEvent, orders_info, locations_info):
	routes, subroutes, oldOrders = {}, {}, []
	for key in previousPlan['routes'].keys():
		for v in range(len(vehicles_info)):
			if previousPlan['routes'][key]['vehicle'] in vehicles_info[v, 0][0]:
				break
		if "mobile" in vehicles_info[v, 1]:
			routes[previousPlan['routes'][key]['vehicle']], nTrips = {}, 0
			for stop in previousPlan['routes'][key]['sequence'].keys():
				location = previousPlan['routes'][key]['sequence'][stop]['location']
				arrival = int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][4])
				departure = int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][4])
				if arrival >= timeOfEvent:	
					nTrips += 1
				pickups, deliveries, nCustomers = [], [], 0
				for n in range(len(orders_info)):
					for i in previousPlan['routes'][key]['sequence'][stop]['pickUps']:
						if orders_info[n, 9] == i:
							pickups.append(n)
							if n not in oldOrders:
								oldOrders.append(n)
							if orders_info[n, 3] == 1:
								nCustomers += 1
					for i in previousPlan['routes'][key]['sequence'][stop]['dropOffs']:
						if orders_info[n, 9] == i:
							deliveries.append(n)
							if n not in oldOrders:
								oldOrders.append(n)
							if orders_info[n, 2] == 1:
								nCustomers += 1
				numVehicles, routes[previousPlan['routes'][key]['vehicle']][nTrips] = 0, {'location': location, 'timeWindow': [arrival, departure], 'pickups': [n for n in pickups], 'deliveries': [n for n in deliveries], 'vehicles': {}, 'customers': nCustomers}
				for p in range(len(vehicles_info)):
					if "last-mile" in vehicles_info[p, 1]:
						vType = [l for l in vehicles_info[p, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
						vId = ""
						for char in vehicles_info[p, 0][0]:
							if char != "*":
								vId += char
							else:
								break
						routes[previousPlan['routes'][key]['vehicle']][nTrips]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
						numVehicles += 1
	if routes == {}:
		routes['depot'] = {}
		routes['depot'][0] = {}
		for j in range(len(locations_info)):
			if locations_info[j, 1] == "depot":
				routes['depot'][0]['location'] = locations_info[j, 0]
				break
		startTime, endTime = 24*60, 0
		for key in previousPlan['routes'].keys():
			for v in range(len(vehicles_info)):
				if previousPlan['routes'][key]['vehicle'] in vehicles_info[v, 0][0]:
					break
			for stop in previousPlan['routes'][key]['sequence'].keys():
				arrival = int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][4])
				departure = int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][4])
				if departure < startTime:
					startTime = departure
				if arrival > endTime:
					endTime = arrival
		routes['depot'][0]['timeWindow'] = [int(startTime), int(endTime)]
		routes['depot'][0]['pickups'], routes['depot'][0]['deliveries'], routes['depot'][0]['vehicles'], routes['depot'][0]['customers'], numVehicles = [], [], {}, 0, 0
		for p in range(len(vehicles_info)):
			if "last-mile" in vehicles_info[p, 1]:
				vType = [l for l in vehicles_info[p, 1] if l in ["carrier", "van", "bike", "scooter", "droid"]][0]
				vId = ""
				for char in vehicles_info[p, 0][0]:
					if char != "*":
						vId += char
					else:
						break
				if vId in subroutes.keys():
					for k in subroutes[vId].keys():
						for j in range(len(locations_info)):
							if locations_info[j, 0] == subroutes[vId][k]['location']:
								break
						if locations_info[j, 1] == "depot" and subroutes[vId][k]['timeWindow'][0] >= timeOfEvent:
							releaseTime = subroutes[vId][k]['timeWindow'][0]
							break
				routes["depot"][0]['vehicles'][str(numVehicles)] = {"id": vId, "releaseTime" : int(vehicles_info[p, 5]), "capacity1" : vehicles_size[p, 0], "capacity2" : vehicles_size[p, 1], "type": vType}
				numVehicles += 1
	
	for key in previousPlan['routes'].keys():
		for v in range(len(vehicles_info)):
			if previousPlan['routes'][key]['vehicle'] in vehicles_info[v, 0][0]:
				break
		if "last-mile" in vehicles_info[v, 1]:
			for r in routes.keys():
				for k in routes[r].keys():
					if timeOfEvent in range(routes[r][k]['timeWindow'][0], routes[r][k]['timeWindow'][1]+1):
						for l in routes[r][k]['vehicles'].keys():
							if routes[r][k]['vehicles'][l]['id'] == previousPlan['routes'][key]['vehicle']:
								subroutes[previousPlan['routes'][key]['vehicle']], nTrips = {}, 0
								for stop in previousPlan['routes'][key]['sequence'].keys():
									location = previousPlan['routes'][key]['sequence'][stop]['location']
									arrival = int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['arrivalTime'][4])
									departure = int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][0])*60*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][1])*60 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][3])*10 + int(previousPlan['routes'][key]['sequence'][stop]['departureTime'][4])
									if arrival in range(routes[r][k]['timeWindow'][0], routes[r][k]['timeWindow'][1]+1) or arrival > routes[r][k]['timeWindow'][1]:	
										for j in range(len(locations_info)):
											if locations_info[j, 0] == location:
												break
										pickups, deliveries, nCustomers = [], [], 0
										for n in range(len(orders_info)):
											for i in previousPlan['routes'][key]['sequence'][stop]['pickUps']:
												if orders_info[n, 9] == i:
													pickups.append(n)
													if n not in oldOrders:
														oldOrders.append(n)
													if orders_info[n, 3] == 1:
														nCustomers += 1
											for i in previousPlan['routes'][key]['sequence'][stop]['dropOffs']:
												if orders_info[n, 9] == i:
													deliveries.append(n)
													if n not in oldOrders:
														oldOrders.append(n)
													if orders_info[n, 2] == 1:
														nCustomers += 1
										subroutes[previousPlan['routes'][key]['vehicle']][nTrips] = {'location': location, 'timeWindow': [arrival, departure], 'pickups': [n for n in pickups], 'deliveries': [n for n in deliveries], 'vehicles': {}, 'customers': nCustomers}
										nTrips += 1
	newOrders = [n for n in range(len(orders_info)) if n not in oldOrders]

	return routes, subroutes, newOrders