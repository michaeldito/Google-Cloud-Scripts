"""
  @file : updateLoadBalancer.py
  @desc : This script will update an nginx load balancer's upstream, and proxy_pass settings.
  @arg  : project (str): name of the google cloud project the load balancer is in.
  @arg  : zone (str): The name of the zone the load balancer is in.
  @arg  : lb_name (str): The name of the load balancer.
  @arg  : proxy (str): The name of the proxy route.

  Example:
  >>> python3 updateLoadBalancer.py project zone lb_name proxy
"""

from controller import Controller
from argparse import ArgumentParser
from colorama import init, Fore
import os

def create_upstream(controller, upstream_name):
  """
  This function will generate the upstream data that will be uploaded to the load balancer.
  Args:
    controller (obj): An instantiated Controller object
    upstream_name (str): The name of the upstream route
  Returns:
    str: the upstream data
  """
  running_ips = controller.get_all_running_rest_server_internal_ips()
  if len(running_ips) == 0:
    running_ips.append('00.000.0.00')
  upstream = 'upstream ' + upstream_name + ' { '
  for ip in running_ips:
    upstream += ' server ' + ip + ';'
  upstream += ' }'
  return upstream

def update_load_balancer_upstream(controller, zone, lb_name, proxy):
  """
  This function will update an nginx load balancer in a Google Cloud project.
  Specifically, it will update it's upstream, and then reload nginx so that the
  changes take effect.
  Args:
    controller (obj): An instantiated Controller object
    zone (str): The name of the zone the load balancer is in
    lb_name (str): The name of the load balancer
    proxy (str): The name of the proxy route
  Returns:
    Nothing
  """
  # First we need our IPs and our data
  print('Preparing to update {} upstream'.format(lb_name))
  #	Make sure the load balancer is on, if not turn it on
  lb_data = controller.get_instance_data(zone, lb_name)
  if lb_data['status'] != 'RUNNING':
    print('{:<70}'.format('{} was off, starting it now ... '.format(lb_name)), end='', flush=True),
    operation = controller.start_instance(lb_name, zone)
    result = controller.wait_for_operation(operation)
    if result['status'] == 'DONE':
      print(Fore.GREEN + '[COMPLETE]')
  # Now get the data we need
  print('{:<70}'.format('Fetching {} external IP address ... '.format(lb_name)), end='', flush=True),
  lb_external_ip = controller.get_external_ip(zone, lb_name)
  print(Fore.GREEN + '[COMPLETE]')
  print('{:<70}'.format('Creating upstream and proxy_pass data ... '), end='', flush=True),
  upstream_data = create_upstream(controller, proxy)
  print(Fore.GREEN + '[COMPLETE]')
  # Edit a local file to send to nginx
  print('{:<70}'.format('Creating nginx/sites-available/default file ... '), end='', flush=True),
  os.system("sed -i -e \'s/upstream_data/" + upstream_data + "/g\' default")
  os.system("sed -i -e \'s/proxy_data/" + proxy + "/g\' default")
  print(Fore.GREEN + '[COMPLETE]')
  print('Preparing to scp sites-available/default file to {}'.format(lb_name))
  # Now use gcloud to send it
  os.system('gcloud compute scp default root@loadbalancer-0:/etc/nginx/sites-available/default --zone us-central1-c')
  # Now ssh into the load balancer, and reload nginx
  print('Reloading nginx on {}'.format(lb_name))
  os.system('gcloud compute ssh {} --zone {} --command \"sudo service nginx reload\"'.format(lb_name, zone))
  # Change our local file back to a template
  os.system("cp default.backup default")
  print('{:<70}'.format('{} updates ...'.format(lb_name)), end='', flush=True),
  print(Fore.GREEN + '[COMPLETE]')

def main(project, zone, lb, proxy):
  init(autoreset=True)
  controller = Controller(project)
  update_load_balancer_upstream(controller, zone, lb, proxy)

if __name__ == '__main__':
  parser = ArgumentParser(description='This script will update the upstream and proxy_pass of an \
  nginx load balancer in a Google Cloud project.')
  parser.add_argument("project", help="the name of your google cloud project")
  parser.add_argument("zone", help="the zone your load balancer is located in")
  parser.add_argument("lb_name", help="the name of your load balancer instance")
  parser.add_argument("proxy", help="the route you want to proxy requests too")
  args = parser.parse_args()
  main(args.project, args.zone, args.lb_name, args.proxy)
