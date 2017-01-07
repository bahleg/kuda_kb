# -*- coding: utf-8 -*-
import json
import urllib2
import time
import re
import datetime

import pymongo

_cat_mapping = {
    'edu': {'business-events', 'education'},
    'transport': {},
    'rollercoaster': {},
    'art-centres': {},
    'zoo': {},
    'cafe': {},
    'cinema': {},
    'theaters': {},
    'hotels': {},
    'med': {},
    'social': {'social-activity', 'speed-dating'},
    'city-places': {},
    'nature-rest': {},
    'business': {'business-events'},
    'concerts': {'circus', 'comedy-club', 'concert', 'evening', 'kvn', 'magic', 'masquerade', 'show', 'stand-up'},
    'specs': {'cinema', 'theater'},
    'active': {'ball', 'dance-trainings', 'games', 'quest', 'sport', 'yoga'},
    'sales': {'discount', 'sale', 'shopping', 'stock', 'yarmarki-razvlecheniya-yarmarki'},
    'relig': {},
    'fest': {'ball', 'festival', 'flashmob', 'global', 'holiday', 'masquerade', 'night', 'open', 'other', 'party'},
    'exp': {'exhibition', 'fashion', 'permanent-exhibitions', 'photo', 'presentation', 'tour'},
    'children': {'kids'},
    'meet': {'evening', 'meeting', 'open', 'romance'},
    'trainings': {'business-events', 'dance-trainings'}
}


def cats_to_kudago_events_cats(query):
    cats = set()
    for cat in query.cats:
        cats = cats.union(_cat_mapping[cat])
    return cats


def init(locations=['msk', 'kzn'][:]):
    res = raw_input('are you sure?')
    if res[0].lower() != 'y':
        return
    mongo = pymongo.MongoClient()
    try:
        mongo.drop_database('kudago_places')
    except:
        pass

    collection = mongo['kudago_events']['events']
    # last_time = mongo['kudago_events']['sync_date'].find_one()
    # if last_time is None:
    last_time = -1
    # else:
    #    last_time = last_time['time']
    actual_since = time.time() - 3600 * 24 * 365
    for loc in locations:
        url = 'https://kudago.com/public-api/v1.3/events/?lang=ru&order_by=-publication_date&page_size=100&fields=id,title,dates,place,description,body_text,location,categories,publication_date,' \
              'price,is_free,site_url&expand=place,location,dates&text_format=plain&location={0}&actual_since={1}'.format(
            loc, str(actual_since))
        print url
        cur_results = json.loads(urllib2.urlopen(url).read())
        print loc, 'count', cur_results['count']
        must_exit = False
        while not must_exit:
            print 'loading page'

            for res in cur_results['results']:
                if res['publication_date'] < last_time or res['publication_date'] < time.time() - 3600 * 24 * 30:
                    print 'thats all'
                    must_exit = True
                    break
                if not 'dates' in res:
                    continue
                good_date = False
                for d in res['dates']:
                    if d['end'] > time.time():
                        good_date = True
                        break

                if not good_date:
                    continue

                collection.insert_one(res)
            if cur_results['next']:
                cur_results = json.loads(urllib2.urlopen(cur_results['next']).read())
            else:
                must_exit = True
    mongo['kudago_events']['sync_date'].delete_many({})
    mongo['kudago_events']['sync_date'].insert_one({'time': time.time()})


def get_kudago_events_by_query(query):
    from ..geo import filter_by_geo
    mongo = pymongo.MongoClient()
    mongo_query = {'place.location': query.city}

    collection = mongo['kudago_events']['events']

    results = list(collection.find(mongo_query))

    filtered = []
    time_lim = time.time() + (query.time_to_travel) * 3600 * 1.5  # fuzzy
    """
    TODO:
    a lot of filtering can be done in mongo
    """
    if len(query.cats) > 0:
        cats = cats_to_kudago_events_cats(query)

    for r in results:
        if len(query.cats) > 0:
            if len(set(r['categories']) & cats) == 0:
                continue
        good_date = False
        for d in r['dates']:
            if d['end'] > time_lim and d['start'] < time_lim:
                good_date = True
                break
        if not good_date:
            continue
        if query.price == 0:
            if not r['is_free']:
                continue
            else:
                r['price'] = 0

        else:
            price_tokens = [int(i) for i in re.findall(u'([0-9]+)\sруб', r['price'])]
            if len(price_tokens) != 0 and max(price_tokens) > query.price:
                continue
            else:
                if len(price_tokens) == 0:
                    r['price'] = '?'
                else:
                    r['price'] = max(price_tokens)

        filtered.append(r)

    coords = []
    for r in filtered:
        coords.append((r['place']['coords']['lon'], r['place']['coords']['lat']))
    filtered_by_geo_indexes = filter_by_geo(coords, query)
    filter_by_geo_results = []
    for i in filtered_by_geo_indexes:
        filter_by_geo_results.append(filtered[i[0]])
        filter_by_geo_results[-1]['time_to_travel'] = i[1]

    templated = to_template(filter_by_geo_results, query)
    return templated


def to_template(results, query):
    from ..geo import go_url
    new_results = []
    for r in results:
        try:
            new_r = {}
            new_r['title'] = r['title']
            new_r['price'] = r['price']
            new_r['description'] = r['description']
            new_r['address'] = r['place'].get('title', '') + '. ' + r['place'].get('address', '')
            new_r['time'] = ''
            new_r['time_to_travel'] = r['time_to_travel']
            for cur_date in r.get('dates', []):
                start = int(cur_date['start'])
                end = int(cur_date['end'])
                s_time = datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
                en_time = datetime.datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M:%S')
                new_r['time'] += s_time + ' - ' + en_time + ';'
            new_r['full_desc'] = r['body_text']
            new_r['url'] = r['site_url']
            new_r['map_url'] = go_url(query, r['place']['coords'])
            new_results.append(new_r)
        except Exception, e:
            print repr(e)

    return new_results


if __name__ == '__main__':
    init()
