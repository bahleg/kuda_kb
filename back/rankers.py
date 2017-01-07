# -*- coding: utf-8 -*-
import re
from scipy.spatial.distance import cdist

from nltk.stem.snowball import RussianStemmer
from nltk.tokenize import wordpunct_tokenize
import numpy as np
from plyvel import DB

import config
from functools32 import lru_cache
good_sym = re.compile(u'^[А-Яа-яЁёA-Za-z]+$')

stemmer = RussianStemmer()
w2v_model = None


def load_w2v():
    global w2v_model
    print 'loading w2v'
    w2v_model = DB(config.w2v_path)
    print 'loaded'

@lru_cache(maxsize=config.w2v_cache)
def get_vector(word):
    try:
        return np.fromstring(w2v_model.get(word.encode('utf-8')), np.float16)
    except:
        return None


def rank_by_tags(results, query):
    import time 
    scores = []
    use_stem = False
    use_vecs = False
    for t in query.tags:
	if get_vector(t) is None:
		use_stem = True
	else:
		use_vecs = True
    for r in results:
        score = []
	text = wordpunct_tokenize(r['full_desc'])
	text = [t.lower() for t in text if good_sym.match(t)]
	if use_vecs:
	        vecs = [get_vector(t) for t in text]
	        vecs = [t for t in vecs if t is not None]
	if use_stem:
	        stems = [stemmer.stem(t) for t in text]
	for tag in query.tags:
            if get_vector(tag) is not None:
                if len(vecs) > 0:
                    best = sorted(cdist(vecs, [get_vector(tag)], 'cosine').flatten().tolist())[:5]

                    cur_score = 1 - np.mean(best) / 2.0
                else:
                    cur_score = 0.0
            else:
                if len(stems) > 0:
                    if stemmer.stem(tag) in stems:
                        cur_score = 1.0
                    else:
                        cur_score = 0.0
                else:
                    cur_score = 0.0
            score.append(cur_score)
        scores.append(score)



    ranks = []
    scores = np.array(scores)
    for i in range(0, len(query.tags)):
        ranks.append(np.argsort(-scores[:, i]).argsort())
    #print ranks
    ranks_sum = np.sum(ranks, axis=0)
    ranks = np.argsort(ranks_sum)
    return ranks

if __name__ == '__main__':
    load_w2v()
    texts = []
    text1 = {
        'full_desc': u'В этом доме играл музыку сам Доргомыжский. Мы с удовольсвтием вспоминаем этого прекрасного человека Доргомыжского.'}
    text2 = {'full_desc': u'Замечательное драйовое музыкальное шоу с гитарами, барабанами и басами.'}
    text3 = {'full_desc': u'В концертном зале им Доргомыжского пройдет прощальная встреча с ветеранами металла.'}
    from query_entity import Query

    q = Query()
    q.tags = [u'рок']
    print rank_by_tags([text1, text2, text3], q)
    q.tags = [u'Доргомыжский']
    print rank_by_tags([text1, text2, text3], q)
    q.tags = [u'музыкант']
    print rank_by_tags([text1, text2, text3], q)
    q.tags = [u'Доргомыжский', u'рок']
    print rank_by_tags([text1, text2, text3], q)
    q.tags = [u'металлист', u'война']
    print rank_by_tags([text1, text2, text3], q)
