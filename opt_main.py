import json
from datetime import *
import time
import warnings
import os
warnings.filterwarnings("ignore")
import pika
import sys
import traceback

import numpy as np
import pandas as pd

import opt_validation
import opt_preprocessing
import opt_orchestrator
import opt_export

online = sys.argv[1]
host = sys.argv[2]
port = sys.argv[3]
username = sys.argv[4]
password = sys.argv[5]

credentials = pika.PlainCredentials(username, password)
params = pika.ConnectionParameters(host, port, '/', credentials, heartbeat=1860, blocked_connection_timeout=930)
connection = pika.BlockingConnection(params)
channel = connection.channel()

def callback(ch, method, properties, body):
	print(datetime.now(), " - Algorithm Start.")
	raw_input_data = json.loads(body)
	print(datetime.now(), " - Data Received Successfully.")
	uuid = raw_input_data['uuid']
	input_data = raw_input_data['data']
	uuidIn = input_data['general']['uuid']
	try:
		areValid, input_data, problems = opt_validation.validation(input_data)
		if areValid:
			uuidIn, areValid, routeDate, nOrders, nLocations, nDepots, nHubs, nMobile, nLastmile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, canBeTransferredWith, mode, event, objective, eligible_types, allOperators, serviceTime, livingLab, previousPlan, timeOfEvent = opt_preprocessing.import_data(input_data)
			if areValid:
				routes, subroutes, maxOrders, newOrders = opt_orchestrator.optimizer(event, livingLab, nOrders, nLocations, nMobile, orders_info, orders_time, orders_size, locations_info, locations_time, vehicles_info, vehicles_size, travelTimes, eligible_types, serviceTime, canBeTransferredWith, objective, previousPlan, timeOfEvent)
				if routes != False:	
					solution, routes = opt_export.export_json(livingLab, vehicles_info, routes, subroutes, orders_info, orders_time, locations_info, travelTimes, uuid, maxOrders, newOrders)
					output_data = {}
					output_data['uuid'] = uuid
					output_data['produced_at'] = int(time.time() * 1000)
					output_data['data'] = solution
					output = json.dumps(output_data)
					print("Printing Routes:")
					print(output)
					channel.basic_publish(exchange='opt-result', routing_key='loc-rout', body=output)
				else:
					error_response['uuid'] = uuid
					error_response['produced_at'] = int(time.time() * 1000)
					error_response['data'] = {"message": "Infeasible solution for the provided dataset"}
					output = json.dumps(error_response)
					channel.basic_publish(exchange='opt-result', routing_key='loc-rout', body=output)
			else:
				print(f"{datetime.now()}  - Algorithm killed: Invalid data input #1.")
				problems['uuid'] = uuid
				problems['produced_at'] = int(time.time() * 1000)
				output = json.dumps(problems)
				channel.basic_publish(exchange='opt-result', routing_key='loc-rout', body=output)
				print("#1 Problems:")
				print(problems)
				print("#################################")
				print(input_data)
		else:
			print(f"{datetime.now()}  - Algorithm killed: Invalid data input #2.")
			problems['uuid'] = uuid
			problems['produced_at'] = int(time.time() * 1000)
			output = json.dumps(problems)
			channel.basic_publish(exchange='opt-result', routing_key='loc-rout', body=output)
			print("#2 Problems:")
			print(problems)
			print("#################################")
			print(input_data)
	except Exception as e:
		print(traceback.format_exc())
		error_message, error_response = {"message": str(e)}, {}
		error_response = {"uuid": uuid, "produced_at": int(time.time() * 1000), "data":error_message}
		output = json.dumps(error_response)
		channel.basic_publish(exchange='opt-result', routing_key='loc-rout', body=output)
		print(f"{datetime.now()}  - Algorithm killed: Invalid data input #3.")
		print("#3 Problems:")
		print(problems)
		print("#################################")
		print(input_data)
	folders = ["./files", "./reports", "./toPlot", "./vehicles"]
	try:
		for f in folders:
			for filename in os.listdir(f):
				if ".ttf" not in filename:
					os.remove(f"{f}/{filename}")
	except Exception:
		pass
	print(f"{datetime.now()}  - Algorithm End.")

print("Start consuming from queue")
channel.basic_consume(queue='loc-rout_job', on_message_callback=callback, auto_ack=True)
channel.start_consuming()