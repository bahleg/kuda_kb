from plyvel import DB
from gensim.models.word2vec import Word2Vec
import numpy as np

db_name = '../w2v_vectors'
w2v_path = '/home/legin/kudablyat/data/all.norm-sz100-w10-cb0-it1-min100.w2v'
w2v = Word2Vec.load_word2vec_format(w2v_path, binary=True, unicode_errors='ignore')
db = DB(db_name, create_if_missing=True)
i = 0
for key in w2v.vocab:
    i+=1
    if i%1000==0:
        print i
    vector = w2v[key]
    db.put(key.encode('utf-8'), np.array(vector).astype(np.float16).tostring())
