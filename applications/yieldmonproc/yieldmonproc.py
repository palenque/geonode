# -*-encoding:utf8

import cherrypy
import os
import simplejson
import requests
from mako.lookup import TemplateLookup
import urllib
import urlparse
import subprocess
import sh
import dateutil.parser


class Saga_cmd(object):
    def __getattr__(self, attr):
        def subcmd(*args, **kwargs):
            args = [attr] + list(args)
            for k,v in kwargs.items():
                args.extend(['-%s' % k,'"%s"' % v])
            return sh.saga_cmd(*args)
        return subcmd
saga_cmd = Saga_cmd()

class YieldMonitorProcessing(object):
    lookup = TemplateLookup(directories=[os.path.join(os.path.dirname(__file__),'templates')])
    palenque_api_url = palenque_url + '/api'
    username = 'yieldmonproc'
    # diego
    palenque_url = 'http://localhost:8000'
    api_key = 'bd51709e7c2a867e6debb058fbc99e321253e02e'
    #production
    #palenque_url = 'http://localhost'
    #api_key = '07c3e6d390556fb11393ed793aecaebbc5d7a321'

    @cherrypy.expose
    def widget(self):
        resp = requests.get('%s/layers/resolve_user' % self.palenque_url,
            cookies = dict([(k,v.value) for k,v in cherrypy.request.cookie.items()]))

        user = ''
        if resp.ok:
            user = simplejson.loads(resp.text).get('user','')
        data = self.yield_monitors('base',user)        
        templ = self.lookup.get_template('widget.html')
        return templ.render(username=user, data=data)

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
        layer_type = 'yield'
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
                product=obj['metadata'].get('producto','Not specified'), #category_description'],
                abstract='Rasterización a partir del campo masa_humedo',
                date=dateutil.parser.parse(obj['date']).strftime('%d/%m/%y'),
                processed=any(x for x in obj['internal_links_forward'] if x['name'] == 'rasterized'),
                title=obj['title']))
        ans=dict(status='ok',objects=objs)
        return ans

    def process_layer(self, typename):
	fname_in = '%s.shp' % typename
	fname_out = '%s_rasterized.tiff' % typename
	pwd = str(sh.pwd()).strip()
        try:
            sh.cd('/tmp/layer')
            sh.rm("-rf",sh.glob('*'))
            sh.unzip('../layer.zip')
	    saga_cmd.shapes_points("Points Filter", POINTS=fname_in, FIELD="MASA_HUMEDO", FILTER="tmp1.shp", RADIUS=100, MINNUM=25, MAXNUM=200, METHOD=4, PERCENT=15)
	    saga_cmd.shapes_points("Points Filter", POINTS="tmp1.shp", FIELD="MASA_HUMEDO", FILTER="tmp2.shp", RADIUS=100, MINNUM=25, MAXNUM=200, METHOD=5, PERCENT=90)
    	    saga_cmd.grid_gridding("Shapes to Grid", INPUT="tmp2.shp", FIELD="MASA_HUMEDO", MULTIPLE=4, LINE_TYPE=0, GRID_TYPE=3, USER_SIZE=0.0001, TARGET=0, USER_GRID="tmp3.sgrd")
	    saga_cmd.grid_tools("Close Gaps", INPUT="tmp3.sgrd", RESULT="tmp4.sgrd")
	    saga_cmd.shapes_points("Convex Hull", SHAPES="tmp2.shp", HULLS="tmphull.shp", POLYPOINTS=0)
	    saga_cmd.shapes_grid("Clip Grid with Polygon", INPUT="tmp4.sgrd", OUTPUT="tmp5.sgrd", POLYGONS="tmphull.shp")
	    saga_cmd.grid_filter("Gaussian Filter", INPUT="tmp5.sgrd", RESULT="tmp6", SIGMA=3, MODE=1, RADIUS=50)

	    sh.gdal_translate("-of", "gtiff", "tmp6.sdat", fname_out)
        finally:
	    sh.cd(pwd)
	return '/tmp/layer/%s' % fname_out


    def download(self, url, typename):
        if not os.path.exists('/tmp/layer'):
            os.makedirs('/tmp/layer')

        q = urlparse.urlparse(url)
        q = q._replace(netloc='%s:%s@%s' % (self.username,self.api_key,q.netloc))
        url = urlparse.urlunparse(q)
        urllib.urlretrieve(url, "/tmp/layer.zip")

        #return self.process_layer(typename)
        return 'out.tiff'

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

        # download the data
        shape_url = (x for x in layer['links'] if x['mime'] == "SHAPE-ZIP").next()
        print shape_url['url']
        fname_out = self.download(shape_url['url'], layer['typename'].split(':')[-1])

        # upload new layer
        params = {'username': self.username, 'api_key': self.api_key}
        files = {'base_file': (fname_out,open(fname_out))}
        metadata = layer['metadata']        
        data = {
            'charset': 'UTF-8',
            'permissions': simplejson.dumps({'users': {}, 'groups': {}}),
            'layer_type': 'yield_raster',
            'owner': username, 
            'metadata': simplejson.dumps(metadata),
            'attributes': simplejson.dumps(
                [{"attribute":"GRAY_INDEX","mapping":"masa_humedo","magnitude":"kg"}])
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


cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': 3000,
                       })

cherrypy.quickstart(YieldMonitorProcessing())
