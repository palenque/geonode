from pint import UnitRegistry

units = UnitRegistry()
units.define('ha = hm**2')


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
