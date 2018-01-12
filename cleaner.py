"""
	@file : cleaner.py
	@desc : This script has the ability to shut down servers in a Google Cloud Project. There are
	a few different ways to shut down servers. These options can be selected by using arguments
	when calling the script.

	@arg  : project (str) [required] name of the google cloud project
	@arg  : -all (flag) provide this argument to shut down all servers
	@arg  : -rest (flag) provide this argument to shut down all REST servers
	@arg  : -np_rest (flag) provide this argument to shut down all REST servers not labeled as persistent
	NOTE  : Only choose one option out of (-all, -rest, -np_rest)
	@arg  :	-e  (flag) [optional] indicates an email will be sent with names of servers shut down
	@arg  : -fr (flag) [optional] [required if -e is true] should precede the senders email address
	@arg  : -to (flag) [optional] [required if -e is true] should precede the recipients email address
	NOTE  : If -e option is indicated, then -fr and -to are required	

	Examples:
	>>> python3 cleaner.py project -all
	>>> python3 cleaner.py project -rest
	>>> python3 cleaner.py project -np_rest
	>>> python3 cleaner.py project -all -e -fr sender@gmail.com -to recipient@gmail.com
"""

from googlecloudclient import GoogleCloudClient
from argparse import ArgumentParser
from sys import argv
from colorama import init, Fore
from sendEmail import *

def shut_down_servers(client, servers):
	"""
	This function will shut down all instances within the argument list object, servers.
	Args:
		client (obj): An instantiated GoogleCloudClient object
		servers (list) (json): see the following link
		https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
	Returns:
		list (str): The names of the servers that have been shut down
	"""
	servers_shut_down = []
	for instance in servers:
		print('{:<70}'.format('Shutting down {} ...'.format(instance['name'])), end='', flush=True),
		zone_name = instance['zone'].rsplit('/', 1)[-1]
		instance_name = instance['name']
		operation = client.stop_instance(instance_name, zone_name)
		result = client.wait_for_operation(operation)
		if result['status'] == 'DONE':
			print(Fore.GREEN + '[COMPLETE]')
			servers_shut_down.append(instance_name)
	print('{:<70}'.format('Shutdown status'), end='', flush=True),
	print(Fore.GREEN + '[COMPLETE]')
	return servers_shut_down

def main(project, all, rest, non_persistent_rest, email, from_email, to_email):
	init(autoreset=True)
	client = GoogleCloudClient(project)
	if all:
		print('Beginning to shut down all servers in {}'.format(project))
		servers_to_shut_down = client.get_instances('RUNNING')
	elif rest:
		print('Beginning to shut down all REST servers in {}'.format(project))
		servers_to_shut_down = client.get_rest_servers('RUNNING')
	elif non_persistent_rest:
		print('Beginning to shut down all non persistent REST servers in {}'.format(project))
		servers_to_shut_down = client.get_running_rest_servers_without_label('persistent', 'true')
	servers_shut_down = shut_down_servers(client, servers_to_shut_down)
	if email:
		send_email(project + ' Instances Shut Down', str(servers_shut_down), from_email, to_email)

if __name__ == "__main__":
	parser = ArgumentParser(
		description='This script will shut down all REST servers not labeled as persistent in \
		a Google Cloud project - with an option to send an email containing the names of the  \
		servers shut down ')
	parser.add_argument('project', help='the name of your google cloud project')
	parser.add_argument('-all', help='flag to indicate all servers in project will be shut down', action='store_true')
	parser.add_argument('-rest', help='flag to indicate all REST servers will be shut down', action='store_true')
	parser.add_argument('-np_rest', help='flag to indicate all non-persistent REST servers will be shut down', action='store_true')
	parser.add_argument('-e', help='flag to send an email containing the names of servers shut down', action='store_true')
	parser.add_argument('-fr', required='-e' in argv, help='sender email')
	parser.add_argument('-to', required='-e' in argv, help='recipient email')
	args = parser.parse_args()
	main(args.project, args.all, args.rest, args.np_rest, args.e, args.fr, args.to)
