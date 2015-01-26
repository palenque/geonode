# -*-encoding:utf8

import cherrypy
import os
import simplejson
import requests
from mako.lookup import TemplateLookup
import urllib
import urlparse
import subprocess

class YieldMonitorProcessing(object):
    lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__),'templates')])
    palenque_url = 'http://localhost:8000'
    palenque_api_url = palenque_url + '/api'
    username = 'yieldmonproc'
    api_key = 'bd51709e7c2a867e6debb058fbc99e321253e02e'

    @cherrypy.expose
    def index(self):
        resp = requests.get('%s/layers/resolve_user' % self.palenque_url,
            cookies = dict([(k,v.value) for k,v in cherrypy.request.cookie.items()]))

        user = ''
        if resp.ok:
            user = simplejson.loads(resp.text).get('user','')
        
        templ = self.lookup.get_template('index.html')
        return templ.render(username=user)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def yield_monitors(self, type, username):

        if type != 'base': 
            ans = dict(status='error', message='invalid layer type: %s' % type)
            return ans
        layer_type = 'monitor'
        resp = requests.get('%s/layers' % self.palenque_api_url, 
            params=dict(owner__username=username, layer_type__name=layer_type, api_key=self.api_key, username=self.username))
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans
        
        data = simplejson.loads(resp.text)
        
        objs = []
        for obj in data['objects']:
            objs.append(dict(
                uri=obj['resource_uri'],
                product=obj['supplemental_information'], #category_description'],
                abstract='Rasterización a partir del campo masa_humedo',
                date=obj['date'],
                processed=any(x for x in obj['internal_links_forward'] if x['name'] == 'rasterized'),
                title=obj['title']))
        ans=dict(status='ok',objects=objs)
        return ans

    def download(self, url):
        if not os.path.exists('/tmp/layer'):
            os.makedirs('/tmp/layer')
        subprocess.call(['rm','/tmp/layer/*'])

        q = urlparse.urlparse(url)
        q = q._replace(netloc='%s:%s@%s' % (self.username,self.api_key,q.netloc))
        url = urlparse.urlunparse(q)
        urllib.urlretrieve(url, "/tmp/layer/layer.zip")
        subprocess.call(['unzip','/tmp/layer/layer.zip'])

        # dirname = os.path.dirname(__file__)
        # subprocess.call(os.path.join(dirname,'process_'

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def process(self, username, resource_uri):
        # get original layer data
        resp = requests.get(urllib.basejoin(self.palenque_api_url,resource_uri),
            params={'username':self.username, 'api_key':self.api_key})
        if not resp.ok:
            ans = dict(status='error', code=resp.status_code, message=resp.text or resp.reason)
            return ans
        layer = simplejson.loads(resp.text)

        # # # download the data
        # # shape_url = (x for x in layer['links'] if x['mime'] == "SHAPE-ZIP").next()
        # # print shape_url['url']
        # # self.download(shape_url['url'])
        # # return "OK"

        # upload new layer
        params = {'username': self.username, 'api_key': self.api_key}
        files = {'base_file': open('out.tiff')}
        metadata = layer['metadata']        
        data = {
            'charset': 'UTF-8', 
            'layer_type': 'yield_raster',
            'owner': username, 
            'metadata': simplejson.dumps(metadata),
            'attributes': simplejson.dumps(
                [{"attribute":"GRAY_INDEX","mapping":"MASA_HUMEDO","magnitude":"kg"}])
        }
        headers = {'Accept-Language':'en'}
        url = '%s/layers/' % self.palenque_api_url
        resp = requests.post(url, headers=headers, files=files, params=params, data=data)
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans

        new_layer_id = urlparse.urlparse(resp.headers['location']).path

        # link new layer
        url = '%s/internal_links/' % self.palenque_api_url
        data = {
            'name': 'rasterized', 
            'source': layer['resource_uri'], 
            'target': new_layer_id}
        headers['Content-Type'] = 'application/json'
        resp = requests.post(url, headers=headers, params=params, data=simplejson.dumps(data))
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans

        # ok!!
        ans = dict(status='ok', message=resp.text)
        return ans


cherrypy.config.update({'server.socket_host': '127.0.0.1',
                        'server.socket_port': 3000,
                       })

cherrypy.quickstart(YieldMonitorProcessing())
