#!/usr/bin/python

import subprocess
import xml.etree.ElementTree
import json
import sys
import os
import requests

"""
	SVN properties
"""
username = ""
password = ""
barnch_path = ""

"""
	SLack properties
	e.g. https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
"""

domain_url = ""


"""
	Hipchat properties
"""

server = ""
token = ""
room = ""

"""
	Paths
"""
pwd = os.getcwd()

rev_path_file = pwd + '/rev.txt'
log_path_file = pwd + '/temp/info.xml'


""" Programm """

class Logentry:pass

class Path: 
	def __init__(self, action, path):
		self.action = action
		self.path = path

class Payload:
	def __init__(self, attachments):
		self.attachments = attachments

class Attachment:pass

class SvnData:
	def __init__(self, username, password, barnch_path):
		self.username = username
		self.password = password
		self.barnch_path = barnch_path

	def get_head_revision_number(self):
		cmd = "svn info --username=" + self.username + " --password=" + self.password + " " + barnch_path + " | grep 'Revision' | awk '{print $2}'";
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		rev = proc.stdout.read()
		return rev
	def write_log_from_revision(self, revision):
		cmd = 'svn  log -v --username=' + self.username + ' --password=' + self.password + " " + barnch_path + ' -r'+str(revision)+':HEAD  --xml >> '+ log_path_file
		proc = subprocess.call(cmd, shell=True)


def proccessLogentry(logentry):
	l = Logentry();
	l.revision = logentry.get("revision");
	l.author = logentry.find("author").text;
	l.msg = logentry.find("msg").text;
	l.date = logentry.find("date").text;

	e_paths = logentry.find("paths");
	e_list_paths = e_paths.findall("path")
	paths = [];

	for path in e_list_paths:
		paths.append(Path(path.get("action"), path.text))

	l.paths = paths;

	return l;

def clean_and_write(f, text):
	f.seek(0);
	f.truncate();
	f.write(text);

def create_payload(logentry):
	ats = []
	at = Attachment()
	at.title = "Revision #" + logentry.revision
	at.text = "*Author:*\t" + logentry.author + "\n\n" + logentry.msg
	at.color = "#7CD197"
	at.mrkdwn_in = ["text", "pretext"]

	ats.append(at)

	at_msg_files = Attachment()
	at_msg_files.pretext = "Affected files:"

	ats.append(at_msg_files)

	for e_file in logentry.paths:
		at_file = Attachment()
		action = e_file.action
		if action=='A':
			at_file.color = "#7CD197"
		elif action == 'M':
			at_file.color = "#DE9E31"
		elif action == 'D':
			at_file.color = "#D50200"
		at_file.text = e_file.path
		ats.append(at_file)


	payload = Payload(ats)
	payload.text = "*New commit in " + logentry.date + "*"
	return payload

def create_payload_for_hipchat(logentry):

	message = "<b>New commit in " + logentry.date + "</b><br><br>"
	message += "<b>Revision #" + logentry.revision + "</b><br>"
	message += "<b>Author:</b>\t" + logentry.author + "<br><br>" + logentry.msg + "<br><br>"

	message += "Affected files:<br>"

	for e_file in logentry.paths:
		action = e_file.action
		message += "<span style='color:"
		if action=='A':
			message += "#7CD197"
		elif action == 'M':
			message += "#DE9E31"
		elif action == 'D':
			message += "#D50200"
		message += "'>"+action+"</span>"
		message += " " + e_file.path + "<br>"

	return message


def hipchat_notify(message, color='yellow', notify=False,
                   format='html'):
    """Send notification to a HipChat room via API version 2
    Parameters
    ----------
    token : str
        HipChat API version 2 compatible token (room or user token)
    room: str
        Name or API ID of the room to notify
    message: str
        Message to send to room
    color: str, optional
        Background color for message, defaults to yellow
        Valid values: yellow, green, red, purple, gray, random
    notify: bool, optional
        Whether message should trigger a user notification, defaults to False
    format: str, optional
        Format of message, defaults to text
        Valid values: text, html
    host: str, optional
        Host to connect to, defaults to api.hipchat.com
    """

    if len(message) > 10000:
        raise ValueError('Message too long')
    if format not in ['text', 'html']:
        raise ValueError("Invalid message format '{0}'".format(format))
    if color not in ['yellow', 'green', 'red', 'purple', 'gray', 'random']:
        raise ValueError("Invalid color {0}".format(color))
    if not isinstance(notify, bool):
        raise TypeError("Notify must be boolean")

    url = "https://{0}/v2/room/{1}/notification".format(server, room)
    headers = {'Content-type': 'application/json'}
    headers['Authorization'] = "Bearer " + token
    payload = {
        'message': message,
        'notify': notify,
        'message_format': format,
        'color': color
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    r.raise_for_status()



def main():

	svn = SvnData(username, password, barnch_path)

	current_head_rev = svn.get_head_revision_number()
	print "HEAD revision: " + current_head_rev

	f = open(rev_path_file, 'r+w')
	prev_rev = f.read()

	if prev_rev=='':
		clean_and_write(f, current_head_rev)
		print "Initial action. Writing HEAD revision into the file"
		sys.exit()

	if prev_rev==current_head_rev:
		print "No changes."
		sys.exit()
	else:
		if os.path.isfile(log_path_file):
			os.remove(log_path_file)
		prev_rev=int(prev_rev)+1
		svn.write_log_from_revision(prev_rev)
		print "Chages have detected. Writing logs into XML"
		clean_and_write(f, current_head_rev)

	print "Start parsing XML"
	e = xml.etree.ElementTree.parse(log_path_file).getroot();
	logentries = e.findall("logentry");

	data = [];

	for logentry in logentries:
		data.append(proccessLogentry(logentry));

	for item in data:

		payload = create_payload(item)
		message = create_payload_for_hipchat(item)

		print "Message is ready for sending."
		print message

		hipchat_notify(message)

		print "Message has been sent to slack"

main()



