#!/usr/local/bin/python
import sys, os, json, yaml, requests

stas = {"NWW":{},
        "NWP":{},
        "NWS":{},
        "NWDP":{}
}

def load_stations():
  global stas
  #s = json.loads (open("stations.json","r").read())
  t = requests.get("http://wmlocal.nwd.usace.army.mil/apps/metadata/webexec/meta.py?function=getOffice&id=ALL").text
  s = json.loads(t)
  for sta in s:
    try:
      a = json.loads(s[sta]["AGENCY_JSON"])
    except:
      a = {}
    office = s[sta]["OFFICE_ID"]
    if "NWS Handbook 5 ID" in a and office in stas:
      stas[office][a["NWS Handbook 5 ID"]] = sta

load_stations()
avail= json.loads (open("avail.json","r").read())
for office in stas:
  output = {}
  for loc in stas[office]:
    if loc+"_XE" in avail:
      if office== "NWP":
        output[loc+"_XE"] = {"path":stas[office][loc]+".Flow-Local.Inst.~6Hours.0.BLEND-RFC-OBS-RFC-FCST"}
      else:
        output[loc+"_XE"] = {"path":stas[office][loc]+".Flow-Local.Ave.~6Hours.6Hours.BLEND-RFC-OBS-RFC-FCST"}
  open(office.lower()+"_local_flows.yaml","w").write(yaml.safe_dump(output, default_flow_style=False))
  


