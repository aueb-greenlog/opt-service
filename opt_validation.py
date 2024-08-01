from datetime import datetime, date, timedelta
import warnings
warnings.filterwarnings("ignore")
from datetime import *

def validation(input_data):
	problems = {}
	problems['general'], problems['routes'] = {}, {}
	problems['general']['fileFormat'], problems['general']['missingFields'] = [], []
	print(datetime.now(), " - Start of Data Validation.")
	if isinstance(input_data, dict):
		if "general" in input_data.keys():
			if "date" in input_data['general'].keys():
				startDate = input_data['general']['date']
				try:
					startDate = datetime.strptime(startDate, '%d-%m-%Y')
				except Exception as e:
					problems['general']['fileFormat'].append(f"Invalid format: {startDate} should be of type string (dd-mm-YY)")
			else:
				problems['general']['missingFields'].append("Missing field: 'date'")
			if "livingLab" in input_data['general'].keys():
				livingLab = input_data['general']['livingLab']
				if livingLab not in ["Athens, Greece", "Barcelona, Spain", "Flanders, Belgium", "Ispra, Italy", "Oxford, England", "Terrassa, Spain"]:
					problems['general']['fileFormat'].append(f"Invalid format: {livingLab} should be one of ['Athens, Greece', 'Barcelona, Spain', 'Flanders, Belgium', 'Ispra, Italy', 'Oxford, England', 'Terrassa, Spain'].")
			else:
				problems['general']['missingFields'].append("Missing field: 'livingLab'")
			if "service" in input_data['general'].keys():
				if "mode" in input_data['general']['service'].keys():
					service = input_data['general']['service']['mode']
					if service not in ["daily", "eventTriggered"]:
						problems['general']['fileFormat'].append(f"Invalid format: {service} should be one of ['daily', 'eventTriggered'].")
					elif service == "eventTriggered":
						if "event" in input_data['general']['service'].keys():
							event = input_data['general']['service']['event']
							if event not in ["new-request", "unavailable-vehicle"]:
								problems['general']['fileFormat'].append(f"Invalid format: {event} should be one of ['new-request', 'unavailable-vehicle'].")
						else:
							problems['general']['missingFields'].append("Missing field: 'event' from 'service'")
						if "time" in input_data['general']['service'].keys():
							tensHour, hour, tensMin, min = input_data['general']['service']['time'][0], input_data['general']['service']['time'][1], input_data['general']['service']['time'][3], input_data['general']['service']['time'][4]
							try:
								tensHour, hour, tensMin, min = int(tensHour), int(hour), int(tensMin), int(min)
							except Exception:
								problems['general']['fileFormat'].append(f"Invalid format: {hour} should have a format of 'HH:MM'.")
						else:
							problems['general']['missingFields'].append("Missing field: 'time' from 'service'")
				else:
					problems['general']['missingFields'].append("Missing field: 'mode' in 'service'")
			else:
				problems['general']['missingFields'].append("Missing field: 'service'")
			if "objective" in input_data['general'].keys():
				objective = input_data['general']['objective']
				if objective not in ["min-travelTime"]:
					input_data['general']['objective'] = "min-travelTime"
			else:
				input_data['general']['objective'] = "min-travelTime"
			if "availableBefore" in input_data['general'].keys():
				availableBefore = input_data['general']['availableBefore']
				try:
					availableBefore = datetime.strptime(availableBefore, '%d-%m-%Y %H:%M:%S')
				except Exception as e:
					problems['general']['fileFormat'].append(f"Invalid format: {availableBefore} should be of type string (dd-mm-YY HH:MM:SS)")
			else:
				problems['general']['missingFields'].append("Missing field: 'availableBefore'")
		else:
			problems['general']['missingFields'].append("Missing field: 'general'")
		locations = []
		if "locations" in input_data.keys():
			for key in input_data['locations'].keys():
				if isinstance(input_data['locations'][key], dict):
					if "tags" in input_data['locations'][key].keys():
						if input_data['locations'][key]['tags'] not in ['customer', 'depot', 'hub']:
							problems['general']['fileFormat'].append(f"Invalid format: location {key} should be a 'depot', a 'customer', or a 'hub'.")
					else:
						problems['general']['missingFields'].append(f"Missing field: 'tags' for location {key}")
					if "coordinates" in input_data['locations'][key].keys():
						if isinstance(input_data['locations'][key]['coordinates'], dict):
							if "x" in input_data['locations'][key]['coordinates'].keys():
								try:
									test = input_data['locations'][key]['coordinates']['x']/1.0
								except Exception:
									problems['general']['fileFormat'].append(f"Invalid format: 'x' coordinate of location {key} is non-numeric.")
							else:
								problems['general']['missingFields'].append(f"Missing field: 'x' coordinate for location {key}")
							if "y" in input_data['locations'][key]['coordinates'].keys():
								try:
									test = input_data['locations'][key]['coordinates']['y']/1.0
								except Exception:
									problems['general']['fileFormat'].append(f"Invalid format: 'y' coordinate of location {key} is non-numeric.")
							else:
								problems['general']['missingFields'].append(f"Missing field: 'y' coordinate for location {key}")
						else:
							problems['general']['fileFormat'].append(f"Invalid format: 'coordinates' of location {key} is not a dictionary.")
					else:
						problems['general']['missingFields'].append(f"Missing field: 'coordinates' for location {key}")
					if "operatingHours" in input_data['locations'][key].keys():
						if isinstance(input_data['locations'][key]['operatingHours'], dict):
							if "start" in input_data['locations'][key]['operatingHours'].keys():
								try:
									test = int(input_data['locations'][key]['operatingHours']['start'][0])
									test = int(input_data['locations'][key]['operatingHours']['start'][1])
									test = int(input_data['locations'][key]['operatingHours']['start'][3])
									test = int(input_data['locations'][key]['operatingHours']['start'][4])
									if input_data['locations'][key]['operatingHours']['start'][2] != ":":
										problems['general']['fileFormat'].append(f"Invalid format: 'start' hour of location {key} should be of type string (HH:MM).")
								except Exception:
									problems['general']['fileFormat'].append(f"Invalid format: 'start' hour of location {key} should be of type string (HH:MM).")
							else:
								problems['general']['missingFields'].append(f"Missing field: 'start' hour for location {key}")
							if "end" in input_data['locations'][key]['operatingHours'].keys():
								try:
									test = int(input_data['locations'][key]['operatingHours']['end'][0])
									test = int(input_data['locations'][key]['operatingHours']['end'][1])
									test = int(input_data['locations'][key]['operatingHours']['end'][3])
									test = int(input_data['locations'][key]['operatingHours']['end'][4])
									if input_data['locations'][key]['operatingHours']['end'][2] != ":":
										problems['general']['fileFormat'].append(f"Invalid format: 'end' hour of location {key} should be of type string (HH:MM).")
								except Exception:
									problems['general']['fileFormat'].append(f"Invalid format: 'end' hour of location {key} should be of type string (HH:MM).")
							else:
								problems['general']['missingFields'].append(f"Missing field: 'end' hour for location {key}")
						else:
							problems['general']['fileFormat'].append(f"Invalid format: 'operatingHours' of location {key} is not a dictionary.")
					else:
						problems['general']['missingFields'].append(f"Missing field: 'operatingHours' for location {key}")
					locations.append(key)
				else:
					problems['general']['fileFormat'].append(f"Invalid format: location {key} is not a dictionary.")
		else:
			problems['general']['missingFields'].append("Missing field: 'locations'")
		if "orders" in input_data.keys():
			validatedKeys, reRun = [], True
			while reRun:
				reRun = False
				for key in input_data['orders'].keys():
					if key not in validatedKeys:
						if "operator" not in input_data['orders'][key]:
							print(datetime.now(), f" - WARNING: Order {key} has no operator - it will be ignored.")
							del input_data['orders'][key]
							validatedKeys.append(key)
							break
						if "operation" not in input_data['orders'][key]:
							print(datetime.now(), f" - WARNING: Order {key} has no operations - it will be ignored.")
							del input_data['orders'][key]
							validatedKeys.append(key)
							break
						else:
							if isinstance(input_data['orders'][key]['operation'], list):
								isInvalid = False
								for operation in input_data['orders'][key]['operation']:
									if operation not in ["Delivery", "Pickup", "Click-and-Collect"]:
										isInvalid = True
										break
								if isInvalid or len(input_data['orders'][key]['operation']) == 0:
									print(datetime.now(), f" - WARNING: Unknown 'operation' for {key} - it will be ignored.")
									del input_data['orders'][key]
									validatedKeys.append(key)
									break
							else:
								print(datetime.now(), f" - WARNING: Format of 'operation' for {key} is invalid - it will be ignored.")
								del input_data['orders'][key]
								validatedKeys.append(key)
								break
						if "parcels" not in input_data['orders'][key]:
							print(datetime.now(), f" - WARNING: Order {key} has no parcels - it will be ignored.")
							del input_data['orders'][key]
							validatedKeys.append(key)
							break
						else:
							isInvalid = False
							if isinstance(input_data['orders'][key]['parcels'], dict):
								for num in input_data['orders'][key]['parcels'].keys():
									if isinstance(input_data['orders'][key]['parcels'][num], dict):
										if "weight" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['weight'] = 0.0
										else:
											try:
												test = input_data['orders'][key]['parcels'][num]['weight']/1.0
											except Exception:
												print(datetime.now(), f" - WARNING: Order {key} has a non-numeric weight value - it will be ignored.")
												isInvalid = True
												break
										if "volume" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['volume'] = 0.0
										else:
											try:
												test = input_data['orders'][key]['parcels'][num]['volume']/1.0
											except Exception:
												print(datetime.now(), f" - WARNING: Order {key} has a non-numeric volume value - it will be ignored.")
												isInvalid = True
												break
										if "length" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['length'] = 0.0
										else:
											try:
												test = input_data['orders'][key]['parcels'][num]['length']/1.0
											except Exception:
												print(datetime.now(), f" - WARNING: Order {key} has a non-numeric length value - it will be ignored.")
												isInvalid = True
												break
										if "width" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['width'] = 0.0
										else:
											try:
												test = input_data['orders'][key]['parcels'][num]['width']/1.0
											except Exception:
												print(datetime.now(), f" - WARNING: Order {key} has a non-numeric width value - it will be ignored.")
												isInvalid = True
												break
										if "height" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['height'] = 0.0
										else:
											try:
												test = input_data['orders'][key]['parcels'][num]['height']/1.0
											except Exception:
												print(datetime.now(), f" - WARNING: Order {key} has a non-numeric height value - it will be ignored.")
												isInvalid = True
												break
										if "tags" not in input_data['orders'][key]['parcels'][num].keys():
											input_data['orders'][key]['parcels'][num]['tags'] = []
									else:
										print(datetime.now(), f" - WARNING: Parcels of order {key} have invalid format - it will be ignored.")
										isInvalid = True
										break
								if isInvalid:
									del input_data['orders'][key]
									validatedKeys.append(key)
									break
							else:
								print(datetime.now(), f" - WARNING: Invalid format for order {key} - it will be ignored.")
								del input_data['orders'][key]
								validatedKeys.append(key)
								break
						if "location" not in input_data['orders'][key].keys():
							print(datetime.now(), f" - WARNING: Order {key} has no location - it will be ignored.")
							del input_data['orders'][key]
							validatedKeys.append(key)
							break
						else:
							isInvalid = False
							if isinstance(input_data['orders'][key]['location'], dict):
								if "Pickup" in input_data['orders'][key]['location'].keys():
									if input_data['orders'][key]['location']["Pickup"] not in locations:
										print(datetime.now(), f" - WARNING: Invalid pickup location for order {key} - it will be ignored.")
										del input_data['orders'][key]
										validatedKeys.append(key)
										break
								else:
									print(datetime.now(), f" - WARNING: Order {key} has no pickup location - it will be ignored.")
									del input_data['orders'][key]
									validatedKeys.append(key)
									break
								if "Delivery" in input_data['orders'][key]['location'].keys():
									if input_data['orders'][key]['location']["Delivery"] not in locations:
										print(datetime.now(), f" - WARNING: Invalid delivery location for order {key} - it will be ignored.")
										del input_data['orders'][key]
										validatedKeys.append(key)
										break
								else:
									print(datetime.now(), f" - WARNING: Order {key} has no delivery location - it will be ignored.")
									del input_data['orders'][key]
									validatedKeys.append(key)
									break
							else:
								print(datetime.now(), f" - WARNING: Invalid format for order {key} - it will be ignored.")
								del input_data['orders'][key]
								validatedKeys.append(key)
								break
						if "availableAfter" in input_data['orders'][key].keys():
							try:
								test = int(input_data['orders'][key]['availableAfter'][0])
								test = int(input_data['orders'][key]['availableAfter'][1])
								test = int(input_data['orders'][key]['availableAfter'][3])
								test = int(input_data['orders'][key]['availableAfter'][4])
								if input_data['orders'][key]['availableAfter'][2] != ":":
									print(datetime.now(), f" - WARNING: 'availableAfter' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
									del input_data['orders'][key]
									validatedKeys.append(key)
									break
							except Exception:
								print(datetime.now(), f" - WARNING: 'availableAfter' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
								del input_data['orders'][key]
								validatedKeys.append(key)
								break
						else:
							input_data['orders'][key]['availableAfter'] = "07:00"
						if "timeWindow" in input_data['orders'][key].keys():
							if isinstance(input_data['orders'][key]['timeWindow'], dict):
								if "After" in input_data['orders'][key]['timeWindow'].keys():
									try:
										test = int(input_data['orders'][key]['timeWindow']['After'][0])
										test = int(input_data['orders'][key]['timeWindow']['After'][1])
										test = int(input_data['orders'][key]['timeWindow']['After'][3])
										test = int(input_data['orders'][key]['timeWindow']['After'][4])
										if input_data['orders'][key]['timeWindow']['After'][2] != ":":
											print(datetime.now(), f" - WARNING: 'After' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
											del input_data['orders'][key]
											validatedKeys.append(key)
											break
									except Exception:
										print(datetime.now(), f" - WARNING: 'After' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
										del input_data['orders'][key]
										validatedKeys.append(key)
										break
								else:
									input_data['orders'][key]['timeWindow']["After"] = "07:00"
								if "Before" in input_data['orders'][key]['timeWindow'].keys():
									try:
										test = int(input_data['orders'][key]['timeWindow']['Before'][0])
										test = int(input_data['orders'][key]['timeWindow']['Before'][1])
										test = int(input_data['orders'][key]['timeWindow']['Before'][3])
										test = int(input_data['orders'][key]['timeWindow']['Before'][4])
										if input_data['orders'][key]['timeWindow']['Before'][2] != ":":
											print(datetime.now(), f" - WARNING: 'Before' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
											del input_data['orders'][key]
											validatedKeys.append(key)
											break
									except Exception:
										print(datetime.now(), f" - WARNING: 'Before' hour of order {key} should be of type string (HH:MM) - it will be ignored.")
										del input_data['orders'][key]
										validatedKeys.append(key)
										break
								else:
									input_data['orders'][key]['timeWindow']["Before"] = "19:00"
						else:
							input_data['orders'][key]["timeWindow"] = {"After": "07:00", "Before": "19:00"}
						if "canBeTransferredWith" in input_data['orders'][key].keys():
							if isinstance(input_data['orders'][key]['canBeTransferredWith'], list):
								pass
							else:
								print(datetime.now(), f" - WARNING: 'canBeTransferredWith' of order {key} should be a list - it will be ignored.")
								del input_data['orders'][key]
								validatedKeys.append(key)
								break
						else:
							input_data['orders'][key]['canBeTransferredWith'] = []
		else:
			problems['general']['missingFields'].append("Missing field: 'orders'")
		if "vehicles" in input_data.keys():
			types = []
			for key in input_data['vehicles'].keys():
				if "operator" not in input_data['vehicles'][key].keys():
					problems['general']['missingFields'].append(f"Missing field: 'operator' of vehicle {key}")
				if "tags" in input_data['vehicles'][key].keys():
					if isinstance(input_data['vehicles'][key]['tags'], list):
						if "mobile" not in input_data['vehicles'][key]['tags'] and "last-mile" not in input_data['vehicles'][key]['tags']:
							problems['general']['fileFormat'].append(f"Invalid format: 'tags' of vehicle {key} should include 'mobile' or 'last-mile'.")
						if "bike" not in input_data['vehicles'][key]['tags'] and "carrier" not in input_data['vehicles'][key]['tags'] and "van" not in input_data['vehicles'][key]['tags'] and "scooter" not in input_data['vehicles'][key]['tags'] and "droid" not in input_data['vehicles'][key]['tags']:
							problems['general']['fileFormat'].append(f"Invalid format: 'tags' of vehicle {key} should include 'bike' or 'carrier' or 'van' or 'scooter' or 'droid'.")
						else:
							if "bike" in input_data['vehicles'][key]['tags'] and "bike" not in types:
								types.append("bike")
							if "carrier" in input_data['vehicles'][key]['tags'] and "carrier" not in types:
								types.append("carrier")
							if "scooter" in input_data['vehicles'][key]['tags'] and "scooter" not in types:
								types.append("scooter")
							if "van" in input_data['vehicles'][key]['tags'] and "van" not in types:
								types.append("van")
							if "droid" in input_data['vehicles'][key]['tags'] and "droid" not in types:
								types.append("droid")
					else:
						problems['general']['fileFormat'].append(f"Invalid format: 'tags' of vehicle {key} should be a list.")
				else:
					problems['general']['missingFields'].append(f"Missing field: 'tags' of vehicle {key}")
				if "CO2_emissions" in input_data['vehicles'][key].keys():
					try:
						test = input_data['vehicles'][key]['CO2_emissions']/1.0
					except Exception:
						problems['general']['fileFormat'].append(f"Invalid format: 'CO2_emissions' of vehicle {key} is non-numeric.")
				else:
					problems['general']['missingFields'].append(f"Missing field: 'CO2_emissions' of vehicle {key}")
				if "capacity" in input_data['vehicles'][key].keys():
					if isinstance(input_data['vehicles'][key]['capacity'], list):
						for compartment in range(len(input_data['vehicles'][key]['capacity'])):
							if isinstance(input_data['vehicles'][key]['capacity'][compartment], dict):
								if "maxWeight" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['maxWeight']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'maxWeight' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['maxWeight'] = 2000
								if "maxLength" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['maxLength']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'maxLength' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['maxLength'] = 2000
								if "maxWidth" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['maxWidth']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'maxWidth' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['maxWidth'] = 2000
								if "maxHeight" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['maxHeight']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'maxHeight' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['maxHeight'] = 2000
								if "maxVolume" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['maxVolume']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'maxVolume' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['maxVolume'] = 2000
								if "numParcels" in input_data['vehicles'][key]['capacity'][compartment].keys():
									try:
										test = input_data['vehicles'][key]['capacity'][compartment]['numParcels']/1.0
									except Exception:
										problems['general']['fileFormat'].append(f"Invalid format: 'numParcels' of vehicle {key} is non-numeric.")
								else:
									input_data['vehicles'][key]['capacity'][compartment]['numParcels'] = 2000
							else:
								problems['general']['fileFormat'].append(f"Invalid format: compartments of vehicle {key} should be dictionaries.")
					else:
						problems['general']['fileFormat'].append(f"Invalid format: 'capacity' of vehicle {key} should be a list.")
				else:
					problems['general']['missingFields'].append(f"Missing field: 'capacity' of vehicle {key}")
				if "maxTime" in input_data['vehicles'][key].keys():
					try:
						test = input_data['vehicles'][key]['maxTime']/1.0
					except Exception:
						problems['general']['fileFormat'].append(f"Invalid format: 'maxTime' of vehicle {key} is non-numeric.")
				else:
					input_data['vehicles'][key]['maxTime'] = 24*60
				if "currentLocation" in input_data['vehicles'][key].keys():
					if input_data['vehicles'][key]['currentLocation'] not in locations:
						problems['general']['fileFormat'].append(f"Invalid format: 'currentLocation' of vehicle {key} is not provided.")
				else:
					problems['general']['missingFields'].append(f"Missing field: 'currentLocation' of vehicle {key}")
				if "availableAfter" in input_data['vehicles'][key].keys():
					try:
						test = int(input_data['vehicles'][key]['availableAfter'][0])
						test = int(input_data['vehicles'][key]['availableAfter'][1])
						test = int(input_data['vehicles'][key]['availableAfter'][3])
						test = int(input_data['vehicles'][key]['availableAfter'][4])
						if input_data['vehicles'][key]['availableAfter'][2] != ":":
							problems['general']['fileFormat'].append(f"Invalid format: 'availableAfter' hour of vehicle {key} should be of type string (HH:MM).")
					except Exception:
						problems['general']['fileFormat'].append(f"Invalid format: 'availableAfter' hour of vehicle {key} should be of type string (HH:MM).")
				else:
					input_data['vehicles'][key]['availableAfter'] = "07:00"
		else:
			problems['general']['missingFields'].append("Missing field: 'vehicles'")
		if service == "eventTriggered":
			if "previousPlan" in input_data.keys():
				if "routes" in input_data['previousPlan'].keys():
					if isinstance(input_data['previousPlan']['routes'], dict):
						reRun, validatedKeys = True, []
						while reRun:
							reRun = False
							for key in input_data['previousPlan']['routes'].keys():
								if key not in validatedKeys:
									if "vehicle" not in input_data['previousPlan']['routes'][key].keys() or "sequence" not in input_data['previousPlan']['routes'][key].keys():
										print(datetime.now(), f" - WARNING: route {key} is invalid - it will be ignored.")
										del input_data['previousPlan']['routes'][key]
										reRun = True
										break
									else:
										if input_data['previousPlan']['routes'][key]['vehicle'] not in input_data['vehicles'].keys():
											print(datetime.now(), f" - WARNING: vehicle {input_data['previousPlan']['routes'][key]['vehicle']} is not valid - it will be ignored.")
											del input_data['previousPlan']['routes'][key]
											reRun = True
											break
										else:
											if isinstance(input_data['previousPlan']['routes'][key]['sequence'], dict) == False:
												problems['general']['fileFormat'].append(f"Invalid format: 'sequence' of route {key} should be a dictionary.")
											else:
												for stop in input_data['previousPlan']['routes'][key]['sequence'].keys():
													if isinstance(input_data['previousPlan']['routes'][key]['sequence'][stop], dict) == False:
														problems['general']['fileFormat'].append(f"Invalid format: stop {stop} of route {key} should be a dictionary.")
													else:
														if "location" not in input_data['previousPlan']['routes'][key]['sequence'][stop].keys():
															print(datetime.now(), f" - WARNING: stop {stop} of route {key} has no location - it will be ignored.")
															del input_data['previousPlan']['routes'][key]
															reRun = True
															break
														else:
															if input_data['previousPlan']['routes'][key]['sequence'][stop]['location'] not in locations:
																print(datetime.now(), f" - WARNING: location of stop {stop} of route {key} is invalid - it will be ignored.")
																del input_data['previousPlan']['routes'][key]
																reRun = True
																break
															else:
																if "arrivalTime" not in input_data['previousPlan']['routes'][key]['sequence'][stop].keys() or "departureTime" not in input_data['previousPlan']['routes'][key]['sequence'][stop].keys():
																	print(datetime.now(), f" - WARNING: stop {stop} of route {key} has no scheduled times - it will be ignored.")
																	del input_data['previousPlan']['routes'][key]
																	reRun = True
																	break
																else:
																	try:
																		arrivalTime, departureTime = input_data['previousPlan']['routes'][key]['sequence'][stop]['arrivalTime'], input_data['previousPlan']['routes'][key]['sequence'][stop]['departureTime']
																		arrivalMinutes = int(arrivalTime[0])*10*60 + int(arrivalTime[1])*60 + int(arrivalTime[3])*10 + int(arrivalTime[4])
																		departureMinutes = int(departureTime[0])*10*60 + int(departureTime[1])*60 + int(departureTime[3])*10 + int(departureTime[4])
																	except Exception:
																		problems['general']['fileFormat'].append(f"Invalid format: times of stop {stop} in route {key} are invalid.")
																	if departureMinutes < arrivalMinutes:
																		print(datetime.now(), f" - WARNING: stop {stop} of route {key} is invalid - it will be ignored.")
																		del input_data['previousPlan']['routes'][key]
																		reRun = True
																		break
																	else:
																		if "pickUps" not in input_data['previousPlan']['routes'][key]['sequence'][stop].keys() or "dropOffs" not in input_data['previousPlan']['routes'][key]['sequence'][stop].keys():
																			print(datetime.now(), f" - WARNING: stop {stop} of route {key} has no associated orders - it will be ignored.")
																			del input_data['previousPlan']['routes'][key]
																			reRun = True
																			break
																		else:
																			if isinstance(input_data['previousPlan']['routes'][key]['sequence'][stop]['pickUps'], list) == False or isinstance(input_data['previousPlan']['routes'][key]['sequence'][stop]['dropOffs'], list) == False:	
																				print(datetime.now(), f" - WARNING: 'pickUps' and 'dropOffs' of stop {stop} in route {key} should be lists - they will be ignored.")
																				del input_data['previousPlan']['routes'][key]
																				reRun = True
																				break
																			else:
																				reOrder = True
																				while reOrder:
																					reOrder = False
																					for n in input_data['previousPlan']['routes'][key]['sequence'][stop]['pickUps']:
																						if n not in input_data['orders'].keys():
																							print(datetime.now(), f" - WARNING: order {n} is invalid - it will be ignored.")
																							input_data['previousPlan']['routes'][key]['sequence'][stop]['pickUps'].remove(n)
																							reOrder = True
																							break
																					if reOrder == False:
																						for n in input_data['previousPlan']['routes'][key]['sequence'][stop]['dropOffs']:
																							if n not in input_data['orders'].keys():
																								print(datetime.now(), f" - WARNING: order {n} is invalid - it will be ignored.")
																								input_data['previousPlan']['routes'][key]['sequence'][stop]['dropOffs'].remove(n)
																								reOrder = True
																								break
												if reRun:
													break												
									validatedKeys.append(key)																							
					else:
						problems['general']['fileFormat'].append(f"Invalid format: 'routes' of the previous plan should be a dictionary.")
				else:
					problems['general']['missingFields'].append("Missing field: 'routes'")
			else:
				problems['general']['missingFields'].append("Missing field: 'previousPlan'")
	else:
		problems['general']['fileFormat'].append("Invalid format")

	for key in locations:
		if "travelTime" in input_data['locations'][key].keys():
			if isinstance(input_data['locations'][key]['travelTime'], dict):
				for t in types:
					if t in input_data['locations'][key]['travelTime'].keys():
						if isinstance(input_data['locations'][key]['travelTime'][t], dict):
							for key2 in input_data['locations'][key]['travelTime'][t].keys():
								try:
									test = input_data['locations'][key]['travelTime'][t][key2]/1.0
								except Exception:
									input_data['locations'][key]['travelTime'][t][key2] = None
						else:
							#problems['general']['fileFormat'].append(f"Invalid format: 'travelTime' of location {key} for type '{t}' should be a dictionary.")
							print(datetime.now(), f" - WARNING: 'travelTime' of location {key} for type '{t}' should be a dictionary.")
					else:
						input_data['locations'][key]['travelTime'][t] = {}
						for key2 in locations:
							input_data['locations'][key]['travelTime'][t][key2] = None
			else:
				#problems['general']['fileFormat'].append(f"Invalid format: 'travelTime' of location {key} should be a dictionary.")
				print(datetime.now(), f" - WARNING: 'travelTime' of location {key} should be a dictionary.")
		else:
			#problems['general']['missingFields'].append(f"Missing field: 'travelTime' of location {key}.")
			pass

	areValid = True
	for key in problems['general'].keys():
		if len(problems['general'][key]) > 0:
			areValid = False
			break
	
	return areValid, input_data, problems