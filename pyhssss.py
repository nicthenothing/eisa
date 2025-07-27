#!/usr/bin/python3
import requests
import json
import sys

print("    \033[1;33;40m(\__/)")
print("    (='.'=)")
print("   ('')_('')")
url = input('\033[1;32;40mEnter the pyhss url[127.0.0.1:8080] :')
if not url:
  url = "127.0.0.1:8080"
url = "http://" + url
imsi = input("Enter IMSI[418200000069761]: ")
if not imsi:
  imsi = "418200000069761"
else:
  while len(imsi) != 15:
     print("IMSI must be 15 characters long. Please enter again: ")
     imsi = input ('Enter IMSI: ')
msisdn = input(f"Enter Phone Number[00{imsi[-2:]}]: ")
if not msisdn:
   msisdn = "00"+imsi[-2:]
ki = input("Enter KI[11111111111111111111111111111111]: ")
if not ki:
  ki = "11111111111111111111111111111111"
else:
  while len(ki) != 32:
      print("KI must be 32 characters long. Please enter again: ")
      ki = input("Enter KI: ")
opc = input("Enter opc[11111111111111111111111111111111]: ")
if not opc:
  opc = "11111111111111111111111111111111"
else:
  while len(opc) != 32:
      print("OPC must be 32 characters long. Please enter again: ")
      opc = input("Enter OPC: ")
mcc = input("Enter MCC [418]: ")
if not mcc:
  mcc = "418"
mnc = input("Enter MNC [20]: ")
if not mnc:
  mnc = "20"
apn_internet = input("Enter APN name for internet [internet]: " )
if not apn_internet:
  apn_internet = 'internet'
apn_internet_id = ""
apn_ims = input("Enter APN name for ims [ims]: " )
if not apn_ims:
  apn_ims = 'ims'
apn_ims_id = ""
error_flag = False

def apn_create(apn_name):
    url_apn = url + '/apn/'
    data = {
      "apn": apn_name,
      "apn_ambr_dl": 0,
      "apn_ambr_ul": 0
    }
    try:
      response = requests.put(url_apn, json=data)
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
    data = json.loads(response.content)
    if response.status_code == 200:
      print(f'APN {apn_name} successfully with apn_id = {data["apn_id"]}')
    elif response.status_code != 200:
      global error_flag
      error_flag = True
      print(f'APN Error: {response.status_code}')    

def create_auc(ki, opc, imsi):
    url_auc = url + "/auc/"
    data = {
        "ki": ki,
        "opc": opc,
        "amf": "8000",
        "sqn": 0,
        "imsi": imsi,
    }
    try:
      response = requests.put(url_auc, json=data)
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
      sys.exit(1)  # Exit the program with an error code of 1
    data = json.loads(response.content)
    if response.status_code == 200:
        print(f'AUC successfully created for IMSI {imsi} with auc_id = {data["auc_id"]}')
        return data["auc_id"]
    elif response.status_code != 200:
        global error_flag
        error_flag = True
        print(f"AUC Error: {response.status_code}\nMaybe {imsi} already exist!")

def subscriber(imsi, msisdn, auc_id):
    url_subscriber = url + "/subscriber/"
    data = {
        "imsi": imsi,
        "enabled": True,
        "auc_id": auc_id,
        "default_apn": apn_internet_id,
        "apn_list": f"{apn_internet_id},{apn_ims_id}",
        "msisdn": msisdn,
        "ue_ambr_dl": 0,
        "ue_ambr_ul": 0,
    }
    try:
      response = requests.put(url_subscriber, json=data)
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
      sys.exit(1)  # Exit the program with an error code of 1
    if response.status_code == 200:
        print(f"Subscriber successfully created for IMSI {imsi}")
    elif response.status_code != 200:
        global error_flag
        error_flag = True
        print(f"Subscriber Error: {response.status_code}")

def ims_subscriber(imsi, msisdn):
    url_ims_subscriber = url + "/ims_subscriber/"
    data = {
        "imsi": imsi,
        "msisdn": msisdn,
        "sh_profile": "string",
        "scscf_peer": f"scscf.ims.mnc0{mnc}.mcc{mcc}.3gppnetwork.org",
        "msisdn_list": f"[{msisdn}]",
        "ifc_path": "default_ifc.xml",
        "scscf": f"sip:scscf.ims.mnc0{mnc}.mcc{mcc}.3gppnetwork.org:6060",
        "scscf_realm": f"ims.mnc0{mnc}.mcc{mcc}.3gppnetwork.org"
    }
    try:
      response = requests.put(url_ims_subscriber, json=data)
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
      sys.exit(1)  # Exit the program with an error code of 1
    if response.status_code == 200:
        print(f"IMS Subscriber successfully creates for IMSI {imsi}")
    elif response.status_code != 200:
        global error_flag
        error_flag = True
        print(f"IMS Subscriber Error: {response.status_code}")

def get_apn_id (apn_name):
    url_apn_list = url + '/apn/list'
    try:
      response = requests.get(url_apn_list)
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
      sys.exit(1)  # Exit the program with an error code of 1
    if response.status_code == 200:
      data = json.loads(response.content)
      for apn in data:
        if apn['apn'] == apn_name:
          return apn['apn_id']
       
def check_for_apn(apn_name):
    try:
      response = requests.get(url + '/apn/list')
    except requests.exceptions.ConnectionError as e:
      print("\033[1;31;40mConnection error:\n", e)
      sys.exit(1)  # Exit the program with an error code of 1
    if response.status_code != 200:
        raise Exception('Failed to retrieve APN list')
    apn_list = json.loads(response.content)
    apn_exists = False
    for apn in apn_list:
        if apn['apn'] == apn_name:
            apn_exists = True
            break
    return apn_exists

if check_for_apn(apn_internet) == False:
  print(f"APN {apn_internet} dose not exist!")
  if not error_flag:
    apn_create(apn_internet)
  print(f"APN {apn_internet} created.")
apn_internet_id = get_apn_id(apn_internet)
if check_for_apn(apn_ims) == False:
  print(f"APN {apn_ims} dose not exist!")
  if not error_flag:
    apn_create(apn_ims)
  print(f"APN {apn_ims} created.")
apn_ims_id = get_apn_id(apn_ims)
if not error_flag:
  auc_id= create_auc(ki, opc, imsi)
if not error_flag:
  subscriber(imsi, msisdn, auc_id)
if not error_flag:
  ims_subscriber(imsi, msisdn)
