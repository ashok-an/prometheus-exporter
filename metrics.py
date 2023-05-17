import json
import requests
import os
import sys
import time
import logging

logger = logging.getLogger('crypto-exporter')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)


from prometheus_client import start_http_server, Gauge, Info

URL = os.environ.get("QUERY_URL", "http://43.205.243.151:7070/crypto/listings")
DURATION = int(os.environ.get("QUERY_INTERVAL", 10))
SYSTEM_VERSION = str(sys.version)
EXPORTER_VERSION = "1.0"
EXPORTER_PORT = int(os.environ.get("EXPORTER_PORT", 8000))

"""
 {
    "ID": "9014",
    "Name": "CoinN",
    "Price": 2.744045445536268
  },
"""

# id.Name: {cur: v0, past: v1, delta: <diff>}
# v0: latest
# v9: 10th value
# delta = abs(v0 - v1)
values = {}
deltas = {}

def store_value(entry):
  k = entry.get('ID') + '.' + entry.get('Name')
  v = entry.get('Price')
  global values
  if k in values:
    this = values[k]
    past, cur = this.get('cur'), v
    delta = abs(cur - past)

    values[k]['past'] = values[k]['cur']
    values[k]['cur'] = v
  else:
    values[k] = {'cur': v, 'past': v}
    delta = 0

  deltas[k] = delta
# end  


if __name__ == "__main__":
  logger.info(f"Starting exporter on localhost:{EXPORTER_PORT} ...")
  start_http_server(EXPORTER_PORT)
  
  i = Info('exporter', 'version details of exporter') 
  i.info({'version': EXPORTER_VERSION, 'system': SYSTEM_VERSION})

  g = Gauge('delta', 'variation between queries', labelnames=['ID', 'Name'])

  while True:
    logger.info(f"query: {URL} ...")
    r = requests.get(URL)

    if r.status_code not in [200, 201]:
      logger.error(f"Unable to query {URL}: Response: {r.text}")
      break

    logger.debug("+++ Storing values")
    for entry in r.json():
      store_value(entry)

    logger.debug("+++ Sorting based on deltas")
    temp = {k: v for k, v in sorted(deltas.items(), key=lambda item: item[1], reverse=True)}
    logger.info(f"+++ {temp.keys()}")

    logger.debug("+++ Publishing metrics")
    for k, v in temp.items():
      _id, name = k.split('.')
      g.labels(ID=_id, Name=name).set(v)

    time.sleep(DURATION)
