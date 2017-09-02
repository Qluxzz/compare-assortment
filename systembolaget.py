import os
import time
import requests
from lxml import etree
from slugify import slugify
import urllib.request

CATEGORY = {
    'Alkoholfritt': 'alkoholfritt',
    'Amerikansk whiskey': 'sprit',
    'Aniskryddad sprit': 'sprit',
    'Aperitif': 'aperitif-dessert',
    'Armagnac': 'sprit',
    'Bitter': 'sprit',
    'Blå mousserande': 'aperitif-dessert',
    'Blå stilla': 'aperitif-dessert',
    'Blanddrycker': 'cider-och-blanddrycker',
    'Brandy och Vinsprit': 'sprit',
    'Calvados': 'sprit',
    'Champange': 'mousserande-viner',
    'Cider': 'cider-och-blanddrycker',
    'Cognac': 'sprit',
    'Drinkar och Cocktails': 'sprit',
    'Fruktvin': 'aperitif-dessert',
    'Genever': 'sprit',
    'Gin': 'sprit',
    'Glögg och Glüwein': 'aperitif-dessert',
    'Grappa och Marc': 'sprit',
    'Irländsk whiskey': 'sprit',
    'Kanadensisk whisky': 'sprit',
    'Kryddad sprit': 'sprit',
    'Likör': 'sprit',
    'Madeira': 'aperitif-dessert',
    'Maltwhisky': 'sprit',
    'Mjöd': 'aperitif-dessert',
    'Montilla': 'aperitif-dessert',
    'Mousserande vin': 'mousserande-viner',
    'Okryddad sprit': 'sprit',
    'Öl': 'ol',
    'Övrig sprit': 'sprit',
    'Övrigt starkvin': 'aperitif-dessert',
    'Portvin': 'aperitif-dessert',
    'Punsch': 'sprit',
    'Röda': 'roda-viner',
    'Rom': 'sprit',
    'Rosé': 'roseviner',
    'Rosévin': 'roseviner',
    'Rött vin': 'roda-viner',
    'Sake': 'aperitif-dessert',
    'Sherry': 'aperitif-dessert',
    'Skotsk maltwhisky': 'sprit',
    'Smaksatt sprit': 'sprit',
    'Smaksatt vin': 'aperitif-dessert',
    'Vermouth': 'aperitif-dessert',
    'Vin av flera typer': 'aperitif-dessert',
    'Vita': 'vita-viner',
    'Vitt vin': 'vita-viner',
    'Whisky': 'sprit',
    'Tequila och Mezcal': 'sprit',
    'Sprit av frukt': 'sprit'
}

BASEURL = 'https://www.systembolaget.se/'

API_URL = 'api/assortment/{}/xml'

FILE_LOCATION = [
    'products',
    'stores',
    'stock'
]

ONEDAY = 86400

def get_product_url(product_url):
    return BASEURL + 'dryck/' + product_url

def get_api_url(location):
    return BASEURL + API_URL.format(location)

def should_update_files():
    """ Check if the files are older than one day and update files if true """
    if not os.path.exists('data/'): 
        os.makedirs('data/')

    for file in FILE_LOCATION:
        path = 'data/{}.xml'.format(file)
        if os.path.exists(path) != True or int(time.time()) - os.stat(path).st_mtime > ONEDAY:
            update_file(file, path)

def update_file(file, path):
    urllib.request.urlretrieve(get_api_url(file), path)
    print('Updated {}'.format(path))

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
    return next((x for x in stores if x['nr'] == store_id), {})

def remove_duplicates(stores):
    """ Remove duplicates between stores """
    return [
        [x for x in stores[0] if x not in stores[1]],
        [x for x in stores[1] if x not in stores[0]]
    ]

def get_store_balance(store_numbers):
    try:
        stock = etree.parse('data/stock.xml').getroot()
    except OSError:
        print('Failed to load stock.xml')
        return

    products = []

    for store_nr in store_numbers:
        try:
            store = stock.find('Butik/[@ButikNr="{}"]'.format(store_nr))
        except:
            return False
        products.append([product.text for product in store])

    return products

def get_stores():
    """ Parse store information from xml file and return sorted list """
    try:
        store_information = etree.parse('data/stores.xml').getroot()
    except OSError:
        print('Failed to load data/stores.xml')
        return

    stores = []
    for child in store_information.iter('ButikOmbud'):
        # Check if store and not pick up point
        if '-' not in child[1].text:
            stores.append({
                'nr': child[1].text,
                'place': child[6].text.title(),
                'name': child[2].text if child[2].text else child[3].text
            })
    return sorted(stores, key=lambda store: store['place'])

def compare_stores(store_one_id, store_two_id):
    """ Compare the products between two stores """
    products = get_products(get_store_balance([store_one_id, store_two_id]))
    print(remove_duplicates(products))

def get_products(stores):
    """ Get products from stores """
    try:
        products = etree.parse('data/products.xml').getroot()
    except OSError:
        print('Failed to load products.xml')
        return

    data = [
        {'name': 'price', 'string': 'Prisinklmoms'},
        {'name': 'name', 'string': 'Namn'},
        {'name': 'name2', 'string': 'Namn2'},
        {'name': 'category', 'string': 'Varugrupp'},
        {'name': 'type', 'string': 'Typ'},
        {'name': 'style', 'string': 'Stil'},
        {'name': 'country', 'string': 'Ursprunglandnamn'},
        {'name': 'format', 'string': 'Forpackning'},
        {'name': 'volume', 'string': 'Volymiml'},
        {'name': 'id', 'string': 'nr'}
    ]

    stores_inventory = []

    for store in stores:
        inventory = []
        
        for product in store:
            info = {}

            try:
                product = products.xpath('//artikel/nr[text()="{}"]'.format(product))[0].getparent()
            except:
                #print('Failed to find product ')
                continue

            if product.find('Varugrupp').text != 'Öl':
                continue

            for entry in data:
                try:
                    info[entry['name']] = product.find(entry['string']).text
                except:
                    print('Failed to find {}'.format(entry['name']))
                    continue
            try:
                info['url'] = '{}/{}-{}'.format(CATEGORY[info['category']], slugify(info['name']), info['id'])
            except KeyError as error:
                #print(error)
                pass
            inventory.append(info)
        stores_inventory.append(inventory)

    return stores_inventory

def main():
    should_update_files()
    compare_stores(2002, 2004)

if __name__ == "__main__":
    main()
