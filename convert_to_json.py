import os
import sys
import time
import sqlite3
import re
import urllib.request
import json
from lxml import etree
from slugify import slugify
from tqdm import tqdm
import pprint

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

def create_tables(db):
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
            storeId INT
        )'''
    ]

    c = db.cursor()
    for table in tables:
        c.execute(table)
    db.commit()

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

def convert_products(db):
    if not os.path.exists('products'):
        os.makedirs('products')

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

    c = db.cursor()
    pbar = tqdm(len(products), desc='Add products to database')
    for product in products:
        info = {}

        id = int(product.find('nr').text)

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
                id)
        except KeyError:
            continue

        for replace in replace_info:
            if replace['name'] in info:
                info[replace['name']] = insert_or_get_existing(
                    replace['table'],
                    replace['name'],
                    info[replace['name']],
                    db,
                    c
                )

        info['id'] = id

        try:
            c.execute('''INSERT INTO products VALUES (
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

    db.commit()

def insert_or_get_existing(table, column, data, db, c):
    c.execute('SELECT rowid FROM {} WHERE {}=?'.format(table, column), (data,))

    row = c.fetchone()

    if row is None:
        c.execute('INSERT OR IGNORE INTO {} ({}) VALUES (?)'.format(table, column), (data,))
        return c.lastrowid
    else:
        return row[0]

def convert_stock(db):
    try:
        store_stock = etree.parse('data/stock.xml').getroot()
    except:
        print('Failed to open data/stock.xml')
        return

    stores = store_stock.xpath('/ButikArtikel/Butik')
    pbar = tqdm(total=len(stores), desc='Split up stock per store')

    c = db.cursor()

    for store in stores:
        nr = store.attrib['ButikNr']

        products = [int(product) for product in store.xpath('ArtikelNr/text()')]

        if len(products) == 0:
            continue

        for product in products:
            c.execute('INSERT INTO stock VALUES (?, ?)', [product, nr])

        pbar.update(1)
    db.commit()

def get_store_products(storeNr, db):
    c = db.cursor()

    parameters = (storeNr,)

    c.execute('SELECT * FROM stock ORDER BY storeId')

def main():
    should_update_files()

    try:
        db = sqlite3.connect('products.db')
    except:
        print('Failed to open database')
        sys.exit()

    create_tables(db)
    #convert_stock(db)
    convert_products(db)
    db.close()
if __name__ == "__main__":
    main()
