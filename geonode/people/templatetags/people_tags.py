#-*- encoding:utf8

from django import template
from django.utils.translation import ugettext as _

from geonode.people.enumerations import PROFILE

register = template.Library()

@register.simple_tag
def profile_icon(profile,css=''):
    if profile == PROFILE.APP:
        css += ' fa fa-cubes'
    elif profile == PROFILE.ORGANIZATION:
        css += ' fa fa-bank'
    elif profile == PROFILE.DEVELOPER:
        css += ' fa fa-lightbulb-o' 
    elif profile == PROFILE.CONTRACTOR:
        css += ' fa fa-briefcase' 
    else:
        css += ' fa fa-user'
    return '<i class="%s"></i>' % css

@register.simple_tag
def profile_description(profile):
    if profile == PROFILE.CONTRACTOR:
        return """Proveedor de tecnología y servicios agropecuarios. <br/>Consume información pública y de 
        sus propios clientes, y genera información que en general queda en poder de los clientes"""

    elif profile == PROFILE.DEVELOPER:
        return """Desarrollador de software.<br/>Utiliza las APIs del sistema para acceder a información pública y 
        de los clientes"""

    elif profile == PROFILE.ORGANIZATION:
        return """Organización pública o privada.<br/>Genera y consume información pública."""

    elif profile == PROFILE.USER:
        return """Productor agropecuario. Utiliza Palenque para contratar servicios y aplicaciones y para 
        resguardar su información privada"""

