# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from geonode.layers.units import *

LAYER_ATTRIBUTE_NUMERIC_DATA_TYPES = [
    'xsd:byte',
    'xsd:decimal',
    'xsd:double',
    'xsd:int',
    'xsd:integer',
    'xsd:long',
    'xsd:negativeInteger',
    'xsd:nonNegativeInteger',
    'xsd:nonPositiveInteger',
    'xsd:positiveInteger',
    'xsd:short',
    'xsd:unsignedLong',
    'xsd:unsignedInt',
    'xsd:unsignedShort',
    'xsd:unsignedByte',
]

MONITOR_FIELDS = (
    ('MASA_SECO','Masa (seco)'),
    ('MASA_HUMEDO','Masa (húmedo)'),
    ('VOLUMEN_SECO','Volumen (seco)'),
    ('VOLUMEN_HUMEDO','Volumen (húmedo)'),
    ('RENDIMIENTO_SECO','Rendimiento (seco)'),
    ('RENDIMIENTO_HUMEDO','Rendimiento (húmedo)'),
    ('FLUJO','Flujo'),
    ('HUMEDAD','Humedad'),
    ('ALTITUD','Altitud'),
    ('ANCHO','Ancho'),
    ('DISTANCIA','Distancia'),
    ('VELOCIDAD','Velocidad'),
    ('TIEMPO','Tiempo'),
)


MONITOR_FIELD_MAGNITUDES = {
    'MASA_SECO': units.kg,
    'MASA_HUMEDO': units.kg,
    'VOLUMEN_SECO': units.l,
    'VOLUMEN_HUMEDO': units.l,
    'RENDIMIENTO_SECO': (units.ton / units.ha),
    'RENDIMIENTO_HUMEDO': (units.ton / units.ha),
    'FLUJO': (units.kg / units.sec),
    # ('HUMEDAD', ),
    'ALTITUD': units.m,
    'ANCHO': units.m,
    'DISTANCIA': units.m,
    'VELOCIDAD': (units.km / units.sec),
    'TIEMPO': units.sec,
}

#MAGNITUDES = YIELD_MAGNITUDES + SPEED_MAGNITUDES + FLOW_MAGNITUDES + WEIGHT_MAGNITUDES + \
#             VOLUME_MAGNITUDES + DISTANCE_MAGNITUDES + TIME_MAGNITUDES

