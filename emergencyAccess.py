#!/usr/bin/python
# Created by: Henrik Lowenberg
# 2021-02-15
# Read
# https://python-freeipa.readthedocs.io/en/latest/
# execute:
# pip install python-freeipa
#
# Import the freeipa library
from python_freeipa import ClientMeta
# pretty print to parse to human-readable output
import pprint
# parse json data
import json
# date
from datetime import datetime
# get input
import sys, getopt
# import regular expressions
import re
 

def main(argv):
  """
  Main function for starting methods
  """
  user = None
  servers = None
  extuser1 = None
  extuser2 = None
 
  try:
    opts, args = getopt.getopt(argv,"hu:s:",["user=","servers="])
    for opt, arg in opts:
 
     if opt == '-h':
       print ('emergencyAccess.py -u username -s server1.example.com,server2.example.com')
       sys.exit(3)
     elif opt in ("-u", "--user"):
       user = arg
    #   print (user)
     elif opt in ("-s", "--servers"):
       servers = arg
       if ',' in servers:
         # split string to tuple, separate on comma 2 handle multiple servers
         res = tuple(servers.split(","))
         servers = res
         #print res
         #print (servers)

  except getopt.GetoptError:
    print ('emergencyAccess.py -u username -s server1.example.com,server2.example.com')
    sys.exit(2)
 
  # get date, format 20210101
  now = datetime.now() # current date and time
  todaysdate = now.strftime("%Y%m%d")
 
  # get login credentials
  client = ClientMeta("replica1.idm.example.com")
  client.login("admin","changeme")
 
# testing regular expressions to identify AD account
  # search for @sds.hclgss.com or similar
  if re.search("\@[a-z]{3,9}\.[a-z]{3,9}\.[a-z]{3,9}", user):
    extuser1 = user
  # search for SDS\ or similar with raw to include backslash
  elif re.search(r"[A-Z]{3,5}\\", user):
    extuser2 = user
 

  if extuser1: print "extuser1: " + extuser1
  if extuser2: print "extuser2: " + extuser2
 
  if extuser1: # split on @, return left side
    tmpfriendlyUserName = extuser1.split("@", 1)
    friendlyUserName = tmpfriendlyUserName[0]
    extuser = extuser1
  elif extuser2: # split on \, return right side
    tmpfriendlyUserName = extuser2.split("\\", 1)
    friendlyUserName = tmpfriendlyUserName[1]
    extuser = extuser2
 
 
  def groupadd(friendlyUserName):
    print "In groupadd()"
    posixgroup_cn = "unix_emerg_" + friendlyUserName + "_" + todaysdate + "_user"
    externalgroup_cn = "unix_emerg_" + friendlyUserName + "_" + todaysdate + "_user_ad"
    client.group_add(posixgroup_cn)
    client.group_add(externalgroup_cn, external=True)
    client.group_add_member(posixgroup_cn,group=externalgroup_cn)
    client.group_add_member(externalgroup_cn,ipaexternalmember=extuser)
    return posixgroup_cn
 
 
  def sudoruleadd(user,servers,posixgroup_cn):
    print "In sudoruleadd()"
    # define common name
    emerg_sudoruleadd_cn = "unix_emerg_" + friendlyUserName + "_" + todaysdate + "_high_rule"
    # show rule if it exists
#    print client.sudorule_show(emerg_sudoruleadd_cn)
#    sys.exit()
    # add rule
    client.sudorule_add(emerg_sudoruleadd_cn,"temporary emergency root access for " + user,o_cmdcategory='all',o_ipasudorunasusercategory='all')
    # add host(s) to rule
    client.sudorule_add_host(emerg_sudoruleadd_cn,host=servers)
    # add local IDM user to rule
#    client.sudorule_add_user(emerg_sudoruleadd_cn,user=user)
    if not extuser:
      client.sudorule_add_user(emerg_sudoruleadd_cn,user=user)
      print "not extuser"
    elif extuser:
      client.sudorule_add_user(emerg_sudoruleadd_cn,group=posixgroup_cn)
      print "extuser true"
      print posixgroup_cn

    # add command to rule (need to exist already)
#    client.sudorule_add_allow_command(emerg_sudoruleadd_cn,sudocmd="sudo su -")
 
 
  def hbacruleadd(user,servers,posixgroup_cn):
    print "In hbacruleadd()"
    # define common name
    emerg_hbacruleadd_cn = "allow_unix_emerg_" + friendlyUserName + "_" + todaysdate + "_high_hbac"
    hbac_descr = "temporary access for user ${user} to server(s): ${servers}"
    # add rule
    client.hbacrule_add(emerg_hbacruleadd_cn)
    # add hosts to rule
    client.hbacrule_add_host(emerg_hbacruleadd_cn, host=servers,all='True')
    # add user to rule
    if not extuser:
      client.hbacrule_add_user(emerg_hbacruleadd_cn, user=user,all='True')
     print "not extuser"
    elif extuser:
      client.hbacrule_add_user(emerg_hbacruleadd_cn, group=posixgroup_cn,all='True')
      print "extuser true"
      print posixgroup_cn


  # Call methods
  if friendlyUserName:
    posixgroup_cn = groupadd(friendlyUserName)
  
  sudoruleadd(user,servers,posixgroup_cn)
  hbacruleadd(user,servers,posixgroup_cn)
 
if __name__ == "__main__":
#  print len(sys.argv)
#  if len (sys.argv) != 5 :
#    print "Error!\nUsage: ./emergencyAccess.py -u username -s server1,server2,server3"
#    sys.exit (1)
 
  main(sys.argv[1:])
 
# END OF SCRIPT #