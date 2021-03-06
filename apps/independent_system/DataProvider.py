 # -*- coding: utf-8 -*-

import sys
from pprint import _id
sys.path.append('../utilities')
from utilities import *

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import numpy as np
from itertools import combinations
import random
from difflib import get_close_matches



log = Log("./log")



print "Connecting Mongo database"
try:
    client = MongoClient(serverSelectionTimeoutMS=2000)
    client.server_info()
    db = client.ProyGrado
except ServerSelectionTimeoutError:
    raise Exception("Couldn't connect Mongo database")



print "Creating Mongo indexes"
db.reviews.create_index('idx', name='position_index')
db.reviews.create_index('source', name='source_index')
db.reviews.create_index('category', name='category_index')
db.reviews.create_index('tagged', name='negation_index')

        
        
def save_opinions(opinions):
    if opinions: db.reviews.insert_many(opinions)


def save_negations(opinions,tagged_as):
    if tagged_as not in ['manually','automatically']:
        raise Exception("Values for 'tagged_as' must be 'manually' or 'automatically'")
    for _id in opinions:
        negation = { 'tagged' : tagged_as }
        for idx, tag in enumerate(opinions[_id]):
            negation['text.' + str(idx) + '.negated'] = tag
            
        opinion = get_opinion(_id)
        
        # Exists and not tagged, then update
        if opinion and 'tagged' not in opinion.keys():
            db.reviews.update( { '_id': _id } , { '$set': negation }  )
        
        # Exists and tagged, then colision to be resolved
        elif opinion:
            currtags = [ item['negated'] for item in opinion['text'] ] 
            if opinions[_id] == currtags: # skip if all tags equal
                continue
            negation = do_correction(opinion,negation)
            db.reviews.update( { '_id': _id } , { '$set': negation }  )
        
        # Not exists
        else: 
            log("Opinion %s skipped (not found)" %  _id , level='error')


def get_sources():
    return list(db.reviews.distinct("source"))


def get_opinion(id):
    return db.reviews.find_one({'_id':id})


def get_opinions(source=None):
    query = {'source': source} if source else {}
    return db.reviews.find(query)


def get_by_idx(source, idx):
    return db.reviews.find_one({'source': source, 'idx': idx})


def get_sample(quantity, source, indexes = None):
    if indexes:
        return list(db.reviews.find({
            'source': source,
            'idx' :{ '$in': indexes} 
        }))
    return list(db.reviews.aggregate([ 
        { '$match' : { "source" : source,"tagged" : { "$exists" : False } } },
        { '$sample': { 'size': quantity } } 
    ]))


def get_tagged(tagger,source=None):
    query = { "tagged" : tagger  }
    if source:
        query.update({ "source" : source })
    result = db.reviews.find(query)
    return result


def get_untagged(limit=None,seed=None):
    result = db.reviews.find({ "tagged" : { "$exists" : False } }) 
    if limit:
        random.seed(seed)  
        rand = int( random.random() * db.reviews.find({}).count() ) 
        result = result.skip(rand).limit(limit)
    return result


def get_size_embedding():
    return len(db.embeddings.find_one({},{ '_id':0 })['embedding'])
    

def update_embeddings(
        femb='../../embeddings/emb39-word2vec.npy',
        ftok='../../embeddings/emb39-word2vec.txt',
        split_tolerance=1,
        verbose=False
    ):
      
    stats = { "ByWord":0,"ByRepl":0,"ByClos":0,"IsNull":0,"Fails":0,"Total":0 }
    
    # Load vectors and its words
    content     = open(ftok).read().lower().replace("_","")
    content     = unicode(content,'utf8')    
    index_for   = { token:index for index, token in enumerate(content.splitlines()) }
    embeddings  = np.load(femb)
    
    # Get simension and create the null vector
    dimension  = len(embeddings[0])
    nullvector = np.zeros(dimension)
    
    # Get vocabulary
    vocabulary = db.reviews.distinct("text.word")  
    
    # Get difference of vector-words and vocabulary-words for improving get_close_matches performance 
    # PROBLEM: 'pizería' could be excluded and 'pizerías' (in the vocabulary) won't have a closest match
    dif_keys = set(index_for.keys()) - set(vocabulary)
    for key in list(dif_keys): index_for.pop(key,None)
    
    replaces = {u'a':u'á',u'e':u'é',u'i':u'í',u'o':u'ó',u'u':u'ú'}
    
    def get_vectors( # Get the associated vector of a word and its match (null if it is the same or null vector)
            word
        ):
        
        stats['Total'] += 1
        
        if index_for.has_key(word):
            stats['ByWord'] += 1
            return None , embeddings[ index_for[ word ] ]
        
        vowels = {idx:char for idx,char in enumerate(word) if char in 'aeiou'}
        for idx in vowels:
            replaced = word[:idx]+replaces[vowels[idx]]+word[idx+1:]
            if index_for.has_key(replaced):
                stats['ByRepl'] += 1
                return replaced , embeddings[ index_for[ replaced ] ]

        size = len(word)
        if size > 1 and size < 20 and ('_' not in word): # Prevents unnecessary calculation
            possibilities = filter( lambda x: size-2 < len(x) < size+2 , index_for.keys() )
            match = get_close_matches( word , possibilities , 1 , 0.75 )
            if match:
                stats['ByClos'] += 1
                return match[0] , embeddings[ index_for[ match[0] ] ]
        
#         if size > 1 and size < 20 and not any( map( lambda chr : chr.isdigit() , word ) ):
#             import pdb; pdb.set_trace()
        
        stats['IsNull'] += 1
        return None , nullvector 
    
    
    # For each word in vocabulary find its embedding    
    result = []
    total = len(vocabulary)
    
    for idx,word in enumerate(vocabulary):
        progress("Updating embeddings (%i,%i,%i,%i)" % ( stats['ByWord'],stats['ByRepl'],stats['ByClos'],stats['IsNull'] ),total,idx)
        if not db.embeddings.find_one({'_id':word}):
            nearest , vector = get_vectors( word )
            result.append({ 
                '_id'      :word,
                'embedding':vector.tolist(),
                'nearestOf':nearest 
            })
        if idx % 500 == 0 and result:
            db.embeddings.insert_many(result)
            result = []
    
    # Save statistics results
    log("Embeddings integration result. %s" % str(stats),level='info')
    if verbose:
        if stats['Total']:
            for case in stats: print "%-17s : %i (%4.2f%%)" % (case,stats[case],100.0*stats[case]/stats['Total']) 
            #raw_input("Press enter to continue...")
        else:
            print "No embeddings has been processed"    
    
    # Save results in database
    if result: db.embeddings.insert_many(result)


def get_word_embedding(word):
    item = db.embeddings.find_one({ "_id" : word })
    if not item:
        print "Not found",word
        vocabulary = db.embeddings.distinct("_id")
        match = get_close_matches( word , vocabulary , 1 , 0.75 )
        if match: item = db.embeddings.find_one({ "_id" : match[0] })
        else    : item = db.embeddings.find_one({ "_id" : "" })
    return item['embedding']


def get_text_embeddings(text, wleft, wright, neg_as=None):    
    size_embedding = get_size_embedding()
    
    def get_entry(text, idx):
        if  0 <= idx < len(text) :
            return get_word_embedding( text[idx]['word'] )
        else :
            return list(np.zeros( size_embedding ))
    
    data,pred = [],[]
    
    total = len(text)
    for idx, word in enumerate(text):
#         progress("Getting embedding",total,idx,end=False)
        
        embeddings = []        
        for i in range(wleft + wright + 1):
            embeddings += get_entry( text , idx-wleft+i )
        
        embeddings = np.array( embeddings ).flatten()
        data.append( embeddings )
        
        if text[idx].has_key('negated'): # for training
            prediction = text[idx]['negated']
            if prediction == True:
                prediction = 1
            elif prediction == False:
                prediction = 0
            elif neg_as == True:
                prediction = 1
            elif neg_as == False:
                prediction = 0
            else: # prediction=None and neg_as=None
                prediction = 2
            pred.append( prediction )
            
    return data, pred


def get_soruce_vocabulary(source):
    return list(db.reviews.aggregate([
        { '$match': {'source': source}},
        { '$unwind': "$text" },
        { '$group': { '_id':'$text.lemma' } }
     ]))

# ----------------------------------------------------------------------------------------------------------------------


def get_stat_balanced(source=None):
    query = {}
    if source:
         query.update({ 'source':source })
    items = db.reviews.find(query)
    balance = int( round( sum( item['category'] for item in items ) / items.count() ) )
    return balance

def do_correction(opinion,negation):
    negs = {x:negation[x] for x in negation}
    diff = []
    print "\n%s vs. %s" % ( opinion['tagged'].upper() , negs['tagged'].upper() )
    for idx,item in enumerate(opinion['text']):
        print "%s%s" % (
                item['word'],
                "\033[91m/(%s:%s)[%i]\033[0m"%(
                    'i' if item['negated'] else 'n' , 
                    'i' if negs['text.' + str(idx) + '.negated'] else 'n',
                    idx
                ) if item['negated'] != negs['text.' + str(idx) + '.negated'] \
                else "\033[1m/%s\033[0m" % ('i' if item['negated'] else 'n'),
            ),
        if item['negated'] != negs['text.' + str(idx) + '.negated']: diff.append(idx)
    print
    diff = list(reversed(diff))
    queue = []
    while diff:
        idx = diff.pop()
        op = raw_input("Q(uit), B(ack), L(eft) or R(ight) for [%i] > " % idx)
        op = op.lower()
        if op == 'q':
            negs = negation
            break  
        elif op == 'l':
            queue.append(idx)
            negs['text.' + str(idx) + '.negated'] = opinion['text'][idx]['negated']
        elif op == 'r':
            queue.append(idx)
            negs['text.' + str(idx) + '.negated'] = negs['text.' + str(idx) + '.negated']
        elif op == 'b':
            diff.append(idx)
            if queue: diff.append(queue.pop())
        else:
            diff.append(idx)
    return negs

if __name__ == '__main__':
    pass


