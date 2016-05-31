import requests
from sets import Set
import json
import pprint

pp = pprint.PrettyPrinter(indent=2)

stores = []
# First store url
stores.append('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&type=Ale&sortdirection=Ascending&site=2002&fullassortment=0')
# Second store url
stores.append('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&type=Ale&sortdirection=Ascending&site=2001&fullassortment=0')

products = []

for store in stores:
  r = requests.get(store)
  if r.status_code == 200:
    for product in r.json()['ProductSearchResults']:
      pp.pprint(product['ProductNumber'])
  print('--------------------------')