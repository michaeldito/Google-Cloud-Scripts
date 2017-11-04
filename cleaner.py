'''
    Author      : Mike Dito
    Class       : CS 385
    Assignment  : Midterm
    File        : cleaner.py
    Description : This script will shut down all running rest servers that are
				  not labeled as persistent. Once these servers are shut down,
				  an email will be sent with the names of these servers.
'''

import sendgrid
import os
import argparse
import sys

from sendgrid.helpers.mail import *
from controller import Controller
from colorama import init, Fore
from python_http_client.exceptions import UnauthorizedError

def sendEmail(project, instances):
	sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
	fromEmail = Email("mcdito13@gmail.com")
	toEmail = Email("mcdito13@gmail.com")
	subject = project + ' Instances Shut Down'
	content = Content("text/plain", str(instances))
	mail = Mail(fromEmail, subject, toEmail, content)
	try:
		response = sg.client.mail.send.post(request_body=mail.get())
		if response.status_code == 202:
			print(Fore.GREEN + '[DONE]')
		else:
			print(Fore.RED + '[FAILED]')
	except UnauthorizedError:
		print(Fore.RED + '[FAILED]')
		print(Fore.CYAN + 'Did you remember to set your sendgrid api?')


def shutDownAllRestServers(project):
	c = Controller(project)
	print('{:<50}'.format('Getting non-persistent running servers ...'), end='', flush=True)
	running = c.getRunningNonPersistentRestServers()
	print(Fore.GREEN + '[DONE]')
	print('Beginning to shutdown instances ...')
	serversShutDown = []
	for instance in running:
		print('Shutting down ' + instance['name'])
		zone = instance['zone'].rsplit('/', 1)[-1]
		instance = instance['name']
		operation = c.stopInstance(instance, zone)
		result = c.waitForOperation(operation)
		if result['status'] == 'DONE':
			print(instance)
			serversShutDown.append(instance)
	return serversShutDown

def main(project, email):
	init(autoreset=True)
	serversShutDown = shutDownAllRestServers(project)
	if email:
		print('{:<50}'.format('Sending email ...'), end='', flush=True)
		sendEmail(project, serversShutDown)
	print('Exiting cleaner.py')

if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="This script will shut down all rest servers not labeled as persistent in the project specified")
	parser.add_argument("project", help="the name of your google cloud project")
	parser.add_argument("-e", "--email", help="send an email containing the names of servers shut down", action="store_true")
	args = parser.parse_args()
	main(args.project, args.email)
