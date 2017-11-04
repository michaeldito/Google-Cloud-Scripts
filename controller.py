#!/usr/bin/python3
'''
    Author      : Mike Dito
    Class       : CS 385
    Assignment  : Lab 03
    File        : controller.py
    Description : This class provides a number of methods that can be used to interact with a project hosted
                  on the Google Cloud Platform. It provides methods for starting, stopping, and creating
		  		  REST servers. It also has a method that will update the load balancer used in this project.
		  		  That method will use a shell to log into the server, execute a list of commands, and then
		  		  log out. The shell is described in the shell.py file.
'''

import googleapiclient.discovery
import shell
import time

class Controller:	
	
	def __init__(self, project):
		self.project = project
		self.compute = googleapiclient.discovery.build('compute', 'v1')
	
	# Zone functions
	def getZoneNamesList(self):
		return [zone['description'] for zone in self.compute.zones().list(project=self.project).execute()['items']] 

	def getInstancesInZone(self, zone):
		try:
			instances = self.compute.instances().list(project=self.project, zone=zone).execute()['items']
		except KeyError:
			instances = []
		return instances

	# Instances functions
	def getAllInstances(self):
		instancesInAllZones = [self.getInstancesInZone(zone) for zone in self.getZoneNamesList()]
		flattenedInstances = [instance for instanceList in instancesInAllZones for instance in instanceList if len(instance) != 0]
		return flattenedInstances

	def getInstances(self, status):
		return [instance for instance in self.getAllInstances() if instance['status'] == status]

	def getInstanceNameList(self):
		return [instance['name'] for instance in self.getAllInstances()]

	# Rest Server functions
	def getRestServers(self, status):
		return [instance for instance in self.getInstances(status) if 'restserver' in instance['name']]
	
	def getRunningNonPersistentRestServers(self):
		running = self.getRestServers('RUNNING')
		servers = []
		for i in running:
			if 'labels' not in i:
				servers.append(i)
			if 'labels' in i and 'persistent' in i['labels'] and i['labels']['persistent'] != 'true':
				servers.append(i)
		return servers

	def getOldestRunningInstance(self):
		running = self.getRestServers('RUNNING')
		runningNames = [instance['name'] for instance in running]
		runningStartTimes = [self.getInstanceOperations(instance, 'start') for instance in running]
		# Since we may have newly created instances running (that do not have a start operation yet)
		# Make a list containing the oldest start operation for each instance that has one
		oldestStartOps = [instance['items'][-1] for instance in runningStartTimes if 'items' in instance]
		runningNamesWithStartOp = [instance['targetLink'].rsplit('/', 1)[-1] for instance in oldestStartOps]
		# Make a list containing instances that do not have a start operation
		noStartOp = [instance for instance in running if instance['name'] not in runningNamesWithStartOp]
		# Now get the insert operations for those instances
		insertTimes = [self.getInstanceOperations(instance, 'insert') for instance in noStartOp]
		# Now add insert operations for the newly created instances to the oldest start operation list
		for instance in insertTimes:
			oldestStartOps.append(instance['items'][0])
		# We can not determine the oldest running instance
		oldest = oldestStartOps[0]
		for instance in oldestStartOps:
			if instance['startTime'] < oldest['startTime']:
				oldest = instance
		return oldest
		
	# Internal/External IP functions
	def getAllRestServerInternalIPs(self):
		return [instance['networkInterfaces'][0]['networkIP'] for instance in self.getInstances('RUNNING') if 'restserver' in instance['name']]

	def getLoadBalancerExternalIP(self):
		return [instance['networkInterfaces'][0]['accessConfigs'][0]['natIP'] for instance in self.getInstances('RUNNING') if 'loadbalancer' in instance['name']][0]

	# Function used when naming new rest servers
	def getCountOfServersWithName(self, serverName):
		return [name.count(serverName) for name in self.getInstanceNameList()].count(1)

	# Operations functions
	def getOperationsInZone(self, z):
		return self.compute.zoneOperations().list(project=self.project, zone=z).execute()

	def getInstanceOperations(self, instanceJSON, opType):
		zone = instanceJSON['zone'].rsplit('/', 1)[-1]
		instanceId = instanceJSON['id']
		filterBy = '(targetId eq '+instanceId+')(operationType eq '+opType+')'
		return self.compute.zoneOperations().list(project=self.project, zone=zone, filter=filterBy).execute()

	def getOperationResult(self, operation):
		zone = operation['zone'].rsplit('/',1)[-1]
		return self.compute.zoneOperations().get(project=self.project, zone=zone, operation=operation['name']).execute()

#	def getServersAvailableWithName(self, name):
#		return [instance for instance in self.getInstances('TERMINATED') if name in instance['disks'][0]['deviceName']]
	
	def waitForOperation(self, operation):
		print('{:<50}'.format('Waiting for operation to finish ...'), end='', flush=True),
		while True:
			result = self.getOperationResult(operation)
			if result['status'] == 'DONE':
				print(Fore.CYAN + '[DONE]')
				if 'error' in result:
					raise Exception(result['error'])
				return result
			time.sleep(1)

	def startInstance(self, name, zone):
		return self.compute.instances().start(project=self.project, zone=zone, instance=name).execute()

	def stopInstance(self, name, zone):
		return self.compute.instances().stop(project=self.project, zone=zone, instance=name).execute()

	def createInstanceFromImage(self, myImage, zone):
		# Get the image requested
		image = self.compute.images().get(project=self.project, image=myImage).execute()
		sourceDiskImage = image['selfLink']
		
		# Configure the machine
		machineType = 'zones/' + zone + '/machineTypes/f1-micro'

		# Read in the startup-script
		startupScript = open('startup.sh', 'r').read()

		# Setup the config
		config = {
			'name': 'restserver-'+str(self.getCountOfServersWithName('restserver')),
			'machineType': machineType,

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
						'sourceImage': sourceDiskImage,
					},
					'deviceName':'restserver-'+str(self.getCountOfServersWithName('restserver'))
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
					'value': startupScript
				}]
			}	
		}
	
		# Now create the instace and return it
		return self.compute.instances().insert(project=self.project, zone=zone, body=config).execute()

	def getUpdatedUpstream(self):
		runningIPs = self.getAllRestServerInternalIPs()
		upstream = 'upstream fibonacci { '
		for ip in runningIPs:
			upstream += ' server ' + ip + ';'
		upstream += ' }'
		return upstream

	def updateLoadBalancerUpstream(self):
		# First we need our IPs and our data
		print('Getting Load Balancer IP and upstream data')
		loadBalancerExtIP = self.getLoadBalancerExternalIP()
		updatedData = self.getUpdatedUpstream()
		# Get file names
		print('Getting file names needed')
		defaultFile = "/etc/nginx/sites-available/default"
		replaceFile = "/etc/nginx/sites-available/replace"
		replaceBackup = "/etc/nginx/sites-available/replace.backup"
		# Create commands needed
		print('Creating commands')
		updateUpstream = "sudo sed -i -e \'s/REPLACE_THIS/" + updatedData + "/g\' "+ replaceFile + ""
		updateDefault = "sudo cp " + replaceFile + " " + defaultFile + ""
		copyReplaceBackup = "sudo cp " + replaceBackup + " " + replaceFile + ""
		reloadNginx = "sudo service nginx reload"
		logout = "logout"
		# Put commands in a list, then run those commands on the LB server
		print('Executing commands')
		commands = [updateUpstream, updateDefault, copyReplaceBackup, reloadNginx, logout]
		shell.runCommandsInShell('mdito', None, loadBalancerExtIP, commands)
