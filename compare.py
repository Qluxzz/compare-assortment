
import requests
from flask import Flask, render_template, request, url_for, redirect, abort
import xml.etree.ElementTree as ET
import pprint

pp = pprint.PrettyPrinter(indent=4)

def get_url(store):
    """ Return formated URL """
    params = {
        'subcategory': '%C3%96l',
        'sortdirection': 'Ascending',
        'fullassortment': '0',
        'site': str(store),
        'page': '0'
    }
    return 'http://www.systembolaget.se/api/productsearch/search', params

def get_store_info(stores, store_id):
    """ Return specific store info """
    for store in stores:
        if store['nr'] == store_id:
            pp.pprint(store)
            return store

def remove_duplicates(store1, store2):
    """ Remove duplicates in each store """
    ids = [set((x['id']) for x in store1), set((x['id']) for x in store2)]
    
    return [
        [x for x in store1 if x['id'] not in ids[1]],
        [x for x in store2 if x['id'] not in ids[0]]
    ]

def get_stores():
    """ Parse store information from xml file and return sorted list """
    tree = ET.parse('stores.xml')
    root = tree.getroot()
    stores = []
    for child in root.iter('ButikOmbud'):
        # Check if store and not pick up point
        if '-' not in child[1].text:
            store = {
                'nr': child[1].text,
                'place': child[6].text.title()
            }
            if child[2].text:
                store['name'] = child[2].text
            else:
                store['name'] = child[3].text
            stores.append(store)
    return sorted(stores, key=lambda store: store['place'])

def compare_stores(store_one_id, store_two_id):
    """ Compare the products between two stores """
    store_assortment = get_products([store_one_id, store_two_id])
    store_assortment = remove_duplicates(store_assortment[0], store_assortment[1])

    return store_assortment

def get_products(stores):
    """ Get products from stores """
    store_assortment = []

    for store in stores:
        products = []

        url, params = get_url(store)

        while params['page'] != -1:
            _request = requests.get(url, params=params)

            if _request.status_code == 200:
                data = _request.json()
                params['page'] = data['Metadata']['NextPage']

                for product in data['ProductSearchResults']:
                    entry = {
                        'id': product['ProductId'],
                        'description': product['BeverageDescriptionShort'],
                        'country': product['Country'],
                        'name': '{} {}'.format(product['ProductNameBold'], product['ProductNameThin']),
                        'url': product['ProductUrl'],
                        'format': product['BottleTextShort'],
                        'volume': product['VolumeText']
                    }

                    try:
                        entry['img'] = product['ProductImage']['ImageUrl']
                    except:
                        pass

                    products.append(entry)

        store_assortment.append(products)
    return store_assortment

app = Flask(__name__)
app.config['STORES'] = get_stores()

@app.route('/')
def index(stores=None):
    return render_template('index.html', stores=app.config['STORES'])

@app.route('/add_stores', methods=['GET', 'POST'])
def add_stores(stores=None, store1_info=None, store2_info=None):
    store1_id = request.args.get('store1')
    store2_id = request.args.get('store2')
    return render_template(
        'results.html',
        stores=compare_stores(store1_id, store2_id),
        store1_info=get_store_info(app.config['STORES'], store1_id),
        store2_info=get_store_info(app.config['STORES'], store2_id)
    )

if __name__ == "__main__":
    app.run(debug=True)
