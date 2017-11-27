'''
	@file   : scale.py
	@desc   : This script will scale a Google Cloud Project's rest servers to @param:instance_count.
	@param  : project (str) name of the google cloud project.
	@param  :	instance_count (int) number of servers to scale to.
	@param  :	zone (str) name of default zone for creating a server.

	Example:
	>>> python3 scale.py project instance_count zone
'''

from controller import Controller
from random import randint
from googleapiclient.errors import HttpError
from argparse import ArgumentParser
from colorama import init, Fore
from updateLoadBalancer import *

def need_to_scale_down(instance_count, num_running_instances):
	return instance_count < num_running_instances

def need_to_scale_up(instance_count, num_running_instances):
	return instance_count > num_running_instances

def done_scaling(instance_count, num_running_instances):
	return instance_count == num_running_instances

def still_need_to_scale(instance_count, num_running_instances):
	return instance_count != num_running_instances

def scale(project, instance_count, zone):
	"""
	This function will scale a Google Cloud project horizontally, so that instance_count
	number of instances are running.
	Args:
		project (str): The name of the GCP project
		instance_count (int): The number of instances to scale to
		zone (str): If an instance needs to be created, it will be in this zone
	Returns:
		Nothing
	"""
	if instance_count > 10:
		print(Fore.CYAN + 'You may only scale up to 10 instances. Exiting ...')
		return

	print('Scaling project {} to {} rest servers'.format(project, str(instance_count)))
	c = Controller(project)
	print('{:<70}'.format('Searching for running REST servers ...'), end='', flush=True),
	running_rest_servers = c.get_rest_servers('RUNNING')
	print(Fore.GREEN + '[COMPLETE]')
	num_running_rest_servers = len(running_rest_servers)
	print('REST servers running: {}'.format(str(num_running_rest_servers)))

	if need_to_scale_up(instance_count, num_running_rest_servers):
		print('Scaling up ...')
		print('{:<70}'.format('Searching for stopped REST servers ...'), end='', flush=True),
		stopped_rest_servers = c.get_rest_servers('TERMINATED')
		print(Fore.GREEN + '[COMPLETE]')
		while still_need_to_scale(instance_count, num_running_rest_servers):
			if len(stopped_rest_servers) > 0: # Do we have any servers we can start?
				instance_to_start = stopped_rest_servers.pop()
				zone_name = instance_to_start['zone'].rsplit('/', 1)[-1]
				instance_name = instance_to_start['name']
				print('{:<70}'.format('Starting {}'.format(instance_name)), end='', flush=True),
				operation = c.start_instance(instance_name, zone_name)
				result = c.wait_for_operation(operation)
				if result['status'] == 'DONE':
					print(Fore.GREEN + '[COMPLETE]')
					num_running_rest_servers += 1
				else:
					print(Fore.RED + '[FAILED]')
			else: # No servers are available to start, create one
				print('All stopped REST servers have been started'),
				print('{:<70}'.format('Creating a new REST server in {} ...'.format(zone)), end='', flush=True),
				try:
					operation = c.create_instance_from_image('lab02-restserver', zone)
					result = c.wait_for_operation(operation)
				except HttpError:
					print(Fore.YELLOW + '[WARNING]')
					print(Fore.CYAN + 'Cannot create instance in {}. It has reached it\'s quota.'.format(zone))
					print('{:<70}'.format('Choosing alternate zone ... '), end='', flush=True),
					zones = c.get_zone_names_list()
					zone = zones[randint(0, len(zones) - 1)]
					print(Fore.GREEN + '[COMPLETE]')
					print('Selected {} as the alternate zone'.format(zone))
				else:
					if result['status'] == 'DONE':
						print(Fore.GREEN + '[COMPLETE]')
						num_running_rest_servers += 1

	if need_to_scale_down(instance_count, num_running_rest_servers):
		print('Scaling down ...')
		while still_need_to_scale(instance_count, num_running_rest_servers):
			print('{:<70}'.format('Searching for the longest running server ...'), end='', flush=True),
			instance_to_stop = c.get_oldest_running_rest_server()
			print(Fore.GREEN + '[COMPLETE]')
			zone_name = instance_to_stop['zone'].rsplit('/', 1)[-1]
			instance_name = instance_to_stop['targetLink'].rsplit('/', 1)[-1]
			print('{:<70}'.format('Stopping {}'.format(instance_name)), end='', flush=True),
			operation = c.stop_instance(instance_name, zone_name)
			result = c.wait_for_operation(operation)
			if result['status'] == 'DONE':
				print(Fore.GREEN + '[COMPLETE]')
				num_running_rest_servers -= 1

	print('Initializing upstream update on nginx load balancer')
	update_load_balancer_upstream(c, 'us-central1-c', 'loadbalancer-0', 'fibonacci')
	print('{:<70}'.format('Scaling project {} to {} rest servers ...'.format(project, str(instance_count))), end='', flush=True),
	print(Fore.GREEN + '[COMPLETE]')

def main(project, instance_count, zone):
	init(autoreset=True)
	scale(project, instance_count, zone)

if __name__ == "__main__":
	parser = ArgumentParser(description='This script will scale a Google Cloud project\'s rest servers \
	so that instance_count number of servers are running.')
	parser.add_argument('project', help='The name of your google cloud project')
	parser.add_argument('instance_count', help='The number of instances to scale to')
	parser.add_argument('zone', help='The zone to create an instance in, if needed')
	args = parser.parse_args()
	main(args.project, int(args.instance_count), args.zone)