#!/usr/bin/python3

'''
   Author      : Mike Dito
   Class       : CS 385
   Assignment  : Lab 03
   File        : scale.py
   Description : This script contains a function 'scale' which, given a Google Cloud project,
				 zone, and instanceCount, will scale that projects servers to the number provided
				 by instanceCount. Zone is used as the default zone for creating instances.
   Parameters  : [1] project: string, name of the google cloud project
				 [2] zone: string, name of default zone for creating a server
				 [3] instanceCount: int, number to scale the servers to
'''

from controller import Controller
from random import randint
from googleapiclient.errors import HttpError
from argparse import ArgumentParser

def needToScaleDown(instanceCount, numRunningInstances):
	return instanceCount < numRunningInstances

def needToScaleUp(instanceCount, numRunningInstances):
	return instanceCount > numRunningInstances

def doneScaling(instanceCount, numRunningInstnaces):
	return instanceCount == numRunningInstances

def stillNeedToScale(instanceCount, numRunningInstances):
	return instanceCount != numRunningInstances

def scale(project, instanceCount, zone):
	if instanceCount > 10:
		print('You may only scale up to 10 instances. Exiting...')
		return
	print('Scaling project \'' + project + '\' to ' + str(instanceCount) + ' restservers')
	c = Controller(project)
	runningRests = c.getRestServers('RUNNING')
	numRunningRests = len(runningRests)
	print('There are ' + str(numRunningRests) + ' currently running')
	if needToScaleUp(instanceCount, numRunningRests):
		print('Scaling up...')
		stoppedRests = c.getRestServers('TERMINATED')
		while stillNeedToScale(instanceCount, numRunningRests):
			if len(stoppedRests) > 0: # Do we have any servers we can start?
				instanceToStart = stoppedRests.pop()
				zoneName = instanceToStart['zone'].rsplit('/', 1)[-1]
				instance = instanceToStart['name']
				start = c.startInstance(instance, zoneName)
				runningRests.append(start)
				numRunningRests += 1
				print(start['targetLink'].rsplit('/', 1)[-1] + ' has been started')
			else: # No servers are available to start, create one
				try:
					create = c.createInstanceFromImage('lab02-restserver', zone)
				except HttpError:
					print('Cannot create instance in ' + zone + '. It has reached it\'s quota.')
					print('Choosing alternate zone...')
					zones = c.getZoneNamesList()
					altZone = zones[randint(0, len(zones) - 1)]
					print('Selected ' + altZone + ' as the alternate zone')
				else:
					numRunningRests += 1
					print(create['targetLink'].rsplit('/', 1)[-1] + ' has been created')
	if needToScaleDown(instanceCount, numRunningRests):
		print('Scaling down...')
		while stillNeedToScale(instanceCount, numRunningRests):
			instanceToStop = c.getOldestRunningInstance()
			zoneName = instanceToStop['zone'].rsplit('/', 1)[-1]
			instance = instanceToStop['targetLink'].rsplit('/', 1)[-1]
			stop = c.stopInstance(instance, zoneName)
			numRunningRests -= 1
			print(stop['targetLink'].rsplit('/',1)[-1] + ' has been stopped')
	print('Updating Load Balancer...')
	c.updateLoadBalancerUpstream()
	print('Scaling complete!')

def main(project, instanceCount, zone):
	scale(project, instanceCount, zone)

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument("project", help="the name of your google cloud project")
	parser.add_argument("instanceCount", help="the number of instances to scale to")
	parser.add_argument("zone", help="the zone to create an instance in, if needed")
	args = parser.parse_args()
	main(args.project, int(args.instanceCount), args.zone)