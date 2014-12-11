from modeltranslation.translator import translator, TranslationOptions
from geonode.tabular.models import Tabular


class TabularTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'abstract',
        'purpose',
        'constraints_other',
        'supplemental_information',
        'distribution_description',
        'data_quality_statement',
    )

translator.register(Tabular, TabularTranslationOptions)
