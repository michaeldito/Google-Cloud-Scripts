"""
	@file   : sendEmail.py
	@desc   : This function will send an email
	@param  :	subject (str) subject of the email
  @param  : content (any type convertable to a str) content of the email
	@param  :	from_email (str) sender of the email
  @param  : to_email (str) recipient of the email
	NOTE    : Your SENDGRID_API_KEY must be set in your environment. See their website
	for details.
"""

import sendgrid
import os
from sendgrid.helpers.mail import *
from colorama import init, Fore
from python_http_client.exceptions import UnauthorizedError

def send_email(subject, email_content, from_email, to_email):
	print('{:<70}'.format('Sending email from {} to {}'.format(from_email, to_email)), end='', flush=True),
	sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
	from_email = Email(from_email)
	to_email = Email(to_email)
	subject = subject
	content = Content("text/plain", email_content)
	mail = Mail(from_email, subject, to_email, content)
	try:
		response = sg.client.mail.send.post(request_body=mail.get())
		if response.status_code in (200, 201, 202):
			print(Fore.GREEN + '[COMPLETE]')
			print(Fore.WHITE + 'Subject: {}'.format(subject))
			print(Fore.WHITE + 'Content: {}'.format(email_content))
		else:
			print(Fore.RED + '[FAILED]')
	except UnauthorizedError:
		print(Fore.RED + '[FAILED]')
		print(Fore.CYAN + 'Did you remember to set your sendgrid api key?')