#!/usr/bin/env python3.1
#
# Easy Python3 Dynamic DNS
# Originally by Jed Smith <jed@jedsmith.org> 4/29/2009
# Modified by Ole Markus With <olemarkus@olemarkus.org>
# This code and associated documentation is released into the public domain.
#
# To use:
#
#   1. In the Linode DNS manager, edit your zone (must be master) and create
#      an A record for your home computer.  You can name it whatever you like;
#      I call mine 'foo'.  Fill in 0.0.0.0 for the IP.
#
#   2. Save it.
#
#   3. Edit the four configuration options below, following the directions for
#      each.  As this is a quick hack, it assumes everything goes right.
#
# Simply add your domain name and hostname here
#
DOMAIN="example.com"
HOSTNAME="foo"
#
# Your Linode API key.  You can generate this by going to your profile in the
# Linode manager.  It should be fairly long.
#
KEY = "abcdefghijklmnopqrstuvwxyz"
#
# The URI of a Web service that returns your IP address as plaintext. 
#
# My personal one is ifconfig.me, but if you want your own, you can use the
# following lines of PHP.
#
#     <?php
#     header("Content-type: text/plain");
#     printf("%s", $_SERVER["REMOTE_ADDR"]);
#
GETIP = "http://ifconfig.me"
#
# If for some reason the API URI changes, or you wish to send requests to a
# different URI for debugging reasons, edit this.  {0} will be replaced with the
# API key set above, and & will be added automatically for parameters.
#
API = "https://api.linode.com/?api_key={0}&resultFormat=JSON"
#
# Comment or remove this line to indicate that you edited the options above.
#
exit("Did you edit the options?  vi this file open.")
#
# That's it!
#
# Now run LinodeDynDNS.py manually, or add it to cron, or whatever.  You can even have
# multiple copies of the script doing different zones.
#
# For automated processing, this script will always print EXACTLY one line, and
# will also communicate via a return code.  The return codes are:
#
#    0 - No need to update, A record matches my public IP
#    0 - Updated record
#    2 - Some kind of error or exception occurred
#
# The script will also output one line that starts with either OK or FAIL.  If
# an update was necessary, OK will have extra information after it.
#
# If you want to see responses for troubleshooting, set this:
#
DEBUG = False


#####################
# STOP EDITING HERE #

try:
	from json import load
	import urllib.request

except Exception as excp:
	exit("Couldn't import the standard library. Are you running Python 3?")

class AppURLopener(urllib.request.FancyURLopener):
    version = "curl"

urllib.request._urlopener = AppURLopener()

def execute(action, parameters = {}):
	# Execute a query and return a Python dictionary.
	uri = "{0}&action={1}".format(API.format(KEY), action)
	if parameters and len(parameters) > 0:
		uri = "{0}&{1}".format(uri, urllib.parse.urlencode(parameters))
	if DEBUG:
		print("-->", uri)
	file, headers = urllib.request.urlretrieve(uri)
	if DEBUG:
		print("<--", file)
		print(headers, end="")
		print(open(file).read())
		print()
	json = load(open(file), encoding="utf-8")
	if len(json["ERRORARRAY"]) > 0:
		err = json["ERRORARRAY"][0]
		raise Exception("Error {0}: {1}".format(int(err["ERRORCODE"]),
			err["ERRORMESSAGE"]))
	return load(open(file), encoding="utf-8")

def finddomainid():
	domains = execute("domain.list")["DATA"]
	for domain in domains:
		if domain["DOMAIN"] == DOMAIN:
			return domain["DOMAINID"]
	raise Exception("Domain not found")

def findresource(domainid):
	resources = execute("domain.resource.list", {"DomainId": domainid})["DATA"]
	for resource in resources:
		if resource["NAME"] == HOSTNAME:
			return resource
	raise Exception("Could not find hostname under this domain")

def ip():
	if DEBUG:
		print("-->", GETIP)
	file, headers = urllib.request.urlretrieve(GETIP)
	if DEBUG:
		print("<--", file)
		print(headers, end="")
		print(open(file).read())
		print()
	return open(file).read().strip()

def main():
	try:
		domainid = finddomainid()
		if DEBUG:
			print("Found domain", domainid)
		res = findresource(domainid)
		if(len(res)) == 0:
			raise Exception("No such resource?".format(RESOURCE))
		public = ip()
		if res["TARGET"] != public:
			old = res["TARGET"]
			request = {
				"ResourceID": res["RESOURCEID"],
				"DomainID": res["DOMAINID"],
				"Name": res["NAME"],
				"Type": res["TYPE"],
				"Target": public,
				"TTL_Sec": res["TTL_SEC"]
			}
			execute("domain.resource.update", request)
			print("OK {0} -> {1}".format(old, public))
			return 0
		else:
			print("OK")
			return 0
	except Exception as excp:
		print("FAIL {0}: {1}".format(type(excp).__name__, excp))
		return 2

if __name__ == "__main__":
	exit(main())
