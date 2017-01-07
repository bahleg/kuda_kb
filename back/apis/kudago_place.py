import json
import urllib2

import pymongo

_cat_mapping = {
    'edu': {"academy-of-music", "course","education-centers", "observatory","painting","workshops"},
    'transport': {"airports","car-washes","metro","station" },
    'rollercoaster': {"amusement"},
    'zoo': {"animal-shelters", "cats","dogs","pet-store","prirodnyj-zapovednik","stable","zoo"},
    'cafe': {"anticafe","bakeries","banquets","bar","bar-s-zhivoj-muzykoj","restaurants","roof",
             "brewery","cafe","canteens","clubs","coffee","fastfood","gay-bar","karaoke","pub","strip-club" ,
             "vegetarian"},
    'cinema': {"cinema"},
    'theaters': {"theatre"},
    'hotels': {"hostels","hotels","inn"},
    'med': {"salons","stomatologiya"},
    'social': {"airports","library","metro","station"},
    'city-places': {"attractions","bridge","prirodnyj-zapovednik","roof","yard",
                    "photo-places","pocket-parks","temple",
                    "castle","cathedrals","church","fountain","houses","interesting-places","lakes",
                     "monastery", "monument","other","palace","park","streets", "synagogue"},
    'nature-rest': {"sanatorii", "suburb" ,
                    "bazy-otdyha","prirodnyj-zapovednik","beaches",
                    "campings", "doma-otdyha","homesteads","kottedzhi","lakes","mosque","pansionaty","park"},
    'business': { "business","coworking"},
    'concerts': {"circus", "comedy-club","concert-hall","culture"},
    'specs': {"cinema","theatre"},
    'active': {"ice-rink","shooting-ranges", "rollerdromes","rope-park","paintball","questroom",
               "amusement","bazy-otdyha","beaches", "billiards", "bowling","slope","sport","sport-centers","stable","swimming-pool",
               "water-park","wind-tunnels",
               "campings","climbing-walls","dance-studio","diving","fitness","karts" },
    'sales': {"books","clothing","farmer-shops","flea-market", "show-room" ,
              "shops","gifts","handmade","shopping-mall",
              "health-food","music-stores","perfume-stores" ,"tea","toys",
              "online-shopping","pet-store","rynok","second-hand","vintage"},
    'relig': {"cathedrals","church", "monastery","mosque", "synagogue","temple"},
    'fest': {},
    'exp': {"art-centers", "art-space","culture","exhibition","gallery","museums"},
    'children': {"kids","toys"},
    'meet': {"books","clubs","culture"},
    'trainings': { "course","workshops"}
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
    collection = mongo['kudago_places']['places']
    for loc in locations:
        url = ' https://kudago.com/public-api/v1.3/places/?lang=ru&page_size=100&fields=id,title,address,location,timetable,description,body_text,site_url,coords,is_closed,categories&text_format=plain&location=' + loc
        cur_results = json.loads(urllib2.urlopen(url).read())
        print loc, 'count', cur_results['count']
        while True:
            print 'loading page'
            for res in cur_results['results']:
                if not res['is_closed']:
                    collection.insert_one(res)
            if cur_results['next']:
                print 'next'
                data = (urllib2.urlopen(cur_results['next']).read())
                print 'read'
                cur_results = json.loads(data)
                print 'parsed'
            else:
                break


def get_kudago_places_by_query(query):
    from ..geo import filter_by_geo
    mongo = pymongo.MongoClient()
    collection = mongo['kudago_places']['places']
    results = list(collection.find({'location': query.city}))
    coords = []
    filtered = []
    if len(query.cats)>0:
        cats = cats_to_kudago_events_cats(query)
    for r in results:
        if len(query.cats)>0:
            if len(set(r['categories'])&cats)==0:
                continue
        if r['coords']['lon'] is None:
            print r
        filtered.append(r)
        coords.append((r['coords']['lon'], r['coords']['lat']))
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
        new_r = {}
        new_r['title'] = r['title']
        new_r['price'] = '-'
        new_r['description'] = r['description']
        new_r['address'] = r['address']
        new_r['time'] = '-'
        new_r['full_desc'] = r['body_text']
        new_r['url'] = r['site_url']
        new_r['time_to_travel'] = r['time_to_travel']
        new_r['coords'] = r['coords']
        new_r['map_url'] = go_url(query, r['coords'])
        #print r['title'], r['categories']
        new_results.append(new_r)
    return new_results


if __name__ == '__main__':
    init()
