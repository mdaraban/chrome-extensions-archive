import glob
import extruct
import json
import os.path
import re
import io, shutil
from extruct.w3cmicrodata import MicrodataExtractor

import sys
from subprocess import *
from shlex import split


from zipfile import ZipFile, BadZipFile

from bs4 import BeautifulSoup

mde = MicrodataExtractor()

def microdata(html):
    microdata = mde.extract(html)['items'][0]['properties']
    def attrget(item, key):
        keys = key.split('.')
        for key in keys:
            item = item.get(key, {})
        if item == {}: return None
        return item
    keys = (
        'name',
        'version',
        'aggregateRating.properties.ratingCount',
        'aggregateRating.properties.ratingValue',
        'image',
        'offers.properties.price'
    )
    return {key:attrget(microdata, key) for key in keys}

def pagemap_extract(html, data):
    pagemap = re.findall(r"(<PageMap>.*</PageMap>)", html, re.MULTILINE)[0]
    soup = BeautifulSoup(pagemap, "lxml")
    for attr in soup.find_all('attribute'):
        data[attr['name']] = attr.text


def scrap(html, data):
    soup = BeautifulSoup(html, "lxml")
    data['full_description'] = soup.find('pre').text.strip()


def parse_page(ext_id):
    filename = 'pages/{ID}.html'.format(ID=ext_id)
    if os.path.isfile(filename):
        with open(filename) as f:
            html = f.read().strip()
            if len(html) == 0:
                print('-- NEED TO RE-DOWNLOAD THIS PAGE')
                return {}
            data = microdata(html)
            data['pagemap'] = pagemap_extract(html, data)
            data['scrap'] = scrap(html, data)
            return data
    else:
        return {}

def decomment(json_text):
    command = split('nodejs decomment.js')
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.stdin.write(json_text.encode('utf-8'))
    result = process.communicate()[0].decode('utf-8')
    return result

def extract_manifest(ext_id):
    debug = False
    crx_file = 'crx/{ID}.crx'.format(ID=ext_id)
    if os.path.isfile(crx_file):
        size = os.path.getsize(crx_file)
        if size == 0:
            print('fucking empty downloads')
            return
        try:
            with ZipFile(crx_file) as myzip:
                if debug:
                    #""" #save file to debug later
                    source = myzip.open('manifest.json')
                    target = open('lol.json', "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    #"""
                with myzip.open('manifest.json') as myfile:
                    text = myfile.read()
                    #if debug: print(text)
                    try:
                        text = text.decode('utf-8-sig')
                    except:
                        text = text.decode('latin-1')
                    if debug: print(text)
                    try:
                        return json.loads(text, strict=False)
                    except Exception as e:
                        print(e)
                        text = decomment(text)
                        return json.loads(text, strict=False)
        except BadZipFile:
            print('fucking interrupted downloads')
    else:
        print(crx_file,'does not exist')

assert decomment("{/*lol*/}").strip() == """{}"""

#test edge case
extract_manifest('pecialgmmceelbdjljhdmifgnnplgbkp')
extract_manifest('epinhnanplaehkdjopehcackkoccdpja')
extract_manifest('fjncnaogemmlhdgigpjlmjaalmmagnpf')
extract_manifest('eceafjaikogdiipibmbcaeopdgpgkfjm')
extract_manifest('ndmkfdienaldgalnecedmgklhgoaanej')
extract_manifest('dcibengndfkldipifhfochlcjmcfmnij')
extract_manifest('cahainciljeejkajijkbhgjlbneeggfj')

DATA = []

def save():
    with open('enriched.json','w') as f:
        json.dump(DATA, f, indent=2, sort_keys=True)

for i, url in enumerate(json.load(open('extension_list.json'))):
    ext_id = url.split('/')[-1]
    print(ext_id)
    data = parse_page(ext_id)
    data['url'] = url
    data['ext_id'] = ext_id
    manifest = extract_manifest(ext_id)
    data['manifest'] = manifest
    DATA.append(data)

    if i % 1000 == 0:
        save()

save()