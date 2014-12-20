from django.contrib import admin
from geonode.tabular.models import Tabular, Attribute, MetadataType, TabularType
from geonode.base.admin import MediaTranslationAdmin

import autocomplete_light


class MetadataTypeInline(admin.TabularInline):
    model = MetadataType

class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display_links = ('id',)
    list_display = (
        'id',
        'tabular',
        'attribute',
        'description',
        'attribute_label',
        'display_order',
        'attribute_type',)
    list_filter = ('tabular',)
    search_fields = ('attribute', 'attribute_label',)


class TabularAdmin(MediaTranslationAdmin):
    list_display = ('id', 'title', 'date', 'category')
    list_display_links = ('id',)
    list_filter = ('date', 'date_type', 'restriction_code_type', 'category')
    search_fields = ('title', 'abstract', 'purpose',)
    date_hierarchy = 'date'
    form = autocomplete_light.modelform_factory(Tabular)


class TabularTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
    )

    inlines = [MetadataTypeInline]
    form = autocomplete_light.modelform_factory(TabularType)

admin.site.register(TabularType, TabularTypeAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Tabular, TabularAdmin)
