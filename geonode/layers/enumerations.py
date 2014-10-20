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


VOLUME_MAGNITUDES = (
    ('m3','m3'),
    ('cm3','cm3'),
)

YIELD_MAGNITUDES = (
    ('ton/ha','ton/ha'),
)

SPEED_MAGNITUDES = (
    ('m/s','m/s'),
    ('km/h','km/h'),
)

FLOW_MAGNITUDES = (
    ('kg/s','kg/s'),
)

DISTANCE_MAGNITUDES = (
    ('m','m'),
    ('cm','cm'),
)

TIME_MAGNITUDES = (
    ('s','s'),
    ('min','min'),
    ('h','h'),
)

WEIGHT_MAGNITUDES = (
    ('kg','kg'),
    ('gram','gr'),
)

MONITOR_FIELD_MAGNITUDES = (
    ('MASA_SECO', WEIGHT_MAGNITUDES),
    ('MASA_HUMEDO', WEIGHT_MAGNITUDES),
    ('VOLUMEN_SECO', VOLUME_MAGNITUDES),
    ('VOLUMEN_HUMEDO', VOLUME_MAGNITUDES),
    ('RENDIMIENTO_SECO', YIELD_MAGNITUDES),
    ('RENDIMIENTO_HUMEDO', YIELD_MAGNITUDES),
    ('FLUJO', FLOW_MAGNITUDES),
    # ('HUMEDAD', ),
    ('ALTITUD', DISTANCE_MAGNITUDES),
    ('ANCHO', DISTANCE_MAGNITUDES),
    ('DISTANCIA', DISTANCE_MAGNITUDES),
    ('VELOCIDAD', SPEED_MAGNITUDES),
    ('TIEMPO', TIME_MAGNITUDES),
)

MAGNITUDES = YIELD_MAGNITUDES + SPEED_MAGNITUDES + FLOW_MAGNITUDES + WEIGHT_MAGNITUDES + \
             VOLUME_MAGNITUDES + DISTANCE_MAGNITUDES + TIME_MAGNITUDES

