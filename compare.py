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
# First store url
stores.append(2002)
# Second store url
stores.append(2001)

products = {}
difference = []

for store in stores:
  page = 0
  next_page = 0
  while next_page != -1:
    r = requests.get('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&type=Ale&sortdirection=Ascending&fullassortment=0&site=' + str(store) + '&page=' + str(page))
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
            
print('--------- Difference ---------')  
for product in difference:
  print('Product')
  print('Name: ' + product['ProductNameBold'])
  if 'ProductNameThin' in product != None:
    print(' Category: ' + str( product['ProductNameThin'] ))
@app.route('/')
def index(products=None):
    return render_template('index.html', products = difference)

if __name__ == "__main__":
    app.run()
