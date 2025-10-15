from django.contrib import admin
from .models import Route, RouteImage

class RouteImageInline(admin.TabularInline):
    model = RouteImage
    extra = 0
    fields = ("image", "alt_text", "order")
    max_num = 9

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "difficulty", "location_name", "created_at")
    list_filter = ("difficulty", "created_at")
    search_fields = ("title", "description", "author__username", "location_name")
    inlines = [RouteImageInline]

@admin.register(RouteImage)
class RouteImageAdmin(admin.ModelAdmin):
    list_display = ("route", "order", "alt_text")
    list_editable = ("order",)
