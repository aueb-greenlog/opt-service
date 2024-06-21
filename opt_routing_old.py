from __future__ import division
import sys
import random
import time
import math
from pyomo.environ import *
import pandas as pd
import json
import itertools
from csv import reader
import logging
logging.getLogger('pyomo.core').setLevel(logging.ERROR)
from datetime import *
import numpy as np
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(1, '.\\vrp')
import run

def solve_routing(filename, route, depot, travelTimes, locations_info, orders_info, orders_time, vehicles_info, operator, eligibleTypes, subroutes, vId, usedVehicles):
	abort = False
	try:
		listNodes, startTyping = [], False
		for j in route.keys():
			if j == depot:
				startTyping = True
			if startTyping:
				for i in range(len(locations_info)):
					if locations_info[i, 0] == route[j]["location"]:
						listNodes.append(locations_info[i, 0])
				break
		for n in route[depot]['pickups']:
			if locations_info[orders_info[n, 4], 0] != route[depot]['location']:
				listNodes.append(locations_info[orders_info[n, 4], 0])
		for n in route[depot]['deliveries']:
			if locations_info[orders_info[n, 5], 0] != route[depot]['location']:
				listNodes.append(locations_info[orders_info[n, 5], 0])
		run.execute_vrp(filename)
	except Exception:
		print(datetime.now(), " - Invalid input for the Routing component.")
		abort = True
	if abort == False:
		toPlot = ""
		for char in filename:
			if char != ".":
				toPlot += char
			else:
				toPlot += "_to_plot.txt"
				break
		try:
			with open(f"./toPlot/{toPlot}", 'r') as infile:
				trips, numVehicles = {}, 0
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
		except Exception:
			print(datetime.now(), " - Invalid input for the Routing component.")
			abort = True

		if abort == False:
			endServices = ""
			for char in filename:
				if char != ".":
					endServices += char
				else:
					endServices += "_end_service."
			timeHorizon = 0
			try:
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
			except Exception:
				print(datetime.now(), " - Invalid input for the Routing component.")
				abort = True
		
		if abort == False:
			try:
				if timeHorizon > route[depot]['timeWindow'][1]:
					delay = int(timeHorizon - route[depot]['timeWindow'][1])
					route[depot]['timeWindow'][1] += delay
				else:
					delay = 0
			except Exception:
				print(datetime.now(), " - Invalid input for the Routing component.")
				abort = True
		
		if abort == False:
			try:
				numVehicles, serviceTime = 0, 3
				for v in range(len(vehicles_info)):
					if "last-mile" in vehicles_info[v, 1] and vehicles_info[v, 6] == route[depot]['operator'] and v not in usedVehicles and numVehicles < len([key for key in route[depot]['vehicles']]):
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
							subroutes[vehicleId][nTrips] = {"location": trips[str(numVehicles)]['route'][0], "pickups": [], "deliveries": [], "timeWindow": [route[depot]['timeWindow'][0], route[depot]['timeWindow'][0]], "vehicles" : {}, "customers": 0, "operator": vehicles_info[v, 6], "duplicates": [nTrips]}
							if nTrips > 0:
								for loc1 in range(len(locations_info)):
									if locations_info[loc1, 0] == subroutes[vehicleId][nTrips-1]['location']:
										break
								for loc2 in range(len(locations_info)):
									if locations_info[loc2, 0] == subroutes[vehicleId][nTrips]['location']:
										break
								for t in range(len(eligibleTypes)):
									if eligibleTypes[t] == "carrier" and "carrier" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "bike" and "bike" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "van" and "van" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "scooter" and "scooter" in vehicles_info[v, 1]:
										break
								if subroutes[vehicleId][nTrips]['timeWindow'][0] - travelTimes[loc1, loc2, t] > subroutes[vehicleId][nTrips-1]['timeWindow'][1]:
									subroutes[vehicleId][nTrips-1]['timeWindow'][1] = int(subroutes[vehicleId][nTrips]['timeWindow'][0] - travelTimes[loc1, loc2, t])
							timeHorizon, collection, dropoff, lastStop = route[depot]['timeWindow'][0], [], [], nTrips
							for j in range(1, len(trips[str(numVehicles)]['route'])):
								arrival, departure, pickups, deliveries = 0, 0, [], []
								for loc1 in range(len(locations_info)):
									if locations_info[loc1, 0] == trips[str(numVehicles)]['route'][j-1]:
										break
								for loc2 in range(len(locations_info)):
									if locations_info[loc2, 0] == trips[str(numVehicles)]['route'][j]:
										break
								for t in range(len(eligibleTypes)):
									if eligibleTypes[t] == "carrier" and "carrier" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "bike" and "bike" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "van" and "van" in vehicles_info[v, 1]:
										break
									if eligibleTypes[t] == "scooter" and "scooter" in vehicles_info[v, 1]:
										break
								arrival = int(timeHorizon + travelTimes[loc1, loc2, t])
								departure = int(arrival + serviceTime*int(bool(locations_info[loc2, 1] == "customer")))
								if locations_info[loc2, 1] == "customer":
									for n in route[depot]['pickups']:
										if locations_info[orders_info[n, 4], 0] == trips[str(numVehicles)]['route'][j]:
											pickups.append(n)
											dropoff.append(n)
											if orders_time[n, 0] > arrival:
												departure = int(orders_time[n, 0] + serviceTime)
									for n in route[depot]['deliveries']:
										if locations_info[orders_info[n, 5], 0] == trips[str(numVehicles)]['route'][j]:
											deliveries.append(n)
											collection.append(n)
											if orders_time[n, 1] > arrival:
												departure = int(orders_time[n, 1] + serviceTime)
								timeHorizon = departure
								subroutes[vehicleId][nTrips+j] = {"location": trips[str(numVehicles)]['route'][j], "pickups": [n for n in pickups], "deliveries": [n for n in deliveries], "timeWindow": [arrival, departure], "vehicles" : {}, "customers": 0, "operator": vehicles_info[v, 6], "duplicates": [nTrips+j]}
								if locations_info[loc2, 1] == "depot" or locations_info[loc2, 1] == "hub":
									subroutes[vehicleId][lastStop]['pickups'] = [n for n in collection]
									subroutes[vehicleId][nTrips+j]['deliveries'] = [n for n in dropoff]
									collection, dropoff = [], []
									lastStop = nTrips + j
						numVehicles += 1
			except Exception:
				print(datetime.now(), " - Invalid input for the Routing component.")
				abort = True
	
	if abort == False:
		return filename, route, subroutes, delay
	else:
		return None, None, None, None