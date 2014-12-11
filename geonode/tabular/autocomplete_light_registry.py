import autocomplete_light
from models import Tabular

autocomplete_light.register(
    Tabular,
    search_fields=['^title'],
    autocomplete_js_attributes={
        'placeholder': 'Document name..',
    },
)
