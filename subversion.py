#!/usr/bin/python

import subprocess
import xml.etree.ElementTree
import json
import sys
import os

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

		print "Message is ready for sending."

		subprocess.call("curl -X POST --data-urlencode 'payload=" + json.dumps(payload, default=lambda o: o.__dict__) + "' " + domain_url +"", shell=True)

		print "Message has been sent to slack"

main()



