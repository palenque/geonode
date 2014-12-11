# -*- encoding: utf-8 -*-

import json, os, zipfile, urllib
import requests

monitores_serie_1 = [
    ('aTv7onqLob',  'soja'    ,'2010-2011',),
    ('tYo5PXv36y',  'soja'    ,'2010-2011',),
    ('q7ibHSwKD3',  'maiz'    ,'2006-2007',),
    ('vRnTHipuVX',  'soja'    ,'2007-2008',),
    ('Ns8O5opoRJ',  'soja'    ,'2010-2011',),
    ('e3eaNao9TN',  'soja'    ,'2008-2009',),
    ('GP4On9Ddye',  'soja'    ,'2006-2007',),
    ('wchbE5C3Ef',  'soja'    ,'2010-2011',),
    ('QM5GJyMyhO',  'soja'    ,'2010-2011',),
    ('FBywmD1yGF',  'soja'    ,'2008-2009',),
    ('h4NUIj6fKK',  'maiz'    ,'2011-2012',),
    ('2YV1VIEWHU',  'soja'    ,'2007-2008',),
    ('luBOe8JMRE',  'maiz'    ,'2011-2012',),
    ('CM10vKKnrA',  'soja'    ,'2012-2013',),
    ('vtny7ohS9l',  'soja'    ,'2010-2011',),
    ('J8p77wvoQ5',  'soja'    ,'2006-2007',),
    ('UtJMa0MEcB',  'soja'    ,'2011-2012',),
    ('2jhNv97MWs',  'maiz'    ,'2011-2012',),
    ('HKZ1oBdfft',  'maiz'    ,'2008-2009',),
    ('sfsCy3LQmO',  'soja'    ,'2006-2007',),
    ('9GHRdrRz65',  'soja'    ,'2007-2008',),
    ('ANPjOEv2ub',  'maiz'    ,'2009-2010',),
    ('vnHozFqKfd',  'maiz'    ,'2007-2008',),
    ('iot0GXrhWx',  'soja'    ,'2009-2010',),
    ('yh9FW8VNTB',  'soja'    ,'2011-2012',),
    ('hUaqk7zFUS',  'soja'    ,'2012-2013',),
    ('QVdQRpfttd',  'soja'    ,'2009-2010',),
    ('bKvKvEmsYz',  'trigo'   ,'2011-2012',),
    ('1BzuCFS4xz',  'trigo'   ,'2004-2005',),
    ('9Qows7fi2B',  'trigo'   ,'2009-2010',),
    ('dgbjwuiJtQ',  'trigo'   ,'2006-2007',),
    ('Yrvq2ZRwJi',  'trigo'   ,'2008-2009',),
    ('afmDrMsdMV',  'trigo'   ,'2005-2006',),
    ('zyJJA9Rj3i',  'trigo'   ,'2007-2008',),
    ('2c3D1hLK4m',  'cebada'  ,'2011-2012',),
    ('GhcCYfl1c5',  'cebada'  ,'2011-2012',),
]


# geonode = 'localhost:8000'
# username = 'tinkamako'
# api_key = '31c72b0d06a9174a89862e13dd7c86d6d9b26fd5'

geonode = 'protopalenque.ddns.net'
username = 'palenque'
api_key = '1cbfdc7c09a678e82c7213845979730105f57589'


def import_monitors():
    for _id, producto, campania in monitores_serie_1:

        filename = _id
        root = _id

        if not os.path.exists(root):
            os.mkdir(root)
        path = os.path.join(root, filename)

        url = 'http://agrodatos.info/monitores/serie-1/%s.zip' % _id
        print 'downloading', url, '...'
        urllib.URLopener().retrieve(url, path)

        if zipfile.is_zipfile(path):
            zipfile.ZipFile(file(path)).extractall(root)

            shapefile = {}
            for f in os.listdir(root):
                if f.split('.')[-1] in ['dbf', 'prj', 'shp', 'shx']:
                    shapefile[f.split('.')[-1]] = file(os.path.join(root, f))

            print shapefile

            files = {
                'base_file': shapefile.get('shp'),
                'dbf_file': shapefile.get('dbf'),
                'prj_file': shapefile.get('prj'),
                'shx_file': shapefile.get('shx')
            }

            attributes = [
                {"attribute": "ELEVACION", "mapping": "ALTITUD", "magnitude": "m"}, 
                {"attribute":"ANCHO", "mapping": "ANCHO", "magnitude": "m"},
                {"attribute":"DISTANCIA", "mapping": "DISTANCIA", "magnitude": "m"},
                {"attribute":"FLUJO", "mapping": "FLUJO", "magnitude": "kg/s"},
                {"attribute":"MASA", "mapping": "MASA_HUMEDO", "magnitude": "kg"},
            ]

            metadata = {
                'campana': campania, 
                'producto': producto.capitalize()
            }

            url = 'http://%s/api/layers/?username=%s&api_key=%s' % (geonode, username, api_key)

            print 'uploading', _id, '...'
            r = requests.post(
                url, 
                files=files,
                data={
                    'metadata': json.dumps(metadata),
                    'attributes': json.dumps(attributes),
                    'charset':'UTF-8',
                    'keywords': u"Agricultura de precisión, Mapa de rinde",
                    'layer_type': 'monitor',
                    'layer_title': _id,
                    # 'abstract': resource['description'],
                    'permissions': '{"users":{},"groups":{}}'             
                }
            )

            print
            print _id, r.ok, '' if r.ok else r.content
            print '.'*80



def import_layers():
    packages = requests.get('http://agrodatos.info/api/3/action/package_list').json()['result']
    for package in packages:

        result = requests.get('http://agrodatos.info/api/3/action/package_show?id=%s' % package).json()['result']
        resources = result['resources']
        tags = [t['name'] for t in result['tags']]
        purpose = result['notes']


        for resource in resources:

            if resource['format'] not in ['shapefile', 'geo:vector']:
                continue

            filename = os.path.basename(resource['url'])
            root = resource['id']
            
            if not os.path.exists(root):
                os.mkdir(root)
            path = os.path.join(root, filename)
            print 'descargando', resource['url'], '...'
            urllib.URLopener().retrieve(resource['url'], path)

            if zipfile.is_zipfile(path):
                zipfile.ZipFile(file(path)).extractall(root)

                shapefile = {}
                for f in os.listdir(root):
                    if f.split('.')[-1] in ['dbf', 'prj', 'shp', 'shx']:
                        shapefile[f.split('.')[-1]] = file(os.path.join(root, f))

                files = {
                    'base_file': shapefile.get('shp'),
                    'dbf_file': shapefile.get('dbf'),
                    'prj_file': shapefile.get('prj'),
                    'shx_file': shapefile.get('shx')
                }

                print tags, purpose,{
                    'keywords': tags,
                    'purpose': purpose,
                    'layer_title': resource['name'],
                    'abstract': resource['description'],
                    'permissions': '{"users":{},"groups":{}}'             
                }
                print resource
                print


                url = 'http://%s/api/layers/?username=%s&api_key=%s' % (geonode, username, api_key)
                print 'cargando', resource['name'], '...'
                try:                   
                    r = requests.post(
                    url, 
                    files=files,
                    data={
                        'charset':'UTF-8',
                        'keywords': tags,
                        'abstract': purpose,
                        'layer_title': resource['name'],
                        # 'purpose': resource['description'],
                        'permissions': '{"users":{},"groups":{}}'             
                    }
                    )
                    print
                    print resource['name'], r.ok, '' if r.ok else r.content
                    print '.'*80

                except Exception as e:
		    print e
                finally:
                   import shutil
                   shutil.rmtree(root)
          

if __name__ == '__main__':
    #import_monitors()
    import_layers()
