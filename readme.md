# Google Cloud Scripts
These are a few python scripts I developed for interacting with a project hosted on the Google Cloud Platform. For examples on how to use each script, check the documentation at the top of each python file.

## Important
In order to use these scripts, you must do a few things first:
- [Create a Google Cloud Project](https://cloud.google.com/resource-manager/docs/creating-managing-projects)
- Create an API key (From the GCP console navigate to: APIs & Services > Credentials > Create credentials > Service account key). Save this key in in a safe place, and then export it to your .bash_profile with `echo "export GOOGLE_APPLICATION_CREDENTIALS=~/<location-of-key>" > ~/.bash_profile`
- [Install gcloud](https://cloud.google.com/sdk/downloads)
- To send emails when using cleaner.py (optional), make a free account with [SendGrid](https://sendgrid.com/), and download your api key to your working directory
- All of these scripts use python3, this should also be installed
- Install all requirements used in these scripts with `pip3 install -r requirements.txt`

## controller.py
The Controller class provides a number of methods that can be used to interact with a project hosted on the Google Cloud Platform. It's attribute 'compute' provides access to the GCP API, and many methods of the class will use it. The purpose of this class is to provide the ability to retreive data about the instances within the project, and to later use this data to control the state of the project.

### Things to note about controller.py:
If you are going to modify this class to your needs, these are a few lines of code you should be aware of.

controller.py 284 `create_instance_from_image(self, my_image, zone)`  
This function requires an image name as an argument.   
controller.py 304 `startup_script = open('startup.sh', 'r').read()`  
When creating a new instance, a startup bash script should be in your working directory.  
controller.py 307 `'name': 'restserver-'+str(self.get_count_of_servers_with_name('restserver')),`  
When your instance is created, this will be it's name.

## scale.py

This script can be used to scale a project's servers to N number of instances. In order to scale up, an image must be saved of your server. To create an image, navigate to:

Compute Engine > Images > Create Image

Then select your Source Disk, and hit Create.  
scale.py 76: `operation = c.create_instance_from_image('lab02-restserver', zone)`  
If you wish to use your image, you must update the first parameter here.

Note: If you are updating the load balancer after scaling your instances down to 0 an error will arise. By executing `systemctl status nginx.service` on the load balancer, the following error message will be shown:

**nginx[2110]: nginx: [emerg] no servers are inside upstream in /etc/nginx/sites-enabled/default:1**

To work around this, in updateLoadBalancer.py I added the following code:
`if len(running_ips) == 0:`
  `running_ips.append('00.000.0.00')`
This may not be the best practice, but it works around the issue.


## updateLoadBalancer.py
This script will update an nginx load balancer's upstream, and proxy_pass settings.

## sendEmail.py
This file contains a single function that will send an email using the sendgrid library.