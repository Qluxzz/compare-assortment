import json
import os
import pprint
import re
import sqlite3
import sys
import time
import urllib.request

from lxml import etree
from slugify import slugify
from tqdm import tqdm

PP = pprint.PrettyPrinter()

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

ONEDAY = 86400

FILE_LOCATION = [
    'products',
    'stores',
    'stock'
]

def create_tables(cursor):
    tables = [
        '''CREATE TABLE IF NOT EXISTS products (
            id INT UNIQUE,
            name TEXT,
            name2 TEXT,
            price DECIMAL,
            category SMALLINT,
            url TEXT,
            country SMALLINT,
            format SMALLINT,
            volume DECIMAL,
            style INT,
            type INT
        )''',
        '''CREATE TABLE IF NOT EXISTS categories (
            category TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS types (
            type TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS styles (
            style TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS formats (
            format TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS countries (
            country TEXT UNIQUE
        )''',
        '''CREATE TABLE IF NOT EXISTS stock (
            productId INT,
            storeId TEXT,
            category INT,
            PRIMARY KEY (productId, storeId)
        )'''
    ]
    [cursor.execute(table) for table in tables]

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

def convert_products(cursor):
    try:
        productsfile = etree.parse('data/products.xml').getroot()
    except:
        print('Failed to load data/products.xml')
        pass

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
    ]

    replace_info = [
        {'name': 'category', 'table': 'categories'},
        {'name': 'country', 'table': 'countries'},
        {'name': 'format', 'table': 'formats'},
        {'name': 'style', 'table': 'styles'},
        {'name': 'type', 'table': 'types'}
    ]

    products_information = {}
    products = productsfile.xpath('/artiklar/artikel')

    pbar = tqdm(len(products), desc='Add products to database')
    for product in products:
        info = {}

        productId = int(product.find('nr').text)

        for entry in data:
            info[entry['name']] = ""
            try:
                text = product.find(entry['string']).text
                if len(text) > 0:
                    info[entry['name']] = text
            except:
                #print('Failed to find {}'.format(entry['name']))
                continue
        try:
            info['url'] = '{}/{}-{}'.format(
                CATEGORY[info['category']],
                slugify(info['name']),
                productId)
        except KeyError:
            continue

        for replace in replace_info:
            if replace['name'] in info:
                info[replace['name']] = insert_or_get_existing(
                    replace['table'],
                    replace['name'],
                    info[replace['name']],
                    cursor
                )

        info['id'] = productId

        try:
            cursor.execute('''INSERT INTO products VALUES (
                :id,
                :name,
                :name2,
                :price,
                :category,
                :url,
                :country,
                :format,
                :volume,
                :style,
                :type
            )''', info)
        except sqlite3.OperationalError as error:
            PP.pprint([error, info])
            continue
        except sqlite3.ProgrammingError as error:
            PP.pprint([error, info])
            continue
        except KeyError as error:
            PP.pprint([error, info])
            continue
        except sqlite3.IntegrityError:
            continue

        pbar.update(1)

def insert_or_get_existing(table, column, data, cursor):
    cursor.execute('SELECT rowid FROM {} WHERE {}=?'.format(table, column), (data,))
    row = cursor.fetchone()

    if row is None:
        cursor.execute('INSERT OR IGNORE INTO {} ({}) VALUES (?)'.format(table, column), (data,))
        return cursor.lastrowid
    else:
        return row[0]

def convert_stock_to_json(cursor):
    if not os.path.exists('stores'):
        os.makedirs('stores')

    cursor.execute('SELECT * FROM stock ORDER BY storeId ASC, category ASC')

    current_store = None
    current_category = None

    products = {}

    db_stores = cursor.fetchall()
    pbar = tqdm(len(db_stores), desc='Converting store stock to json')
    for productId, storeNr, categoryNr in db_stores:
        if current_store is None:
            current_store = storeNr

        if current_category is None:
            current_category = categoryNr
            products[current_category] = []

        if storeNr != current_store:
            write_to_file(products, current_store)
            products.clear()
            current_store = storeNr

        if categoryNr != current_category:
            current_category = categoryNr
            products[current_category] = []
        products[current_category].append(productId)
        pbar.update(1)

def convert_products_to_json(cursor):
    if not os.path.exists('products'):
        os.makedirs('products')

    cursor.execute('SELECT * FROM products ORDER BY category ASC, id ASC')

    current_category = None

    products = {}

    db_products = cursor.fetchall()
    pbar = tqdm(len(db_products), desc='Converting product information to json')
    for product in db_products:
        if current_category is None:
            current_category = product[4]

        if product[4] != current_category:
            with open('products/{}.json'.format(current_category), 'w') as jsonfile:
                json.dump(products, jsonfile)
            products.clear()
            current_category = product[4]
        products[product[0]] = product[1:4] + product[5:]
        pbar.update(1)

def convert_stores_to_json():
    try:
        store_information = etree.parse('data/stores.xml').getroot()
    except:
        print('Failed to open data/stores.xml')
        return

    stores = store_information.xpath('/ButikerOmbud/ButikOmbud')

    store_json = []

    for store in stores:
        nr = store.xpath('Nr/text()')[0]

        if '-' in nr:
            continue
        try:
            name = store.xpath('Namn/text()')[0]
        except IndexError:
            name = store.xpath('Address1/text()')[0]

        city = store.xpath('Address4/text()')[0]
        store_json.append([nr, name, city.upper()])

    with open('stores/info.json', 'w') as jsonfile:
        json.dump(sorted(store_json, key=lambda x: x[2]), jsonfile)

def convert_misc_to_json(cursor):
    info = {}

    statements = [
        {'row': 'style', 'table': 'styles'},
        {'row': 'type', 'table': 'types'},
        {'row': 'country', 'table': 'countries'},
        {'row': 'format', 'table': 'formats'},
        {'row': 'category', 'table': 'categories'}
    ]

    for statement in statements:
        cursor.execute('SELECT rowid, {} FROM {}'.format(statement['row'], statement['table']))
        info[statement['table']] = {}
        for entry in cursor.fetchall():
            info[statement['table']][entry[0]] = entry[1]

    with open('info.json', 'w') as jsonfile:
        json.dump(info, jsonfile)

def write_to_file(products, storeNr):
    with open('stores/{}.json'.format(storeNr), 'w') as jsonfile:
        json.dump(products, jsonfile)

def convert_stock(cursor):
    try:
        store_stock = etree.parse('data/stock.xml').getroot()
    except:
        print('Failed to open data/stock.xml')
        return

    stores = store_stock.xpath('/ButikArtikel/Butik')
    pbar = tqdm(total=len(stores), desc='Split up stock per store')

    for store in stores:
        nr = store.attrib['ButikNr']

        products = [int(product) for product in store.xpath('ArtikelNr/text()')]

        if len(products) == 0:
            continue

        cursor.execute('''
            SELECT id, category 
            FROM products 
            WHERE id IN ({})
        '''.format(', '.join([str(x) for x in products])))

        for entry in cursor.fetchall():
            cursor.execute(
                'INSERT INTO stock VALUES (?, ?, ?)',
                (entry[0], nr, entry[1],)
            )
        pbar.update(1)

def main():
    should_update_files()
    try:
        database = sqlite3.connect(':memory:')
    except:
        print('Failed to open database')
        sys.exit()

    cursor = database.cursor()

    create_tables(cursor)
    convert_products(cursor)
    convert_stock(cursor)

    convert_stock_to_json(cursor)
    convert_products_to_json(cursor)
    convert_stores_to_json()
    convert_misc_to_json(cursor)
    database.close()

if __name__ == "__main__":
    main()
