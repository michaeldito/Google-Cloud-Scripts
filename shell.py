#!/usr/bin/python3

'''
   Author      : Mike Dito
   Class       : CS 385
   Assignment  : Lab 03
   File        : shell.py
   Description : The following class uses the paramiko library to implement a shell that can be used
		 to execute commands on another server. Paramiko implements SSHv2 protocol, providing
		 client and server functionality.
'''

import paramiko, socket, time

class ssh:
	shell = None
	client = None

	def __init__(self, address, username, password):
		print('Connecting to ' + username + '@' + address)
		self.client = paramiko.client.SSHClient()
		self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
		try:
			self.client.connect(address, username=username, password=password, timeout=10.0)
		except socket.timeout as err:
			print('Connection timed out. Check the hostname, username, and password')
		else:
			print('Connected')

	# closeConnection: This function will close the SSH connection.
	def closeConnection(self):
		if self.client != None:
			self.client.close()
			print('Connection closed')
		else:
			print('Connection was never opened. Closing failed.')

  	# openShell: Used to invoke the ssh shell with the host and credentials defined
  	# on initialization
	def openShell(self):
		self.shell = self.client.invoke_shell()

  	# sendShell: Used to send a command to the shell.
	def sendShell(self, command):
		if self.shell:
			self.shell.send(command + '\n')
		else:
			print('Shell not opened.')

# runCommandsInShell: Given a username, password, server address, and a list of commands,
# this function will create a connection to tha server, open a shell, and enter each command.
def runCommandsInShell(name, password, serverAddress, commands):
	sshUsername = name
	sshPassword = password
	sshServer = serverAddress

	connection = ssh(sshServer, sshUsername, sshPassword)
	connection.openShell()
	for command in commands:
		print(command)
		if command == 'logout':
			connection.closeConnection()
			return
		connection.sendShell(command)
		time.sleep(1.5)
