#!/usr/bin/env python
# -*- coding: latin-1 -*-
import requests
from sets import Set
import json
import pprint
from flask import Flask
from flask import render_template

app = Flask(__name__)
pp = pprint.PrettyPrinter(indent=2)

stores = []
# The store to emanate from
stores.append(2001)
# The store to compare with
stores.append(1901)

products = {}
difference = []

for store in stores:
  page = 0
  next_page = 0
  while next_page != -1:
    r = requests.get('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&sortdirection=Ascending&fullassortment=0&site=' + str(store) + '&page=' + str(page))
    if r.status_code == 200:
      next_page = r.json()['Metadata']['NextPage']
      page += 1
      for product in r.json()['ProductSearchResults']:
        if store == stores[1]:
          if product['ProductNumber'] not in products:
             difference.append(product)
        else:
          if product['ProductNumber'] not in products:
             products[product['ProductNumber']] = product

@app.route('/')
def index(products=None):
    return render_template('index.html', products = difference)

if __name__ == "__main__":
    app.run()
