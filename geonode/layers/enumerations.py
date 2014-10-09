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
    ('MASA_SECO','Masa (seco) kg'),
    ('MASA_HUMEDO','Masa (húmedo) '),
    ('VOLUMEN_SECO','Volumen (seco) m3'),
    ('VOLUMEN_HUMEDO','Volumen (húmedo)'),
    ('RENDIMIENTO_SECO','Rendimiento (seco) ton/ha'),
    ('RENDIMIENTO_HUMEDO','Rendimiento (húmedo)'),
    ('FLUJO','Flujo kg/s'),
    ('HUMEDAD','Humedad '),
    ('ALTITUD','Altitud m'),
    ('ANCHO','Ancho m'),
    ('DISTANCIA','Distancia m'),
    ('VELOCIDAD','Velocidad m/s'),
    ('TIEMPO','Tiempo s'),
)

VOLUME_MAGNITUDES = (
    ('m3','m3'),
    ('cm3','cm3'),
)

YIELD_MAGNITUDES = (
    ('ton/ha','ton/ha'),
)

FLOW_MAGNITUDES = (
    ('kg/s','kg/s'),
)

DISTANCE_MAGNITUDES = (
    ('m','Metros'),
    ('cm','Centimetros'),
)

TIME_MAGNITUDES = (
    ('s','Segundos'),
    ('min','Minutos'),
    ('h','Horas'),
)

WEIGHT_MAGNITUDES = (
    ('kg','kg'),
    ('gram','gr'),
)

MAGNITUDES = WEIGHT_MAGNITUDES + VOLUME_MAGNITUDES

