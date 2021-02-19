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
# parse json data
import json
# date
from datetime import datetime
# get input
import sys, getopt
 
def main(argv):
  """
  Main contains methods: sudruleadd, hbacruleadd
  """
  user = None
  servers = None
 
  try:
    opts, args = getopt.getopt(argv,"hu:s:",["user=","servers="])
    for opt, arg in opts:
 
     if opt == '-h':
       print ('emergencyAccess.py -u <username> -s <serverlist,commaseparated>')
       sys.exit(3)
     elif opt in ("-u", "--user"):
       user = arg
     elif opt in ("-s", "--servers"):
       servers = arg
  except getopt.GetoptError:
    print ('emergencyAccess.py -u <username> -s <serverlist,commaseparated>')
    sys.exit(2)
 
  # get date, format 20210101
  now = datetime.now() # current date and time
  todaysdate = now.strftime("%Y%m%d")
 
  # get login credentials
  client = ClientMeta("idmreplica1.idm.example.com")
  client.login("admin","mypwd")
 
  def sudoruleadd(user,servers):
    # define common name
    emerg_sudoruleadd_cn = "unix_emerg_" + user + "_" + todaysdate + "_high_rule"
    # show rule if it exists
#    print client.sudorule_show(emerg_sudoruleadd_cn)
#    sys.exit(3)
    # add rule
    client.sudorule_add(emerg_sudoruleadd_cn,"temporary emergency root access for " + user,o_cmdcategory='all',o_ipasudorunasusercategory='all')
    # add host(s) to rule
    client.sudorule_add_host(emerg_sudoruleadd_cn,host=servers)
    # add user to rule
    client.sudorule_add_user(emerg_sudoruleadd_cn,user=user)
    # add command to rule (need to exist already)
#    client.sudorule_add_allow_command(emerg_sudoruleadd_cn,sudocmd="sudo su -")
 
 
  def hbacruleadd(user,servers):
    # define common name
    emerg_hbacruleadd_cn = "allow_unix_emerg_" + user + "_" + todaysdate + "_high_hbac"
    hbac_descr = "temporary access for user ${user} to server(s): ${servers}"
    # add rule
    client.hbacrule_add(emerg_hbacruleadd_cn)
    # add hosts to rule
    client.hbacrule_add_host(emerg_hbacruleadd_cn, host=servers, all='True' )
    # add user to rule
    client.hbacrule_add_user(emerg_hbacruleadd_cn, user=user, all='True' )

 # Call methods
  sudoruleadd(user,servers)
  hbacruleadd(user,servers)

 
if __name__ == "__main__":
#  print len(sys.argv)
#  if len (sys.argv) != 5 :
#    print "Error!\nUsage: ./emergencyAccess.py -u username -s server1,server2,server3"
#    sys.exit (1)

  main(sys.argv[1:])