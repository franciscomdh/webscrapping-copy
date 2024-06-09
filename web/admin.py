# Django
import os
import traceback

from django.contrib import admin, messages
from djangoql.admin import DjangoQLSearchMixin
from rangefilter.filter import DateRangeFilter
from django.utils.html import format_html

# Models
from .models import Event, CountryCode, CityCode, Place, EventLink
from web.management.commands.evento import fill_cities, fill_country
from web.management.commands.database_controller import send_endpoint


@admin.register(Event)
class EventAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    """Evento admin.
    Clase que me permite mostrar los datos sobre el admin
    """

    class Media:
        js = ("js/admin_paginator_dropdown.js",)
    # change_list_template = os.path.abspath(os.path.dirname(__name__)) + '/templates/admin/change_list_form.html'

    def changelist_view(self, request, extra_context=None):
        # Copy the request.GET so we can modify it (no longer immutable querydict)
        request.GET = request.GET.copy()
        # Pop the custom non-model parameter off the request (Comes out as an array?)
        # Force it to int
        page_param = int(request.GET.pop('list_per_page', [100])[0])
        # Dynamically set the django admin list size based on query parameter.
        self.list_per_page = page_param
        return super(EventAdmin, self).changelist_view(request, extra_context)

    # Funcion que permite enviar los datos a través de la API
    def send(self, request, queryset):
        print("--- request ---")
        print(request)
        eventos = queryset.values()
        if len(eventos) > 2000:
            messages.error(request, "No puedes enviar más de 2000 eventos en simultáneo.")
        for evento in eventos:
            name = evento['nombre']
            date = evento['fecha']
            country = evento['pais']
            city = evento['ciudad']
            print(name, date, country, city)
        # Enviando data al endpoint
        eventsNotSavedInApi = send_endpoint(queryset)
        if eventsNotSavedInApi:
            eventsByMessage = {}
            errorQty = len(eventsNotSavedInApi.items())
            for key, value in eventsNotSavedInApi.items():
                # join events by code
                if errorQty > 10:
                    msg = value['msg']
                else:
                    msg = value['msg_detail']
                eventsByMessage[msg] = f'{eventsByMessage[msg]}, {str(key)}' if msg in eventsByMessage.keys() else f'{str(key)}'
            for key, value in eventsByMessage.items():
                # key cointains the message and value contains the event ids
                messages.error(
                    request,
                    f"'Error sending event/s {value}: {key}"
                )
        else:
            messages.success(request, "Todos los eventos se enviaron correctamente.")

    def save_model(self, request, obj, form, change):
        obj.modificado = True
        obj.enviado = False
        super(EventAdmin, self).save_model(request, obj, form, change)

    def image_tag(self, obj):
        """Funcion para mostrar imagen de cabecera sobre el admin"""
        try:
            return format_html('<img src="{}" width=200px height=100px />',
                               obj.imagen.url)
        except Exception as e:
            print(e)
            print(traceback.print_exc())

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True

    def image_tag_mini(self, obj):
        """Funcion para mostrar imagen miniatura sobre el admin"""
        try:
            return format_html('<img src="{}" width=200px height=100px />',
                               obj.imagen_mini.url)
        except Exception as e:
            print(e)
            print(traceback.print_exc())

    image_tag_mini.short_description = 'Image mini'
    image_tag_mini.allow_tags = True

    def short_date(self, obj):
        return obj.fecha.strftime("%d %b %Y")

    short_date.admin_order_field = 'fecha'
    short_date.short_description = 'Fecha'

    def get_categorias_or_empty(self, obj):
        """Funcion para mostrar las categorías por nombre"""
        return obj.categorias if str(obj.categorias) != 'web.Event.None' else '-'

    get_categorias_or_empty.short_description = 'Categorías (tags)'

    def sitio_web_as_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.sitio_web,
            obj.sitio_web,
        )

    sitio_web_as_link.short_description = 'Sitio Web'

    list_display = [
        'id',
        'id_api',
        # 'send',
        'datos_requeridos_completos',
        # 'modify',
        'estado',
        'nombre',
        'short_date',
        'pais',
        'ciudad',
        'sede',
        'latitud',
        'longitud',
        'codigo_de_pais',
        'codigo_de_ciudad',
        'codigo_de_ciudad_confirmado',
        'get_categorias_or_empty',
        'participantes',
        'sitio_de_origen',
        # 'sitio_web',
        'sitio_web_as_link',
        'image_tag',
        'image_tag_mini'
    ]
    list_editable = [
        # 'date',
        # 'country',
        'sede',
        'codigo_de_pais',
        'codigo_de_ciudad',
        'codigo_de_ciudad_confirmado',
        'latitud',
        'longitud'
    ]
    autocomplete_fields = [
        'codigo_de_pais',
        'codigo_de_ciudad'
    ]
    raw_id_fields = [
        'codigo_de_pais',
        'codigo_de_ciudad'
    ]
    list_filter = [
        'datos_requeridos_completos',
        ('fecha', DateRangeFilter)
        # 'date',
        # 'codigo_de_pais',
        # 'codigo_de_ciudad',
        # 'categories'
    ]

    send.short_description = "Send selected events"
    actions = [send]

    search_fields = ['fecha', 'ciudad', 'nombre', 'ciudad', 'pais',
                     'codigo_de_pais', 'codigo_de_ciudad', 'codigo_de_ciudad_confirmado', 'categorias']

    list_per_page = 100

    # readonly_fields = ('image_tag',)


admin.site.unregister(Event)
admin.site.register(Event, EventAdmin)


@admin.register(CountryCode)
class CountryAdmin(admin.ModelAdmin):
    """Country admin.
    Clase que me permite mostrar los datos sobre el admin
    """

    list_display = [
        # 'id',
        # 'country',
        # 'code'
        'idpais',
        'nombre',
        'countrycode'
    ]

    list_editable = [
        # 'code',
        # 'country',
        'nombre',
        'countrycode',
    ]

    # search_fields = ['country', 'code']
    search_fields = ['nombre', 'countrycode']

    list_per_page = 50


@admin.register(CityCode)
class CityAdmin(admin.ModelAdmin):
    """City admin.
    Clase que me permite mostrar los datos sobre el admin
    """
    list_display = [
        # 'id',
        # 'city',
        # 'code',
        'idciudad',
        'idregion',
        'idprovincia',
        'nombre',
        'citycode',
        'country_name'
    ]

    def country_name(self, obj):
        # id_city = obj.id
        # kaka = ((CityCode.objects.get(id=id_city)).id_pais).country
        # # country = CountryCode.objects.filter(id=obj.id_pais)
        # return kaka
        try:
            country_data = CountryCode.objects.get(idpais=obj.idpais)
            return country_data.nombre
        except CountryCode.DoesNotExist:
            return ''


    list_editable = [
        # 'city',
        # 'code'
        # 'idciudad',
        'idregion',
        'idprovincia',
        'nombre',
        'citycode',
    ]

    # search_fields = ['code', 'city']
    search_fields = ['citycode', 'nombre']

    list_per_page = 50

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    """Country admin.
    Clase que me permite mostrar los datos sobre el admin
    """

    list_display = [
        # 'id',
        'nombrepais',
        'nombreciudad',
        'venue',
        # 'lat',
        # 'long',
        'latitud',
        'longitud',
    ]

    list_editable = [
        'venue',
        # 'lat',
        # 'long',
        'latitud',
        'longitud',
    ]

    search_fields = ['nombrepais', 'nombreciudad', 'venue']

@admin.register(EventLink)
class EventLinkAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    """Country admin.
    Clase que me permite mostrar los datos sobre el admin
    """

    list_display = [
        'id',
        'site',
        'scraped',
        'link',
        'saved_date',
    ]

    search_fields = ['id']
