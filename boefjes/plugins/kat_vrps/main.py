"""Boefje script for validating vrps records"""
import json
import logging
from typing import Union, Tuple

import requests
import os.path
import json
from datetime import datetime
from netaddr import IPNetwork, IPAddress

from boefjes.job_models import BoefjeMeta

logger = logging.getLogger(__name__)


def run(boefje_meta: BoefjeMeta) -> Tuple[BoefjeMeta, Union[bytes, str]]:
    input_ = boefje_meta.arguments["input"]
    print("Meta:")
    print(boefje_meta)

    testip = '164.68.110.58' #valid
    testip = '195.246.117.117' #invalid
    testip = '193.37.108.0' #invalid
    testip = input_['address']

    #check if vrps.json exists, is valid json and not too old.
    url          = 'https://console.rpki-client.org/vrps.json'
    now          = datetime.utcnow()
    download     = True
    vrps_content = None
    if not os.path.exists('vrps.json'):
        download = True
    else:
        try:
            f = open('vrps.json')
            vrps_content = json.load(f)
            f.close()
            buildtime = datetime.strptime(vrps_content['metadata']['buildtime'], '%Y-%m-%dT%H:%M:%SZ' )
            if (now - buildtime).total_seconds() > 1800:
                download = True
            else:
                download = False  #file exists, is valid json and not older than 30 minutes
            
        except:
            download = True

    #if no valid database was found, download it
    if download:
        r = requests.get(url, allow_redirects=True)
        open('vrps.json', 'wb').write(r.content)
        f = open('vrps.json')
        vrps_content = json.load(f)
        f.close()

    #now search for records
    exists = False
    valid = False
    roas = []
    for roa in vrps_content['roas']:
        prefix = roa['prefix']
        if IPAddress(testip) in IPNetwork(roa['prefix']):
            exists = True
            expires = datetime.fromtimestamp( roa['expires'] )
            roas.append({'prefix': roa['prefix'], 'expires': expires.strftime('%Y-%m-%dT%H:%M'), 'ta': roa['ta']})
            if expires > now:
                valid = True

    results = {
      "vrps_records": roas,
      "valid": valid,
      "exists": exists
    }
    print("Results:")
    print(json.dumps(results))

    return boefje_meta, json.dumps(results)



#boefje_1               | Meta:
#boefje_1               | id='b844cfe72c424f3c9de0caf1eaa7fd18' started_at=datetime.datetime(2022, 11, 27, 14, 33, 50, 563021, tzinfo=datetime.timezone.utc) ended_at=None boefje=Boefje(id='vprs', version=None) input_ooi='IPAddressV4|internet|164.68.123.321' arguments={'input': {'object_type': 'IPAddressV4', 'scan_profile': "reference=Reference('IPAddressV4|internet|164.68.123.321') level=2 scan_profile_type='inherited'", 'primary_key': 'IPAddressV4|internet|164.68.123.321', 'address': '164.68.123.321', 'network': {'name': 'internet'}}} organization='_dev'
#boefje_1               | {"vrps_records": [], "valid": false, "exists": false}

