from django.contrib import admin

from geonode.apps.models import AppMember, App, AppCategory


class AppMemberInline(admin.TabularInline):
    model = AppMember


class AppAdmin(admin.ModelAdmin):
    inlines = [
        AppMemberInline
    ]
    # exclude = ['group', ]

admin.site.register(App, AppAdmin)
admin.site.register(AppCategory)
# admin.site.register(GroupInvitation)
