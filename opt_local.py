import json
from datetime import *
import time
import warnings
import os
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import opt_validation
import opt_preprocessing
import opt_orchestrator
import opt_export

if __name__ == "__main__":
	print(datetime.now(), " - Algorithm Start.")
	file = open(f'./instances/ox_daily.json', encoding='utf-8')
	input_data = json.load(file)
	input_data = input_data['data']
	print(datetime.now(), " - Data Received Successfully.")
	uuid = input_data['general']['uuid']
	#try:
	areValid, input_data, problems = opt_validation.validation(input_data)
	if areValid:
		uuid, areValid, routeDate, nOrders, nLocations, nDepots, nHubs, nMobile, nLastmile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith, mode, event, objective, eligible_types, allOperators, serviceTime, livingLab, previousPlan, timeOfEvent = opt_preprocessing.import_data(input_data)
		if areValid:
			routes, subroutes, maxOrders, newOrders = opt_orchestrator.optimizer(event, livingLab, nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, eligible_types, serviceTime, canBeTransferredWith, objective, previousPlan, timeOfEvent)
			if routes != False:	
				solution, routes = opt_export.export_json(livingLab, vehicles_info, routes, subroutes, orders_info, orders_time, locations_info, travelTimes, uuid, maxOrders, newOrders)
				output_data = {}
				output_data['uuid'] = uuid
				output_data['produced_at'] = int(time.time() * 1000)
				output_data['data'] = solution
				#output = json.dumps(output_data)
				filename = f"optOutput.json"
				with open(filename, 'w') as outfile:
					json.dump(output_data, outfile, indent = 4)
				'''
				json_dict, definition = opt_export.aimsun_json(livingLab, routeDate, vehicles_info, routes, orders_info, locations_info)
				filename = f"fleet_schedule.json"
				with open(filename, 'w') as outfile:
					json.dump(json_dict, outfile, indent = 4)
				filename = f"operator_definition.json"
				with open(filename, 'w') as outfile:
					json.dump(definition, outfile, indent = 4)
				
				od_dict = {'Origin': {}, 'Destination': {}}
				numPair = 0
				for i in range(nLocations):
					for j in range(nLocations):
						if i != j:
							od_dict['Origin'][numPair] = locations_info[i, 0]
							od_dict['Destination'][numPair] = locations_info[j, 0]
							numPair += 1
				od = pd.DataFrame(od_dict)
				filename = "od_list.xlsx"
				od.to_excel(filename)
				'''
			else:
				error_message, error_response = {"message": "Infeasible solution for the provided dataset"}, {}
				error_response['general'], error_response['routes'] = {"uuid": uuid, "produced_at": int(time.time() * 1000)}, error_message
				#error_response = json.dumps(error_response)
				filename = f"optOutput.json"
				with open(filename, 'w') as outfile:
					json.dump(error_response, outfile, indent = 4)
		else:
			print(f"{datetime.now()}  - Algorithm killed: Invalid data input.")
			problems['general']['uuid'] = uuid
			problems['general']['producedAt'] = int(time.time() * 1000)
			#output = json.dumps(problems)
			filename = f"optOutput.json"
			with open(filename, 'w') as outfile:
				json.dump(problems, outfile, indent = 4)
	else:
		print(f"{datetime.now()}  - Algorithm killed: Invalid data input.")
		problems['general']['uuid'] = uuid
		problems['general']['producedAt'] = int(time.time() * 1000)
		#output = json.dumps(problems)
		filename = f"optOutput.json"
		with open(filename, 'w') as outfile:
			json.dump(problems, outfile, indent = 4)
	'''
	except Exception as e:
		print(f"{datetime.now()}  - Algorithm killed: Invalid data input.")
		error_message, error_response = {"message": str(e)}, {}
		error_response['general'], error_response['routes'] = {"uuid": uuid, "produced_at": int(time.time() * 1000)}, error_message
		#error_response = json.dumps(error_response)
		filename = f"optOutput.json"
			with open(filename, 'w') as outfile:
				json.dump(error_response, outfile, indent = 4)
	'''
	folders = ["./files", "./reports", "./toPlot", "./vehicles"]
	try:
		for f in folders:
			for filename in os.listdir(f):
				os.remove(f"{f}/{filename}")
	except Exception:
		pass
	print(f"{datetime.now()}  - Algorithm End.")
	