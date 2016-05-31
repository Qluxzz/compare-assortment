#!/usr/bin/env python
# -*- coding: latin-1 -*-
import requests
from sets import Set
import json
import pprint

pp = pprint.PrettyPrinter(indent=2)

stores = []
# First store url
stores.append(2002)
# Second store url
stores.append(2001)

products = {}
difference = []

for store in stores:
  r = requests.get(store)
  if r.status_code == 200:
    for product in r.json()['ProductSearchResults']:
      pp.pprint(product['ProductNumber'])
  print('--------------------------')    r = requests.get('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&type=Ale&sortdirection=Ascending&fullassortment=0&site=' + str(store) + '&page=' + str(page))