from django.db.models import signals

from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer
from geonode.people.models import Profile

from geonode.geoserver.signals import geoserver_pre_save
from geonode.geoserver.signals import geoserver_pre_delete
from geonode.geoserver.signals import geoserver_post_save
from geonode.geoserver.signals import geoserver_post_save_map
from geonode.geoserver.signals import geoserver_pre_save_maplayer

from tastypie.models import create_api_key

signals.pre_save.connect(geoserver_pre_save, sender=Layer)
signals.pre_delete.connect(geoserver_pre_delete, sender=Layer)
signals.post_save.connect(geoserver_post_save, sender=Layer)
signals.pre_save.connect(geoserver_pre_save_maplayer, sender=MapLayer)
signals.post_save.connect(geoserver_post_save_map, sender=Map)

# signal to generate api key 
signals.post_save.connect(create_api_key, sender=Profile)
