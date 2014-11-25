import cherrypy
import os
import simplejson
import requests
from mako.lookup import TemplateLookup
import urllib

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

    def download(self, layer_id):
        params={'api_key':self.api_key, 'username':self.username, 'resource__id': layer_id, 'mime':'SHAPE-ZIP'}
        url = '%s/link/' % self.palenque_api_url
        resp = requests.get(url, params=params)
        if not resp.ok:
            ans = dict(status='error', code=resp.status_code, message=resp.text or resp.reason)
            return ans

        data = simplejson.loads(resp.text)
        import ipdb; ipdb.set_trace()
        urllib.urlretrieve(data['objects'][0]['url'], "layer_%s.zip" % layer_id)


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

        # upload new layer
        params = {'username': self.username, 'api_key': self.api_key}
        files = {'base_file': open('/Users/diego/tmp2/out.tiff', 'r')}
        data = {'charset':'UTF-8', 'layer_title':'%s (raster)' % layer['title'], 'owner':username}
        headers = {'Accept-Language':'en'}
        url = '%s/layers/' % self.palenque_api_url
        resp = requests.post(url, headers=headers, files=files, params=params, data=data)
        if not resp.ok:
            ans = dict(status='error', message=resp.text)
            return ans

        url = resp.headers['location']
        new_layer_id = url.split('/')[-2]

        # link new layer
        url = '%s/layers/%s/links/' % (self.palenque_api_url, layer_id)
        data = {'direction':'forward', 'target':'/api/layers/%s/' % new_layer_id, 'link_type': 'rasterized'}
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