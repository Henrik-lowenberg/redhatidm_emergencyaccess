# Created by: Henrik Lowenberg
# 2021-02-15
# Read
# https://python-freeipa.readthedocs.io/en/latest/
#
# How-to install python-freeipa:
# export https_proxy='SDS\firstname.lastname':yourpwd@httpwebpxgot.it.hclgss.com:8080
# pip install python-freeipa
#
# Import the freeipa library
from python_freeipa import ClientMeta
# pretty print to parse to human-readable output
import pprint
# parse json data
import json
# date
from datetime import datetime, timedelta
# another date
import dateutil.parser as dparser
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
  removeRole = False

  # get login credentials
  client = ClientMeta("idmreplica1.idm.example.com")
  client.login("admin","changeme")

  if sys.argv[1] = '--remove':
    removeRole = True

  if not removeRole:
    try:
      opts, args = getopt.getopt(argv,"hu:s:",["user=","servers="])
      for opt, arg in opts:

       if opt == '-h':
         print ('emergencyAccess.py -u username -s server1.example.com,server2.example.com')
         sys.exit(3)
       elif opt in ("-u", "--user"):
         user = arg
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

       elif opt in ("-s", "--servers"):
         servers = arg
         if ',' in servers:
           # split string to tuple, separate on comma 2 handle multiple servers
           res = tuple(servers.split(","))
           servers = res

    except getopt.GetoptError:
      print ('emergencyAccess.py -u username -s server1.example.com,server2.example.com')
      sys.exit(2)


  # get date, format 20210101
  now = datetime.now() # current date and time
  todaysdate = now.strftime("%Y%m%d")


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
    # print "In sudoruleadd()"
    # define common name
    emerg_sudoruleadd_cn = "unix_emerg_" + friendlyUserName + "_" + todaysdate + "_high_rule"
    # show rule if it exists
    # print client.sudorule_show(emerg_sudoruleadd_cn)
    # add rule
    client.sudorule_add(emerg_sudoruleadd_cn,"temporary emergency root access for " + user,o_cmdcategory='all',o_ipasudorunasusercategory='all')
    # add host(s) to rule
    client.sudorule_add_host(emerg_sudoruleadd_cn,host=servers)
    # add local IDM user to rule
    if not extuser:
      client.sudorule_add_user(emerg_sudoruleadd_cn,user=user)
    # print "not extuser"
    elif extuser:
      client.sudorule_add_user(emerg_sudoruleadd_cn,group=posixgroup_cn)
      # print "extuser true"
      # print posixgroup_cn

    # add command to rule (need to exist already)
    # client.sudorule_add_allow_command(emerg_sudoruleadd_cn,sudocmd="sudo su -")


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
      # print "not extuser"
    elif extuser:
      client.hbacrule_add_user(emerg_hbacruleadd_cn, group=posixgroup_cn,all='True')
      # print "extuser true"
      # print posixgroup_cn


  def removeold():
    all_emerg_groups = client.group_find("emerg")
    all_emerg_sudorules = client.sudorule_find("emerg")
    all_emerg_hbacrules = client.hbacrule_find("emerg")
    right_now_3_days_ago = datetime.today() - timedelta(days=3)

    try:
      if all_emerg_groups:
        #print all_emerg_groups['result'][1]['cn']
        for usergroup in all_emerg_groups['result'][1]['cn']:
          getTheDate = dparser.parse(usergroup, fuzzy=True)
          #print getTheDate
          if getTheDate < right_now_3_days_ago:
            print "user group is older than 3 days"
            groupRemovalList.append(usergroup)
            for group in groupRemovalList:
              client.group_del(group)
        print

      if all_emerg_sudorules:
        #print all_emerg_sudorules['result'][0]['cn']
        for sudorule in all_emerg_sudorules['result'][0]['cn']:
          getTheDate = dparser.parse(sudorule, fuzzy=True)
          #print getTheDate
          if getTheDate < right_now_3_days_ago:
            print "sudo rule is older than 3 days"
            sudoruleRemovalList.append(sudorule)
            for sudorule in sudoruleRemovalList:
              client.sudorule_del(sudorule)
        print

      if all_emerg_hbacrules:
        #print all_emerg_hbacrules['result'][0]['cn']
        for hbacrule in all_emerg_hbacrules['result'][0]['cn']:
          getTheDate = dparser.parse(hbacrule, fuzzy=True)
          #print getTheDate
          if getTheDate < right_now_3_days_ago:
            print "hbac rule is older than 3 days"
            hbacruleRemovalList.append(hbacrule)
            for hbacrule in hbacruleRemovalList:
              client.hbacrule_del(hbacrule)
        print
    except NameError:
      print "some or no group/rules were not found..."



  # Call methods
  if not removeRole:
    if friendlyUserName:
      posixgroup_cn = groupadd(friendlyUserName)
    sudoruleadd(user,servers,posixgroup_cn)
    hbacruleadd(user,servers,posixgroup_cn)
  elif removeRole:
    removeold()


if __name__ == "__main__":
  main(sys.argv[1:])

# END OF SCRIPT #