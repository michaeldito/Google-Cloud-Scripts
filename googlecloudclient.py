"""
	@file : googlecloudclient.py
	@desc : The GoogleCloudClient class provides a number of methods that can be used to interact with a project hosted
	on the Google Cloud Platform. It's attribute 'compute' provides access to the GCP API, and many methods
	will use it. The purpose of this class is to provide the ability to retreive data about the instances
	within the project.

	Example:
	>>> client = GoogleCloudClient('project-name')
"""

import googleapiclient.discovery
import time
import os

class GoogleCloudClient:	
	
	def __init__(self, project):
		""" 
		The constructor will initialize the compute attribute, establishing a connection to the GCP API, and
		set the project name.
		Args:
			project (str): The project name
		"""

		self.project = project
		self.compute = googleapiclient.discovery.build('compute', 'v1')
	
	def get_zone_names_list(self):
		""" 
		This function will return a list of the names of all zones.
		Returns: list (str): ['asia-east1-c', 'us-central1-c', ... ]
		"""

		return [zone['description'] for zone in self.compute.zones().list(project=self.project).execute()['items']] 

	def get_instances_in_zone(self, zone):
		""" 
		This function will return a list of json data for all instances in a specific zone.
		Args:
			zone (str): The name of the zone to search for instances in
		Example:
		>>> c.get_instances_in_zone('us-central1-c')
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
		"""
		
		try:
			instances = self.compute.instances().list(project=self.project, zone=zone).execute()['items']
		except KeyError:
			instances = []
		return instances

	def get_instance_data(self, zone, instance):
		"""
		This function will return all data associated with an instance.
		Args:
			zone (str): The name of the zone the instance is in
			instance (str): The name of the instance
		Example:
		>>> c.get_instance_data('us-central1-c', 'lab03-controller')
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#get
		"""

		return self.compute.instances().get(project=self.project, zone=zone, instance=instance).execute()

	def get_all_instances(self):
		"""
		This function will return a list data about all instances in the project.
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
		"""

		instances_in_all_zones = [self.get_instances_in_zone(zone) for zone in self.get_zone_names_list()]
		flattened_instances = [instance for instance_list in instances_in_all_zones for instance in instance_list if len(instance) != 0]
		return flattened_instances
 
	def get_instances(self, status):
		"""
		This function will return a list of instances with a specific status.
		Args:
			status (str): The status of the instance. It can be one of the following:
			PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, TERMINATED
		Example:
		>>> c.get_instances('RUNNING')
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
		"""

		return [instance for instance in self.get_all_instances() if instance['status'] == status]

	def get_instance_name_list(self):
		"""
		This function will return a list of the names of all instances in the project.
		Returns:
			list (str): ['lab03-controller', 'loadbalancer-0', 'restserver-0', ... ]
		"""

		return [instance['name'] for instance in self.get_all_instances()]

	def get_rest_servers(self, status):
		"""
		This function will return a list of data about all rest servers with a specific status.
		Args:
			status (str): The status of the instance. It can be one of the following:
			PROVISIONING, STAGING, RUNNING, STOPPING, STOPPED, SUSPENDING, SUSPENDED, TERMINATED
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
		"""

		return [instance for instance in self.get_instances(status) if 'restserver' in instance['name']]
	
	def get_running_rest_servers_without_label(self, label, value):
		"""
		This function will return a list of data about all rest servers that are running, that also 
		do not have a specific value for a provided label.
		Args:
			label (str): The label to look for
			value (str): The value the label should not have
		Example:
		>>> c.get_running_rest_servers_without_label('persistent', 'true')
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
		"""

		running = self.get_rest_servers('RUNNING')
		servers = []
		for i in running:
			if 'labels' not in i:
				servers.append(i)
			if 'labels' in i and label in i['labels'] and i['labels'][label] != value:
				servers.append(i)
		return servers

	def get_oldest_running_rest_server(self):
		"""
		This function will return a json object containing data about the oldest running rest server in 
		the project.
		Returns:
			list (json): see the following link
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.zoneOperations.html#list
		"""

		running = self.get_rest_servers('RUNNING')
		running_names = [instance['name'] for instance in running]
		running_start_times = [self.get_instance_operations(instance, 'start') for instance in running]
		# Since we may have newly created instances running (that do not have a start operation yet)
		# Make a list containing the oldest start operation for each instance that has one
		oldest_start_operations = [instance['items'][-1] for instance in running_start_times if 'items' in instance]
		running_names_with_start_operation = [instance['targetLink'].rsplit('/', 1)[-1] for instance in oldest_start_operations]
		# Make a list containing instances that do not have a start operation
		no_start_operations = [instance for instance in running if instance['name'] not in running_names_with_start_operation]
		# Now get the insert operations for those instances
		insert_times = [self.get_instance_operations(instance, 'insert') for instance in no_start_operations]
		# Now add insert operations for the newly created instances to the oldest start operation list
		for instance in insert_times:
			oldest_start_operations.append(instance['items'][0])
		# We can now determine the oldest running instance
		oldest = oldest_start_operations[0]
		for instance in oldest_start_operations:
			if instance['startTime'] < oldest['startTime']:
				oldest = instance
		return oldest
		
	def get_all_running_rest_server_internal_ips(self):
		"""
		This function will return a list of internal ip addresses for all running rest servers in the project.
		Returns:
			list (str): ['10.128.0.5']
		"""

		return [instance['networkInterfaces'][0]['networkIP'] for instance in self.get_instances('RUNNING') if 'restserver' in instance['name']]

	def get_external_ip(self, zone, instance):
		"""
		This function will return the external ip address for a specific instance in the project.
		Args:
			zone (str): The zone the instance is located in
			instance (str): The name of the instance
		Returns:
			str: The external ip address of the instance
		Example:
		>>> c.get_external_ip('us-central1-c', 'restserver-2')
		'35.193.133.78'
		"""

		data = self.get_instance_data(zone, instance)
		return data['networkInterfaces'][0]['accessConfigs'][0]['natIP']

	def get_count_of_servers_with_name(self, server_name):
		"""
		This function will return the number of servers that contain server_name as a substring of its name.
		Args:
			server_name (str): The name to search for
		Returns:
			int: The number of instances that contain server_name as a substring of their names
		Example:
		>>> c.get_count_of_servers_with_name('restserver')
		5
		"""

		return [name.count(server_name) for name in self.get_instance_name_list()].count(1)

	def get_operations_in_zone(self, zone):
		"""
		This function will return data about recent operations in a specific zone.
		Args:
			zone (str): The name of the zone to look for operations in
		Returns:
			dict: Details about operations in the zone
		Example:
		>>> c.get_operations_in_zone('us-central1-c')
		https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.zoneOperations.html#list
		"""

		return self.compute.zoneOperations().list(project=self.project, zone=zone).execute()

	def get_instance_operations(self, instance_json, operation_type):
		"""
		This function will return operation data for a specific instance, and a specific operation type.
		Args:
			instance_json (json): Information about the instance. Input should match the following link:
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#list
			operation_type (str): The operation type
		Example:
			* see get_oldest_running_rest_server()
		Returns:
			dict: Details about operations in the zone
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.zoneOperations.html#list
		"""

		zone = instance_json['zone'].rsplit('/', 1)[-1]
		instance_id = instance_json['id']
		filter_by = '(targetId eq '+instance_id+')(operationType eq '+operation_type+')'
		return self.compute.zoneOperations().list(project=self.project, zone=zone, filter=filter_by).execute()

	def get_operation_result(self, operation):
		"""
		This function will return the result of an operation.
		Args:
			operation (json): Data about the operation
		Returns:
			dict: details about the operation
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.zoneOperations.html#get
		"""

		zone = operation['zone'].rsplit('/',1)[-1]
		return self.compute.zoneOperations().get(project=self.project, zone=zone, operation=operation['name']).execute()

	def wait_for_operation(self, operation):
		"""
		This function will wait for a provided operation to finish, and report any errors if they occur.
		Args:
			operation (json): Data about the current operation
		Example:
			* see scale.py
		Returns:
			dict: Details about the operation
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.zoneOperations.html#get
		"""

		while True:
			result = self.get_operation_result(operation)
			if result['status'] == 'DONE':
				if 'error' in result:
					raise Exception(result['error'])
				return result
			time.sleep(1)

	def start_instance(self, name, zone):
		"""
		This function will start an instance.
		Args:
			name (str): The name of the instance to start
			zone (str): The zone it is located in
		Returns:
			dict: Details about the operation
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#start
		"""
		return self.compute.instances().start(project=self.project, zone=zone, instance=name).execute()

	def stop_instance(self, name, zone):
		"""
		This function will stop an instance.
		Args:
			name (str): The name of the instance to stop
			zone (str): The zone it is located in
		Returns:
			dict: Details about the operation
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#start
		"""

		return self.compute.instances().stop(project=self.project, zone=zone, instance=name).execute()

	def create_instance_from_image(self, my_image, zone):
		"""
		This function will create a new instance, from a previously made image, in a specific zone.
		It will attach to the instance a startup script named 'startup.sh' that should be located
		in the project directory.
		Args:
			my_image (str): The name of the image to use
			zone (str): The name of the zone to create the instance in
		Returns:
			dict: Details about the operation
			https://developers.google.com/resources/api-libraries/documentation/compute/v1/python/latest/compute_v1.instances.html#insert
		"""

		# Get the image requested
		image = self.compute.images().get(project=self.project, image=my_image).execute()
		source_disk_image = image['selfLink']
		
		# Configure the machine
		machine_type = 'zones/' + zone + '/machineTypes/f1-micro'

		# Read in the startup-script
		startup_script = open('startup.sh', 'r').read()

		# Setup the config
		config = {
			'name': 'restserver-'+str(self.get_count_of_servers_with_name('restserver')),
			'machineType': machine_type,

			'tags': {
				'items': [
					'http-server',
					'https-server'
				]
			},

			# Specify the boot disk and the image to use as a source
			'disks': [
				{
					'boot': True,
					'autoDelete': True,
					'initializeParams': {
						'sourceImage': source_disk_image,
					},
					'deviceName':'restserver-'+str(self.get_count_of_servers_with_name('restserver'))
				}
			],
		
			# Specify a network interface with NAT to acces the public internet
			'networkInterfaces': [{
				'network': 'global/networks/default',
				'accessConfigs': [
					{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
				]
			}],

			# Allow the instance to acces cloud storage and logging
			'serviceAccounts': [{
				'email': 'default',
				'scopes': [
					'https://www.googleapis.com/auth/devstorage.read_write',
					'https://www.googleapis.com/auth/logging.write'
				]
			}],

			# Metadata is readable from the instance and allows you to pass configuration
			# from deployment scripts to instances
			'metadata': {
				'items': [{
					# Startup script is automatically executed by the instance upon startup
					'key': 'startup-script',
					'value': startup_script
				}]
			}	
		}
	
		# Now create the instace and return it
		return self.compute.instances().insert(project=self.project, zone=zone, body=config).execute()
