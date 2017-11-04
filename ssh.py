from paramiko import client
import socket

class ssh:
  client = None

  def __init__(self, address, username, password):
    print('Connecting to ' + username + '@' + address)
    self.client = client.SSHClient()
    # If you want the script to be able to access a server that's not yet in
    # the known_hosts file, do this
    self.client.set_missing_host_key_policy(client.AutoAddPolicy())
    try:
      self.client.connect(address, username=username, password=password, timeout=5.0)
    except socket.timeout as err:
      print('Connection timed out. Check the hostname, username, and password')
    else:
      print('Connected.')

  def sendCommand(self, command):
    if self.client:
      stdin, stdout, stderr = self.client.exec_command(command)
      # Check if the command was invalid
      if stdout.channel.recv_exit_status():
        for line in stderr:
          print line
      else:
        print('Command complete.')
    else:
      print('Connection not opened.')

  def close(self):
    self.client.close()
    print('Connection closed.')
