# coding=utf-8
"""Scraper de la info de 10times"""

# Librerias externas
import json

from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, date
import html
import time
import traceback
import re

# Librerias internas
from web.management.commands.scraper_10times_links import scraper_links
from web.models import Event, EventLink, CountryCode, CityCode
from web.management.commands.evento import Evento
from web.management.commands.database_controller import all_registers_query
from web.management.commands.database_controller import check_existing_event
from web.management.commands.custom_ip_request import get as custom_ip_get

# Extraemos la cantidad de Participantes
# Estos se dividen en tres:
#     - Visitors
#     - Exhibitors
#     - Delegates
# No siempre la pagina muestra todos estos datos.


def get_participants(soup_event):
    try:
        visitors_name = soup_event.find('div', id='name_vis')
        visitors_container = visitors_name.parent
        visitors_a_tag = visitors_container.find('a')
        if visitors_a_tag:
            raw_visitors = visitors_a_tag.text.strip()
        else:
            visitors_container_text = visitors_container.find_all(text=True, recursive=False)
            # removing text from child tags
            inner_text = [element for element in visitors_container_text if isinstance(element, NavigableString)]
            filtered_inner_text_list = [row for row in inner_text if any(c.isdigit() for c in row)]
            raw_visitors = filtered_inner_text_list[0] if len(filtered_inner_text_list) > 0 else ''
        visitors_list = raw_visitors.split('-')
        visitors_str = visitors_list[1] if len(visitors_list) > 1 else visitors_list[0]
        visitors = re.sub("[^0-9]", "", "".join(visitors_str))

        # 10times has changed and, in order to track exhibitors, the scraper needs to be updated
        # leaving them empty (0), as they're not highest priority
        exhibitors = 0

        n_visitors = int(visitors) if visitors else 0

        participants = n_visitors + exhibitors
        
        return visitors, exhibitors, participants
    except Exception as e:
        print("Error al leer a los participantes")
        print(e)
        print(traceback.print_exc())
        return "0", "0", None


def get_cover_image(soup_event):
    text = soup_event.find('section', class_='page-wrapper')
    text = text.attrs.get('style')
    cover_image_url = ''
    try:
        for letter in range(len(text)):
            if text[letter] == 'h' and text[letter+1] == 't' and text[letter+2] == 't':
                while(text[letter] != ')'):
                    cover_image_url = cover_image_url + text[letter]
                    letter = letter + 1
                break
    except Exception as e:
        print(e)
        print(traceback.print_exc())
    return cover_image_url

#  Extraemos el link de la imagen y la guardamos en un strings
#  Posteriormente tenemos que ver como descargamos esa imagen y en donde la guardamos


def get_event_image(soup_event):
    try:
        link_img = soup_event.find('img', class_='img-thumbnail img-160 lazy').attrs.get('data-src')
        print('link image mini 10times ---> ' + link_img)
        return link_img
    except Exception as e:
        return 'No image'


#  Extraemos las caterorias de los eventos y las guardamos en una lista
def get_event_categories(soup_event):
    try:
        categories = soup_event.find("td", id="hvrout2").find_all('a')
        i = 0
        for category in categories:
            categories[i] = category.text
            i += 1
        return categories
    except Exception as e:
        print("Error al leer las categorias")
        print(e)
        print(traceback.print_exc())
        return None


#  Extraemos el tipo de evento. Si es conference o tradeShow
def get_event_type(soup_event):
    try:
        event_type_tag = soup_event.find('td', id="hvrout2") \
                         or soup_event.find('div', class_='mt-5 text-muted')
        cadena = event_type_tag.text if event_type_tag else ""
        tradeShow_word = cadena.find("Trade Show")
        conference_word = cadena.find("Conference")
        if tradeShow_word > 0:
            return "Trade Show"
        elif conference_word > 0:
            return "Conference"
    except Exception as e:
        print("Error al leer el tipo de evento")

        return None

# Extraemos la hora o el periodo de tiempo en el cual se realiza el evento


def get_timings(soup_event):
    try:
        timing = soup_event.find('tr', id='hvrout1').find('td').text.strip()
        t_aux = ""
        timing_checked = ""
        for t in timing:
            if (t == " " and t_aux == " ") or t == "\n":
                timing_checked = timing_checked + ""
            else:
                timing_checked = timing_checked + t
            t_aux = t

        return timing_checked
    except Exception as e:
        print("Error al leer el timing")
        print(e)
        print(traceback.print_exc())
        return None


# Lee los eventos que son presenciales, esten cancelados o no
# En caso de no tener un establecimiento, define a place como  "unkown"
# Todos tienen ciudad y pais


def get_event_place(soup_event):
    try:
        place = ""
        city = ""
        country = ""
        # div = soup_event.find_all('div', class_="lead mb-0")[1]
        div = soup_event.find_all('div', class_="mb-0")[1]

        # city = div.find_all('a')[0].text
        # country = div.find_all('a')[1].text
        specific_place = div.text
        specific_place = specific_place.split(sep=',')

        if len(specific_place) == 3:
            place = specific_place[0].strip()
            city = specific_place[1].strip()
            country = specific_place[2].strip()
        elif len(specific_place) == 2:
            place = None
            city = specific_place[0].strip()
            country = specific_place[1].strip()

        # Check if place, city and country are correct
        # When country is missing, we cannot use get_xxxx_smart method
        country_is_missing = CountryCode.objects.filter(nombre=country).count() == 0
        city_is_missing = CityCode.objects.filter(nombre=city).count() == 0
        country_has_city = CityCode.objects.filter(nombre=country).count() > 0

        if (city_is_missing and country_is_missing and country_has_city) \
                or (country_is_missing and city_is_missing and len(specific_place) == 2):
            place = city
            city = country
            country = None
        elif city_is_missing and country_has_city and len(specific_place) == 2:
            place = city
            city = country

        return place, city, country

    except Exception as e:
        print("Error a leer la ubicacion")
        print(e)
        print(traceback.print_exc())
        return None, None, None


def get_event_date(soup_event):
    try:
        if soup_event.find('div', class_="eventTime") is not None:
            event_date = soup_event.find('div', class_="eventTime").attrs.get('data-start-date')
        elif soup_event.find('strike') is not None:
            strike = soup_event.find('strike')
            event_date = strike.find('span').attrs.get("content")
        elif soup_event.find('div', class_="header_date color_orange mt-5") is not None:
            div = soup_event.find('div', class_="header_date color_orange mt-5")
            event_date = div.find('span').attrs.get('content')
        else:
            # div = soup_event.find('div', class_="lead mb-0")
            div = soup_event.find('div', class_="mb-0")
            event_date = div.find('span').attrs.get("content")

        date_list = event_date.split("-")
        year = date_list[0]
        event_month = date_list[1]
        day = date_list[2]
        event_pre_formatted_date = day+"/"+event_month+"/"+year
        date_format = datetime.strptime(event_pre_formatted_date,'%d/%m/%Y')
        return date_format
    except Exception as e:
        print("No se leyo la fecha de inicio")
        print(e)
        print(traceback.print_exc())
        return None

#---------------------///////////////////////-------------------------#


def get_event_end_date(soup_event):
    try:
        if soup_event.find('div', {'id': 'live-now'}) is not None:
            event_date = soup_event.find('div', {'id': 'live-now'}).attrs.get('data-enddate')
        elif soup_event.find('div', class_="eventTime") is not None:
            event_date = soup_event.find('div', class_="eventTime").attrs.get('data-end-date')
        elif soup_event.find('strike') is not None:
            strike = soup_event.find('strike')
            event_date = strike.findAll('span')[1].attrs.get("content")
        elif soup_event.find('div',class_="header_date color_orange mt-5") is not None:
            div = soup_event.find('div',class_="header_date color_orange mt-5")
            event_date = div.findAll('span')[1].attrs.get('content')
        else:
            div = soup_event.find('div',class_="lead mb-0")
            event_date = div.findAll('span')[1].attrs.get("content")
        
        date_list = event_date.split("-")
        year = date_list[0]
        month = date_list[1]
        day = date_list[2]
        event_pre_formatted_date = day+"/"+month+"/"+year
        date_format = datetime.strptime(event_pre_formatted_date, '%d/%m/%Y')
        return date_format
    except Exception as e:
        print("No se leyo la fecha de finalizacion")
        print(e)
        return None


def get_event_status(soup_event):
    try:
        if soup_event.find('strike') is not None:
            status = soup_event.find('small', class_="font-12 status mx-5").text.strip()
        elif soup_event.find('div', class_="header_date color_orange mt-5") is not None:
            status = "Valid"
        else:
            status = "Valid"
        return status
    except Exception as e:
        print("Error al leer el Status")
        print(e)
        return None


# El siguiente bloque extrae el nombre, la fecha, el estado del evento, y
# si es online o presencial
# Posee un if para tres tipos de estructuras diferentes de eventos
# El primer bloque es para los eventos que han sido cancelado o pospuesto,
# y que son presenciales
# El segundo es para los eventos vigentes y presenciales
# El tercero es para los eventos vigentes y online (estos no son leidos por
# problemas posteriores a este bloque)


def get_event_data(soup_event):
    # First use script tag (with type "application/ld+json") data to extract event info
    try:
        # todo: use script tag (with type "application/ld+json") data to extract event info
        scripts = soup.find_all('script', {'type': 'application/ld+json'})

    except:
        print("Could not extract info from JSON, trying old scraper")

    # If not script tag was found, try using previous scraper
    try:
        if soup_event.find('strike') is not None:
            name = soup_event.find('h1').text
            is_cancelled = True
            is_online = False
        elif soup_event.find('div', class_="header_date color_orange mt-5") is not None:
            name = soup_event.find('h1').text
            name = name.lstrip()
            is_cancelled = False
            is_online = True
        elif soup_event.find('div', class_='mt-5 text-muted'):
            name = soup_event.find('h1').text
            name = name.lstrip()
            is_online = True if \
                (soup_event.find('div', class_='mt-5 text-muted').text.find('Online')
                 or soup_event.find('div', class_='mt-5 text-muted').text.find('Virtual'))\
                else False
            is_cancelled = False
        else:
            name = soup_event.find('h1').text
            is_cancelled = False
            is_online = False
        return name, is_cancelled, is_online
    except Exception as e:
        print("Error al leer los datos")
        print(e)


def get_event_data_from_json(soup_event, link):
    scripts = soup_event.find_all('script', {'type': 'application/ld+json'})
    if not scripts or len(scripts) == 0:
        # todo: improve code to raise exception
        # raise Exception('Cannot extract event data from JSON. Could not find JSON.')
        print('Cannot extract event data from JSON. Could not find JSON.')
        return None, False

    all_scripts = soup_event.find_all('script')
    data_layer_json = None
    for script in all_scripts:
        prefix = 'dataLayer='
        if len(script.contents) > 0 and prefix in script.contents[0]:
            data_layer = script.contents[0][len(prefix):]
            data_layer_json = json.loads(data_layer)

    # event_data = json.loads(scripts[0].text)
    event_data = json.loads(scripts[0].contents[0])
    print('--- event_data ---')
    print(event_data)

    # Set empty values
    event_type = None
    name = None
    website = None
    date = None
    end_date = None
    event_status = None
    place = None
    city = None
    country_name = None
    country_code = None
    latitude = None
    longitude = None
    image_mini_url = None
    cover_image_url = None
    categories = []

    # note: unescaping HTML characters... not doing it in event to avoid mixing logic, but it would reduce code repetition

    if data_layer_json is not None and len(data_layer_json) > 0:
        event_type = html.unescape(data_layer_json[0]['Event Type'])
        city = html.unescape(data_layer_json[0]['City'])
        country_name = html.unescape(data_layer_json[0]['Country'])
        if 'Industry' in data_layer_json[0]:
            categories.append(html.unescape(data_layer_json[0]['Industry']))

    # todo: confirm properties values
    print(event_data['@type'])
    if '@type' in event_data:
        event_type = html.unescape(event_data['@type'])
    print(html.unescape(event_data['name']))
    if 'name' in event_data:
        name = html.unescape(event_data['name'])
    print(event_data['url'])
    if 'url' in event_data:
        website = html.unescape(event_data['url'])
    print(event_data['startDate'])
    if 'startDate' in event_data:
        date = datetime.strptime(html.unescape(event_data['startDate']), '%Y-%m-%d')
    # name, link, date, end_date, timing,
    #            place, city, country, event_status,
    #            event_type, categories, cover_image_url, visitors,
    #            exhibitors, participants
    print(event_data['endDate'])
    if 'endDate' in event_data:
        end_date = datetime.strptime(html.unescape(event_data['endDate']), '%Y-%m-%d')
    print(event_data['eventStatus'])
    if 'eventStatus' in event_data:
        event_status = html.unescape(event_data['eventStatus'])
    # print(event_data['eventAttendanceMode'])  # is online?
    if 'location' in event_data:
        if 'name' in event_data['location']:
            place = html.unescape(event_data['location']['name'])
        if 'address' in event_data['location']:
            if 'streetAddress' in event_data['location']['address'] and place is None:
                place = html.unescape(event_data['location']['address']['streetAddress'])
            if 'addressLocality' in event_data['location']['address']:
                city = html.unescape(event_data['location']['address']['addressLocality'])
            if country_name is None and 'addressRegion' in event_data['location']['address']:
                country_name = html.unescape(event_data['location']['address']['addressRegion'])
            if 'addressCountry' in event_data['location']['address']:
                country_code = html.unescape(event_data['location']['address']['addressCountry'])
                # ISO standard uses GB for United Kingdom, but the page uses UK in some places
                if country_code == 'UK':
                    country_code = 'GB'
            if 'geo' in event_data['location'] and '@type' in event_data['location']['geo'] and event_data['location']['geo']['@type'] == 'GeoCoordinates':
                latitude = html.unescape(event_data['location']['geo']['latitude']).replace(',', '.')
                longitude = html.unescape(event_data['location']['geo']['longitude']).replace(',', '.')

    if 'image' in event_data:
        for image in event_data['image']:
            if 'wrapper' in image:
                cover_image_url = image
            elif 'eventLogo' in image or 'eventlogo' in image:  # or '/event/' in image: NOTE: disabled /event/ beacuse it brought too many fakes
                image_mini_url = image

    timing = None
    visitors = 0
    exhibitors = 0
    participants = 0
    is_online = False
    if 'eventAttendanceMode' in event_data:
        is_online = 'OnlineEventAttendanceMode' in event_data['eventAttendanceMode']

    event = Evento(nombre=name, link_al_evento=link, fecha=date, fecha_final=end_date, timing=timing,
                   sede=place, ciudad=city, pais=country_name, estado_del_evento=event_status,
                   tipo_del_evento=event_type, categorias=categories, imagen_url=cover_image_url, visitantes=visitors,
                   expositores=exhibitors, participantes=participants, sitio_de_origen='10times',
                   sitio_web=website, image_mini_url=image_mini_url,
                   is_online=is_online, country_code=country_code, latitude=latitude, longitude=longitude)

    return event


def recorrer_eventos(links_events, limit=0):
    # La variable limita la cantidad de eventos que se recorren
    count = 0
    existing_events = all_registers_query()
    print('Eventos traidos desde el registro:')

    for link_data in links_events:
        if limit is not 0 and count >= limit:
            break

        try:
            link = link_data.link
            print("\nINGRESAMOS AL LINK DE UN EVENTO Y OBTENEMOS SUS DATOS:\n")
            print(link)
            # Obtenemos el codigo html de cada uno de los eventos
            url_event = link
            page_event = custom_ip_get(url_event)
            soup_event = BeautifulSoup(page_event.content, "html.parser")

            # todo: try extracting from JSON
            event = get_event_data_from_json(soup_event, link)
            if event.is_online:
                continue

            if event is not None:
                # NOTE: get missing data (that is not in JSON) and skip the rest of the function (return)
                # td id="visitors" data-count="241
                try:
                    event.visitantes, _, _ = get_participants(soup_event)
                    visitors = int(event.visitantes)
                    # following commented code is from old implementation.
                    # It shows a different value that the expected from the client,
                    # so will keep it commented until confirmation
                    # TODO: remove following 2 commented lines after confirmation
                    # visitors = int(soup_event.find('td', id='visitors')['data-count'])
                    # event.visitantes = str(soup_event.find('td', id='visitors')['data-count'])
                except:
                    print('Could not get visitors')
                    visitors = 0
                    event.visitantes = "0"
                try:
                    # td id="exhibitors" data-count="241
                    exhibitors = int(soup_event.find('td', id='exhibitors')['data-count'])
                    event.expositores = str(soup_event.find('td', id='exhibitors')['data-count'])
                except:
                    print('Could not get exhibitors')
                    exhibitors = 0
                    event.expositores = "0"
                try:
                    # td id="speakers" data-count="241
                    speakers = int(soup_event.find('td', id='speakers')['data-count'])
                except:
                    print('Could not get speakers')
                    speakers = 0

                event.participantes = visitors + exhibitors + speakers
                event.timing = get_timings(soup_event)

                if event.ciudad is not None and event.pais is not None and event.fecha is not None and event.nombre is not None and event.link_al_evento is not None:
                    print('---> GOT event data:')
                    print(event.ciudad)
                    print(event.pais)
                    print(event.fecha)
                    print(event.nombre)
                    print(event.link_al_evento)
                    check_existing_event(event=event, existing_events=existing_events)
                else:
                    continue

            else:
                print('Could NOT get data from JSON. Will try old scraper implementation')
                # Comenzamos a extraer los datos
                name, is_cancelled, is_online = get_event_data(soup_event)
                # skip onlne events
                if is_online:
                    continue
                date = get_event_date(soup_event)
                event_status = get_event_status(soup_event)
                place, city, country = get_event_place(soup_event)
                categories = get_event_categories(soup_event) or []
                image_url_mini = get_event_image(soup_event)
                cover_image_url = get_cover_image(soup_event)
                event_type = get_event_type(soup_event)
                visitors, exhibitors, participants = get_participants(soup_event)
                timing = get_timings(soup_event)
                end_date = get_event_end_date(soup_event)

                print("Nombre: " + name)
                print("Link: " + link)
                print("Fecha: ", date)
                print('Fecha de fin: ', end_date)
                print("Ubicacion: \n\tLugar: %s\n\tCiudad: %s\n\tPais: %s" % (place, city, country))
                print("Hora: " + timing if timing else "")
                print("Estado: " + event_status)
                print("Evento online" if is_online else "Evento presencial")
                print("Categorias: ")
                for category in categories:
                    print("\t %s" % category)
                print("Link image: \n\t" + image_url_mini)
                print("Link coverImage: \n\t" + cover_image_url)
                print("Tipo de evento: " + event_type)
                print("Participantes:")
                print("\tVisitors: %s\n\tExhibitors: %s" % (visitors, exhibitors))
                print("Total participantes: \n\t%s" % participants)

                if (city is not None, country is not None, date is not None,
                        name is not None, link is not None):
                    aux_event = Evento(name, link, date, end_date, timing,
                                       place, city, country, event_status,
                                       event_type, categories, cover_image_url, visitors,
                                       exhibitors, participants, sitio_de_origen='10times',
                                       sitio_web='', image_mini_url=image_url_mini)
                    check_existing_event(aux_event, existing_events)
                else:
                    continue
        except Exception as e:
            print(f"Esta es la excepcion general: {e}")
            print(traceback.print_exc())
            continue
        finally:
            time.sleep(5)
            EventLink.objects.filter(link=link_data.link).delete()

        count += 1
        # uncomment to limit events
        # if count == 15:
        #     print("Leyó todos los eventos")
        #     break


def start_scraper():
    if EventLink.objects.filter(site="10times").count() == 0:
        scraper_links()
        return

    links_events = EventLink.objects.filter(site="10times")
    recorrer_eventos(links_events, 10000)

    # dictionary = scraper_links()
    # for links_events_countries in dictionary.values():
    #     recorrer_eventos(links_events_countries)
