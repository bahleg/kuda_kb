import math
import json
import urllib2

from geopy.distance import great_circle

import config


def get_city(query):
    if 54.858276 <= query.lat <= 56.499906 and 35.950421 <= query.lon <= 39.059552:
        return 'msk'
    if 55.570463 <= query.lat <= 55.925221 and 48.680707 <= query.lon <= 49.526654:
        return 'kzn'

    return '?'


# https://toster.ru/q/23016
# https://leonid.shevtsov.me/post/chto-ty-dolzhen-znat-pro-geograficheskie-koordinaty/
def geo_to_xy(lat, lon):
    x = lat * 111.0
    y = lon * abs(math.cos(math.radians(lat)) * 111.0)
    return x, y


def filter_by_geo(coords, query):
    def mykey(x):
        if isinstance(x[1], str):
            return float(x[1].split('-')[1])  # high bound of expectation
        else:
            return x[1]

    # coords: lon, lat
    if query.use_car:
        radius = 100.0 * query.time_to_travel * 1.0 / 60
    else:
        radius = 7.5 * query.time_to_travel * 1.0 / 60

    radius = max(1, radius)  # 1 km as min
    """
    lon1 = query.lon - radius / abs(math.cos(math.radians(query.lat)) * 111.0)
    lon2 = query.lon + radius / abs(math.cos(math.radians(query.lat)) * 111.0)
    lat1 = query.lat - (radius / 111.0)
    lat2 = query.lat + (radius / 111.0)
    """
    # q_x, q_y, = geo_to_xy(query.lat, query.lon)

    filtered_simple = []
    for i, c in enumerate(coords):
        try:
            dist = great_circle((query.lat, query.lon), (c[1], c[0])).kilometers
            if dist <= radius:
                if query.use_car:
                    duration = dist * 60.0 / 60
                else:
                    duration = dist * 60.0 / 5

                filtered_simple.append((i, '{0}-{1}'.format(str(int(round(duration))), str(int(round(duration * 1.5))))))
        except:
            pass

    filtered_simple.sort(key=mykey)

    filtered_simple = filtered_simple[:config.max_result_check]


    # using GIS
    key = query.city + '.'
    if query.use_car:
        key += 'car'
    else:
        key += 'foot'
    if key not in config.geo_servers:
        return filtered_simple

    refiltered_by_gis = []
    for i in filtered_simple:
        try:
            url = config.geo_servers[key][1] + '{0},{1};{2},{3}'.format(str(query.lon), str(query.lat),
                                                                        str(coords[i[0]][0]), str(coords[i[0]][1]))
            geo_result = json.loads(urllib2.urlopen(url).read())
            if geo_result['routes'][0]['duration'] / 60 < query.time_to_travel:
                refiltered_by_gis.append((i[0], int(round(geo_result['routes'][0]['duration'] / 60))))
        except:
            refiltered_by_gis.append(i)

    refiltered_by_gis.sort(key=mykey)

    return refiltered_by_gis


def go_url(query, coords2):
    coords1 = (query.lon, query.lat)
    coords2 = (coords2['lon'], coords2['lat'])
    url = 'https://www.google.com/maps?f=d&saddr={0},{1}&daddr={2},{3}&dirflg=d'.format(str(coords1[1]),
                                                                                        str(coords1[0]),
                                                                                        str(coords2[1]),
                                                                                        str(coords2[0]))

    return url
