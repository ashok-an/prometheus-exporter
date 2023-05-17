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


from prometheus_client import start_http_server, Gauge, Info, Counter, Summary

URL = os.environ.get("QUERY_URL", "http://43.205.243.151:7070/crypto/listings")
DURATION = int(os.environ.get("QUERY_INTERVAL_SECONDS", 10))
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

query_time = Summary('query_processing_seconds', 'Time spent processing request')

@query_time.time()
def do_query(url=URL):
    r = requests.get(url)

    if r.status_code not in [200, 201]:
      logger.error(f"Unable to query {url}: Response: {r.text}")
      sys.exit(0)
  
    return r.json()
# end

if __name__ == "__main__":
  logger.info(f"(config) EXPORTER_VERSION: {EXPORTER_VERSION}")
  logger.info(f"(config) EXPORTER_PORT: {EXPORTER_PORT}")
  logger.info(f"(config) QUERY_INTERVAL_SECONDS: {DURATION}")
  logger.info(f"(config) QUERY_URL: {URL}")
  logger.info(f"Starting exporter ...")
  start_http_server(EXPORTER_PORT)
  
  i = Info('version', 'version details of exporter') 
  i.info({'app': EXPORTER_VERSION, 'system': SYSTEM_VERSION})

  c = Counter('query_count', 'Total number of queries')
  g = Gauge('price_change', 'variation between queries', labelnames=['ID', 'Name'])

  while True:
    c.inc()
    logger.info(f"query: {URL} ...")
    logger.debug("+++ Storing values")
    for entry in do_query():
      store_value(entry)

    logger.debug("+++ Sorting based on deltas")
    temp = {k: v for k, v in sorted(deltas.items(), key=lambda item: item[1], reverse=True)}
    logger.info(f"+++ top5 = {list(temp.keys())[:5]}")

    logger.debug("+++ Publishing metrics")
    for k, v in temp.items():
      _id, name = k.split('.')
      g.labels(ID=_id, Name=name).set(v)

    time.sleep(DURATION)
