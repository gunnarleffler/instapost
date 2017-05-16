#!/bin/bash
#Get data from USBR and pipe to instapost using json format
./usbr_to_json -d --lookback 7 example.conf | \
  ../instapost/instapost -v -j
#Get data from USBR and pipe to instapost using YAML format
./usbr_to_json -d --lookback 7 example.conf | \
  ../instapost/instapost -v 
