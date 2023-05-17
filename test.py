import json
import requests
import os
import sys
import time


from prometheus_client import start_http_server, Gauge, Info

URL = os.environ.get(ENDPOINT_URL, "http://43.205.243.151:7070/crypto/listings")
DURATION = int(os.environ.get(QUERY_DURATION, 10))

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
  start_http_server(8000)
  g = Gauge('delta', 'variation between queries', labelnames=['ID', 'Name'])

  while True:
    time.sleep(DURATION)
    r = requests.get(url)
    for entry in r.json():
      store_value(entry)
    temp = {k: v for k, v in sorted(deltas.items(), key=lambda item: item[1], reverse=True)}
    for k, v in temp.items():
      print(k, v)
      g.labels(ID=k, Name=k).set(v)
    #print(temp)
