"""
Database_controller tiene las funciones que vincular
los scraper con la base de datos. Es el archivo que los comunica.

Scrapers <----> Database_controller <----> Django model <----> DB

"""
import traceback

from web.management.commands.evento import Evento
from web.models import *
from datetime import datetime
import json
import requests
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger('django')


def all_registers_query():
    """
    Función que devuelve una lista de
    todos los registros que existen en DB
    """
    return Event.objects.all()


# def check_existing_event(event, existing_events):
#     """
#     La siguiente función determina si
#     el evento existe o no
#     """
#     # Verificamos si el evento existe.
#     exist = False
#     matching_event = None
#
#     # todo: this code needs refactoring to correctly check event existence
#     # todo: improve existing events check (check against db instead of looping)
#     if len(existing_events) > 0:
#         for e in existing_events:
#             cond1 = (e.name == event.name)
#             cond2 = (e.event_link == event.event_link)
#             if cond1 and cond2:
#                 exist = True
#                 matching_event = e
#                 break
#         # Si existe vamos a comprobar si fue modificado algun campo.
#         # Si no existe se carga como "Nuevo"
#         if exist:
#             if not events_are_equal(event, matching_event) and matching_event.status != "New":
#                 update(event, "Changed", matching_event.id)
#         else:
#             save(event)
#     else:
#         save(event)


def check_existing_event(event, existing_events):
    """
    La siguiente función determina si
    el evento existe o no
    """
    # Verificamos si el evento existe.
    try:
        matching_event = Event.objects.get(nombre=event.nombre, link_al_evento=event.link_al_evento)
        if not events_are_equal(event, matching_event):
            status = "New" if matching_event.estado == "New" else "Changed"
            update(event, status, matching_event.id)
    # Si no existe se carga como "Nuevo"
    except Event.DoesNotExist as e:
        save(event)


def events_are_equal(event, matching_event):
    """
    Función para comparar todos los atributos de un evento
    """

    # Comparamos la fecha de inicio
    fecha_pag = datetime.strftime(event.fecha, "%Y-%m-%d")
    fecha_DB = datetime.strftime(matching_event.fecha, "%Y-%m-%d")
    if fecha_pag != fecha_DB:
        return False

    # Comparamos la fecha de finalización
    if (event.fecha is not None) and (matching_event.fecha is not None):
        fecha_pag = datetime.strftime(event.fecha, "%Y-%m-%d")
        fecha_DB = datetime.strftime(matching_event.fecha, "%Y-%m-%d")
        if fecha_pag != fecha_DB:
            return False

    # Comparamos el timing
    if event.timing != matching_event.timing:
        return False

    # Comparaos la ciudad
    if event.ciudad != matching_event.ciudad:
        return False

    # Comparamos el país
    if event.pais != matching_event.pais:
        return False

    # Comparamos el estado del evento
    if event.estado_del_evento != matching_event.estado_del_evento:
        return False

    # Comparamos el Type
    if event.tipo_del_evento != matching_event.tipo_del_evento:
        return False

    # Comparamos image_url
    if event.imagen_url != matching_event.imagen_url:
        return False

    # Comparamos participantes
    if event.participantes != matching_event.participantes:
        return False

    return True


def location_is_diferent(event, matching_event):
    """
    Función para verificar si la localización es diferente
    """
    is_diferent = True
    cond1 = (event.pais == matching_event.pais)
    cond2 = (event.ciudad == matching_event.ciudad)

    if cond1 and cond2:
        is_diferent = False

    return is_diferent


def location_is_equal(event, matching_event):
    """
    Función para verificar si la localización es diferente
    """
    is_equal = False
    cond1 = (event.pais == matching_event.pais)
    cond2 = (event.ciudad == matching_event.ciudad)

    if cond1 and cond2:
        is_equal = True

    return is_equal


def flow_control_image(event, event_aux):
    """
    Flujo de control para verificar si existe la imagen.
    Si no existe, toma una del directorio por defecto y
    las crea.
    """
    has_img_url, has_img_url_mini = event.check_url_image()
    
    # Imagen grande
    # NOTE: remove "and False" to use site's image if present (disabled by client request)
    if has_img_url and False:
        if event.check_image(event.imagen_url) is False:
            url_imcab_default = event.getting_standard_image(
                image_type='cabecera')
            path_imcabecera, _ = event.write_image_cabecera(url_imcab_default, event_aux, has_img_url_mini)
            print('--- SAVED IMAGE CABECERA ---')
            event_aux.save_image(path_imcabecera)
        else:
            event_aux.add_remote_image()
            event_aux.save()
    else:
        url_imcab_default = event.getting_standard_image(
            image_type='cabecera')
        path_imcabecera, _ = event.write_image_cabecera(url_imcab_default, event_aux, has_img_url_mini)
        print('--- SAVED IMAGE CABECERA ---')
        event_aux.save_image(path_imcabecera)

    # Imagen mini
    try:
        # NOTE: remove "and False" to use site's image if present (disabled by client request)
        if has_img_url_mini and False:
            if event.check_image(event.imagen_mini_url) is False:
                url_immin_default = event.getting_standard_image(
                    image_type='miniatura')
                path_immini, _ = event.write_image_miniatura(url_immin_default, event_aux.pk)
                event_aux.save_image_mini(path_immini)
            else:
                image_mini_data = event_aux.get_remote_image_mini()
                image_mini_temp = NamedTemporaryFile(delete=True)
                image_mini_temp.write(image_mini_data.read())
                image_mini_temp.flush()
                event_aux.imagen_mini.save(f"image_mini_{event_aux.pk}.jpg", File(image_mini_temp))
                event_aux.save()
        else:
            url_immin_default = event.getting_standard_image(
               image_type='miniatura')
            path_immini, _ = event.write_image_miniatura(url_immin_default, event_aux.pk)
            event_aux.save_image_mini(path_immini)
    except Exception as e:
        logger.error("--- EXCEPTION GETTING IMAGE MINI ---")
        logger.error(e)
        logger.error(traceback.print_exc())


# def save(event, estado, id_event_to_change):
def save(event):
    """
    Función para cargar los atributos scrapeados en la base de datos
    """
    try:
        code_country = event.get_country_code()
        # code_country = CountryCode.objects.filter(countrycode=event_code_country).first() if event_code_country else None
        # todo: set match type on event_aux
        code_city, match_type = event.get_city_code()
        # code_city = CityCode.objects.filter(citycode=event_code_city).first() if event_code_city else None

        event_aux = Event.objects.create(
            nombre=event.nombre,
            link_al_evento=event.link_al_evento,
            fecha=event.fecha,
            fecha_final=event.fecha_final,
            timing=event.timing,
            sede=event.sede,
            ciudad=event.ciudad,
            codigo_de_ciudad_confirmado=match_type is Evento.CityMatchType.EXACT,
            pais=event.pais,
            estado_del_evento=event.estado_del_evento,
            tipo_del_evento=event.tipo_del_evento,
            imagen_url=event.imagen_url,
            imagen_mini_url=event.imagen_mini_url,
            visitantes=event.visitantes,
            expositores=event.expositores,
            participantes=event.participantes,

            #country_code_st=event.codeCountry(),
            #city_code_st=event.codeCity(),
            # country_code=CountryCode.objects.filter(code=event.codeCountry()).first(),
            # city_code=CityCode.objects.filter(code=event.codeCity()).first(),
            codigo_de_pais=code_country,
            codigo_de_ciudad=code_city,

            estado="New",
            sitio_de_origen=event.sitio_de_origen,
            latitud=event.lat_long()[0],
            longitud=event.lat_long()[1],
            sitio_web=event.sitio_web)

        for category in event.categorias:
            event_aux.categorias.add(category)

        # Flow control to write image
        flow_control_image(event=event, event_aux=event_aux)

        # Agregar la funcion para matchear el pais y ciudad con sus codigos
    except Exception as e:
        logger.error(f'Error saving event: {event.nombre}')
        logger.error(e)
        logger.error(traceback.print_exc())


def update(event_data, status, id):
    try:
        print("--- 1 ---")
        aux_register = Event.objects.get(id=id)
        print("--- 2 ---")
        aux_register.nombre = event_data.nombre
        # aux_register.event_link = event.event_link,
        aux_register.fecha = event_data.fecha
        aux_register.fecha_final = event_data.fecha_final
        aux_register.timing = event_data.timing
        aux_register.sede = event_data.sede
        # todo: update place coordinates (lat and long)
        aux_register.latitud = event_data.lat_long()[0]
        aux_register.longitud = event_data.lat_long()[1]
        aux_register.estado_del_evento = event_data.estado_del_evento
        aux_register.tipo_del_evento = event_data.tipo_del_evento
        # todo: categories shouldn't be copied from original event... or they do???
        aux_register.categorias = event_data.categorias
        aux_register.imagen_url = event_data.imagen_url
        aux_register.imagen_mini_url = event_data.imagen_mini_url
        aux_register.visitantes = event_data.visitantes,
        aux_register.expositores = event_data.expositores,
        aux_register.participantes = event_data.participantes
        aux_register.estado = status
        aux_register.sitio_de_origen = event_data.sitio_de_origen
        aux_register.sitio_web = event_data.sitio_web

        # todo: update location data
        aux_register.ciudad = event_data.ciudad,
        aux_register.pais = event_data.pais,
        # aux_register.country_code = CountryCode.objects.filter(code=event_data.codeCountry()).first(),
        country_code = event_data.get_country_code()
        if country_code is not None:
            # aux_register.codigo_de_pais = CountryCode.objects.filter(countrycode=event_data.codeCountry()).first()
            aux_register.codigo_de_pais = country_code
        # aux_register.city_code = CityCode.objects.filter(code=event_data.codeCity()).first(),
        city_code, match_type = event_data.get_city_code()
        if city_code is not None:
            # aux_register.codigo_de_ciudad = CityCode.objects.filter(citycode=event_data.codeCity()).first()
            aux_register.codigo_de_ciudad = city_code
            aux_register.codigo_de_ciudad_confirmado = match_type is Evento.CityMatchType.EXACT
        # todo: Flow control to write image
        flow_control_image(event=event_data, event_aux=aux_register)

        aux_register.save()

    except Exception as e:
        print("--- 3 ---")
        print(e)
        logger.error(e)
        logger.error(traceback.print_exc())

def send_endpoint(queryset):
    """
    return List containing event IDs that failed being stored
    """
    eventos = queryset
    logger.info('QUERYSET LENGTH')
    logger.info(len(queryset))
    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'es-AR,es;q=0.8,en-US;q=0.5,en;q=0.3',
        'Authorization':'Basic YXBpQGFkbWluLWV2ZW50bzp5JTZ2bUAjcT94REIlSEc=',
        'Connection':'keep-alive',
        'Host':'api.hotelesenargentina.net',
        # 'Host':'sandbox.api.hotelesenargentina.net',
        'Upgrade-Insecure-Requests':'1',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0',
        'Username': 'api@admin-evento',
        'Password': 'y%6vm@#q?xDB%HG',
        'Content-type': 'application/json',
        'Accept': 'application/json'
        }

    eventsNotSavedInApi = {}
    events_data_for_api = []

    logger.info('SENDING ENVENTS TO API')
    for evento in queryset:
        try:
            #s = [EventSerializer(e).data for e in eventos]
            logger.info(evento.id)
            if not evento.codigo_de_ciudad or evento.codigo_de_ciudad is None:
                logger.info("Falta el código de ciudad.")
                eventsNotSavedInApi[evento.id] = {
                    "code": 'missing_city_code',
                    "msg": "Falta el código de ciudad.",
                    "msg_detail": "Falta el código de ciudad."
                }
                continue
            # TODO: resolver datos anidados que pueden estar incompletos (None)
            if not evento.imagen_mini or evento.imagen_mini is None or not evento.imagen or evento.imagen is None:
                logger.info("Falta alguna de las imágenes.")
                eventsNotSavedInApi[evento.id] = {
                    "code": 'missing_image',
                    "msg": "Falta alguna de las imágenes.",
                    "msg_detail": "Falta alguna de las imágenes."
                }
                continue
            imagenMiniatura = f'https://ai-bookingmeet.com{evento.imagen_mini.url}'
            imagenBanner = f'https://ai-bookingmeet.com{evento.imagen.url}'

            if not evento.fecha or evento.fecha is None:
                logger.info("Falta la fecha de inicio.")
                eventsNotSavedInApi[evento.id] = {
                    "code": 'missing_image',
                    "msg": "Falta la fecha de inicio.",
                    "msg_detail": "Falta la fecha de inicio."
                }
            if not evento.fecha_final or evento.fecha_final is None:
                logger.info("Falta la fecha de finalización.")
                eventsNotSavedInApi[evento.id] = {
                    "code": 'missing_image',
                    "msg": "Falta la fecha de finalización.",
                    "msg_detail": "Falta la fecha de finalización."
                }

            fecha_inicio = evento.fecha.date().strftime("%Y-%m-%d")
            fecha_fin = evento.fecha_final.date().strftime("%Y-%m-%d")
            if evento.id_api is None:
                data = {
                    'indice': evento.id,
                    'idDestino': evento.codigo_de_ciudad.idciudad,
                    'nombre': evento.nombre,
                    "imagenMiniatura": imagenMiniatura,
                    "imagenBanner": imagenBanner,
                    "fechaInicio": fecha_inicio,
                    "fechaFin": fecha_fin,
                    "latitud": evento.latitud,
                    "longitud": evento.longitud,
                    "cantidadVisitantes": evento.participantes,
                    "sede": evento.sede
                }
            else:
                data = {
                    'indice': evento.id,
                    "idDestino": evento.codigo_de_ciudad.idciudad,
                    'nombre': evento.nombre,
                    "imagenMiniatura": imagenMiniatura,
                    "imagenBanner": imagenBanner,
                    "fechaInicio": fecha_inicio,
                    "fechaFin": fecha_fin,
                    "idEvento": evento.id_api,
                    "latitud": evento.latitud,
                    "longitud": evento.longitud,
                    "cantidadVisitantes": evento.participantes,
                    "sede": evento.sede
                }
            events_data_for_api.append(data)
        except Exception as e:
            eventsNotSavedInApi[evento.id] = {
                "code": "internal_error",
                "msg": "No se pudo enviar el evento.",
                "msg_detail": "No se pudo enviar el evento."
            }
            logger.error(e)
            logger.error(traceback.print_exc())

    print('===========> json.dumps(events_data_for_api)')
    print(json.dumps({'eventos': events_data_for_api}))
    try:
        url = 'https://api.hotelesenargentina.net/evento/'
        # url = 'http://sandBox-api@admin-evento:S^Gz4iiZEv@R+|u@sandbox.api.hotelesenargentina.net/evento/'
        r = requests.post(url, data=json.dumps({'eventos': events_data_for_api}), headers=headers)
        events_response_list = r.json()
        # Possible response codes
        # '401': 'Error Autenticación',
        # '201': 'Evento creado',
        # '500': 'Error Guardar Evento',
        # '200': 'Evento modificado',
        # '400': 'Error Validación',
        # '0001': 'Error Validación Nombre',
        # '0002': 'Error Validación <imagen>',
        # '0003': 'Error Validación <imagen>',
        # '0004': 'Error Validación Destino',
        # '0005': 'Error Validación Fechas',
        # '0006': 'Error Valdación Fechas',
        # '0007': 'Error Validación Fechas',
        # '0008': 'Error Validación Fechas Fin',
        # '0009': 'Error Validación Latitud/Longitud',
        # '0010': 'Error Validación Latitud/Longitud',
        # '0011': 'Error Validacion Latitud/Longitud',
        # '0012': 'Error Actualizar Evento',
        # '0013': 'Error Guardar evento'
        logger.info('===> events_response_list')
        logger.info(events_response_list)
        logger.info('len(events_response_list)')
        logger.info(len(events_response_list))
        for event_response_data in events_response_list:
            logger.info('---> event_response_data_json')
            logger.info(event_response_data)
            # event_response_data = json.loads(event_response_data_json)
            try:
                # make bulk request
                # Obtengo el codigo desde el json de la respuesta del servidor
                codigoResp = event_response_data['codigoResp']
                # resp = switcher.get(codigoResp, 'Error')
                if codigoResp == '201' or codigoResp == '200':
                    Event.objects.filter(id=event_response_data['indice']).update(estado="Sent", enviado=True, id_api=event_response_data['idEvento'])
                else:
                    logger.info('Reservas en Congresos API respondió con código de error:')
                    logger.info(event_response_data['detalleResp'])
                    eventsNotSavedInApi[event_response_data['indice']] = {
                        "code": codigoResp,
                        "msg": event_response_data['tipoResp'],
                        "msg_detail": event_response_data['detalleResp']
                    }
                    # Event.objects.filter(id=evento.id).update(status=resp)
            except Exception as e:
                eventsNotSavedInApi[event_response_data['indice']] = {
                    "code": "error_reading_response",
                    "msg": "No se pudo leer la respuesta",
                    "msg_detail": "No se pudo interpretar la respuesta de la API de Reservas en Congresos."
                }
                logger.error(e)
                logger.error(traceback.print_exc())
    except Exception as e:
        eventsNotSavedInApi[0] = {
            "code": "internal_error",
            "msg": "Error inesperado",
            "msg_detail": "Hubo un error inesperado al intentar enviar los eventos"
        }
        # show error in message
        # eventsNotSavedInApi[evento.id] = "No se pudo enviar el evento."
        logger.error(e)
        logger.error(traceback.print_exc())

    return eventsNotSavedInApi
