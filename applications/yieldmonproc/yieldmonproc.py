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
    palenque_api_url = 'http://localhost:8000/api'
    username = 'app3'
    api_key = 'e5dd0825188c7e68ff9883f0bb98fbb2d67d2e68'

    @cherrypy.expose
    def index(self):
        templ = self.lookup.get_template('index.html')
        return templ.render()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def yield_monitors(self, type, username):

        if type != 'base': 
            ans = dict(status='error', message='invalid layer type: %s' % type)
            return ans
        layer_type = 'monitor'
        resp = requests.get('%s/layers' % self.palenque_api_url, 
            params=dict(owner__username=username, layer_type=layer_type, api_key=self.api_key, username=self.username))
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans
        data = simplejson.loads(resp.text)
        print data
        objs = []
        for obj in data['objects']:
            objs.append(dict(
                id=obj['id'],
                product=obj['category_description'],
                date=obj['date'],
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

        dirname = os.path.dirname(__file__)
        subprocess.call(os.path.join(dirname,'process_'
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def process(self, username, layer_id):
        # get original layer data
        resp = requests.get('%s/layers/%s' % (self.palenque_api_url,layer_id),
            params={'owner__username':username, 'api_key':self.api_key, 'username':self.username})
        if not resp.ok:
            ans = dict(status='error', code=resp.status_code, message=resp.text or resp.reason)
            return ans
        layer = simplejson.loads(resp.text)

        # download the data
        shape_url = (x for x in layer['links'] if x['mime'] == "SHAPE-ZIP").next()
        print shape_url['url']
        self.download(shape_url['url'])
        return "OK"

        # upload new layer
        params = {'username': self.username, 'api_key': self.api_key}
        files = {'base_file': open('out.tiff')}
        data = {'charset':'UTF-8', 'layer_title':'%s (raster)' % layer['title'], 'owner':username}
        headers = {'Accept-Language':'en'}
        url = '%s/layers/' % self.palenque_api_url
        resp = requests.post(url, headers=headers, files=files, params=params, data=data)
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans

        url = resp.headers['location']
        new_layer_id = url.split('/')[-2]

        # # link new layer
        # url = '%s/layers/%s/links/' % (self.palenque_api_url, layer_id)
        # data = {'direction':'forward', 'target':'/api/layers/%s/' % new_layer_id, 'link_type': 'rasterized'}
        # resp = requests.post(url, headers=headers, params=params, data=simplejson.dumps(data))
        # if not resp.ok:
        #     ans = dict(status='error', message=resp.text)
        #     return ans

        # ok!!
        ans = dict(status='ok', message=resp.text)
        return ans


cherrypy.config.update({'server.socket_host': '127.0.0.1',
                        'server.socket_port': 3000,
                       })

cherrypy.quickstart(YieldMonitorProcessing())