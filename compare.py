#!/usr/bin/env python
# -*- coding: latin-1 -*-
import requests
import json
from flask import Flask, render_template, request, url_for, redirect, abort
import xml.etree.ElementTree as ET

app = Flask(__name__)

tree = ET.parse('stores.xml')
root = tree.getroot()

def get_store_info( store_id ):
    for store in stores:
        if store['nr'] == store_id:
            pp.pprint(store)
            return store
def remove_duplicates( store1, store2 ):
    for product in store1:
        for product2 in store2:
            if product['ProductId'] == product2['ProductId']:
                store1.remove(product)
                store2.remove(product2)
def get_stores():
    stores = []
    for child in root.iter('ButikOmbud'):
        # Check if store and not pick up point
        if '-' not in child[1].text:
            store = {
                'nr': child[1].text,
                'name': child[3].text,
                'address': child[4].text,
                'place': child[6].text.title()
            }
            stores.append( store )
    return sorted( stores, key=lambda store: store['place'])
def compare_stores( store_one_id, store_two_id ):
    stores = [ store_one_id, store_two_id ]

    products = {}
    difference = []

    for store in stores:
        products = []
        page = 0
        next_page = 0
        while next_page != -1:
            r = requests.get('http://www.systembolaget.se/api/productsearch/search?subcategory=%C3%96l&sortdirection=Ascending&fullassortment=0&site=' + str(store) + '&page=' + str(page))
            if r.status_code == 200:
                next_page = r.json()['Metadata']['NextPage']
                page += 1
                for product in r.json()['ProductSearchResults']:
                    products.append(product)
        store_assortment.append( products )

    if len(store_assortment[0]) > len(store_assortment[1]):
        remove_duplicates( store_assortment[0], store_assortment[1] )
    else:
        remove_duplicates( store_assortment[1], store_assortment[0] )
    return store_assortment

@app.route('/')
def index(stores=None):
    return render_template('index.html', stores = get_stores())

@app.route('/results', methods=['GET', 'POST'])
def results( products = None ):
    return render_template('results.html', stores = get_stores())

@app.route('/add_stores', methods=['GET', 'POST'])
def add_stores():
    return render_template('results.html', products = compare_stores( request.args.get('store1_field'), request.args.get('store2_field')))

if __name__ == "__main__":
    app.run(debug=True)
