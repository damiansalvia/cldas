x
'''
Example of a complete execution
@author: Nicolás Mechulam, Damián Salvia
'''

import sys
sys.path.append('../src')

import time, os

from cldas.utils import USEFUL_TAGS
from cldas.utils.misc import Iterable
from cldas.utils.file import save, load, save_result
from cldas.utils.visual import progress
from cldas.evaluator import evaluate

from cldas.utils.logger import Log, Level
log = Log('./log')

import cldas.db.crud as dp

def end_time(start_time,case=''):
    elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))
    print "\n","Elapsed:",elapsed,"\n"
    log( "[%s] Elapsed: %s" % (case,elapsed) , level=Level.DEBUG)



'''
---------------------------------------------
      Retrieval stage
---------------------------------------------
'''
start_time = time.time()
  
from cldas.retrieval import CorpusReader
  
corporea = []
 
if not dp.get_opinions(source='AARD'): 
    reader = CorpusReader( '../corpus/AARD', '*/*.json', 
        op_pattern   = '\"(.*?)\"[,(?:\\r\\n)]', 
        path_pattern = '(neg|pos)/', 
        decoding     = 'unicode-escape' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = {'neg':33, 'pos':66 }
    corporea.append( ( reader, mapping ) )    
  
if not dp.get_opinions(source='MC'):
    reader = CorpusReader( '../corpus/MC', '*.xml', 
        op_pattern   = '<body>(.*?)</body>', 
        file_pattern = 'rank=\"([1-5])\"', 
        decoding     = 'cp1252' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { '1':17, '2':34, '3':50, '4':67, '5':84 }
    corporea.append( ( reader, mapping ) )
     
if not dp.get_opinions(source='EB'):  
    reader = CorpusReader( '../corpus/EB', '*.xml', 
        op_pattern   = '/<phrase.*?polarity=\".*?\".*?>(.*?)<\/phrase>/g', 
        file_pattern = '/<phrase.*?polarity=\"(.*?)\".*?>.*?<\/phrase>/g', 
        decoding     = 'cp1252'
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { 'negative':25, '': 50, 'positive':75 }
    corporea.append( ( reader, mapping ) )
 
if not dp.get_opinions(source='COAH'): 
    reader = CorpusReader( '../corpus/COAH', '*.xml', 
        op_pattern   = '<coah:review>(.*?)</coah:review>', 
        file_pattern = '<coah:rank>([1-5])<\/coah:rank>' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { '1':17, '2':34, '3':50, '4':67, '5':86 }
    corporea.append( ( reader, mapping ) )
 
if not dp.get_opinions(source='COAR'): 
    reader = CorpusReader( '../corpus/COAR', '*.csv', 
        op_pattern   = '\d+;[1-5]\s.*?;.*?;.*?;(.*?);', 
        file_pattern = '\d+;([1-5])\s.*?;.*?;.*?;.*?;' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { '1':17, '2':34, '3':50, '4':67, '5':86 }
    corporea.append( ( reader, mapping ) )
    
if not dp.get_opinions(source='COPOS'): 
    reader = CorpusReader( '../corpus/COPOS', '*.csv', 
        op_pattern   = '.*?;(.*?;.*?);\d{2}\s.*?\d{4};[0-5];', 
        file_pattern = '.*?;.*?;.*?;\d{2}\s.*?\d{4};([0-5]);',
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { '0':50, '1':17, '2':34, '3':50, '4':67, '5':86 }
    corporea.append( ( reader, mapping ) )
    
if not dp.get_opinions(source='DOS'): 
    reader = CorpusReader( '../corpus/DOS', '*.xml', 
        op_pattern   = '/<text>(.*?)<\/text>\s*<Opinions>\s*<Opinion .* polarity="(?:positive|negative|neutral)".*?\/>\s*<\/Opinions>/g', 
        file_pattern = '/<text>.*?<\/text>\s*<Opinions>\s*<Opinion .* polarity="(positive|negative|neutral)".*?\/>\s*<\/Opinions>/g',
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = {'negative':33, 'positive':66 }
    corporea.append( ( reader, mapping ) )
  
if not dp.get_opinions(source='UTPren'):
    reader = CorpusReader( '../corpus/UTPren', 'test.csv', 
        op_pattern   = '(.*?),(?:Pos|Neg|Neu),.*?,.*?,.*?(?:\n|$)', 
        file_pattern = '.*?,(Pos|Neg|Neu),.*?,.*?,.*?(?:\n|$)' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { 'Neg':25, 'Neu':50, 'Pos':75 }
    corporea.append( ( reader, mapping ) )
     
    reader = CorpusReader( '../corpus/UTPren', 'train.csv', 
        op_pattern   = '(.*?),(?:TRUE|FALSE),(?:Pos|Neg|Neu)(?:\n|$)', 
        file_pattern = '.*?,(?:TRUE|FALSE),(Pos|Neg|Neu)(?:\n|$)' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { 'Neg':25, 'Neu':50, 'Pos':75 }
    corporea.append( ( reader, mapping ) )
     
if not dp.get_opinions(source='RRD'): 
    reader = CorpusReader( '../corpus/RRD', '*/*.json', 
        op_pattern   = '\"(.*?)\"[,\\n]', 
        path_pattern = '(neg|pos)/', 
        decoding     = 'unicode-escape' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = {'neg':33, 'pos':66 }
    corporea.append( ( reader, mapping ) )
 
if not dp.get_opinions(source='ST'):  
    reader  = CorpusReader( '../corpus/ST', '*.tsv', 
        op_pattern   = '\d\t\d\t(.*?)\t.*?\n', 
        file_pattern = '(\d\t\d)\t.*?\n' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = {  # diff:val :: -4:10,-3:20,-2:30,-1:40,0:50,1:60,2:70,3:80,4:90
        '1\t1':50, '1\t2':40, '1\t3':30, '1\t4':20, '1\t5':10,
        '2\t1':60, '2\t2':50, '2\t3':40, '2\t4':30, '2\t5':20,   
        '3\t1':70, '3\t2':60, '3\t3':50, '3\t4':40, '3\t5':30,       
        '4\t1':80, '4\t2':70, '4\t3':60, '4\t4':50, '4\t5':40,    
        '5\t1':90, '5\t2':80, '5\t3':70, '5\t4':60, '5\t5':50,  
    }
    corporea.append( ( reader, mapping ) )
 
if not dp.get_opinions(source='UTRep'):
    reader = CorpusReader( '../corpus/UTRep', '*.csv', 
        op_pattern   = '"(.*?)",(?:NEU|NONE|N|P)(?:\n|$)', 
        file_pattern = ',(NEU|NONE|N|P)(?:\n|$)'
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { 'N':25, 'NEU':50, 'NONE':50, 'P':75 }
    corporea.append( ( reader, mapping ) )
  
end_time(start_time,case='RETRIEVE')
  
  
  
'''
---------------------------------------------
      Preprocessing stage
---------------------------------------------
'''
start_time = time.time()
  
from cldas.prelim import Preprocess
  
for ( reader,mapping ) in corporea:
    source  = reader.source
    data    = reader.data( mapping=mapping )
    preproc = Preprocess( source, data )
    print "Classes:", preproc.categories()
    print "Succeed:", len( preproc.sents() ) 
      
    dp.save_opinions( preproc.data() )
  
end_time(start_time,case='PREROCESS')
 
 
 
'''
---------------------------------------------
      Adding Negation Scope tagging
---------------------------------------------
'''
start_time = time.time()
 
dp.save_negations_from_files('./neg/manual/*')    
 
if not dp.get_opinions(source='SFU-NEG'):    
    reader = CorpusReader( '../corpus/SFU-NEG', '*/*.xml', 
        scope_pattern='<scope>(.*?)<\/scope>', 
        negexp_pattern='<negexp(?: discid="1n")?>(.*?)<\/negexp>', 
        op_pattern='<review.*?>(.*?)<\/review>', 
        wd_pattern='<\w .*?wd=\"(.*?)\".*?\/>', 
        file_pattern='<review.*?polarity=\"(.*?)\">' 
    )
    print "Classes:", reader.categories()
    print "Opinions:", len( reader.opinions() )
    mapping = { 'negative':33, 'positive':66 }
    
    source  = reader.source
    data    = reader.data( mapping=mapping )
    preproc = Preprocess( source, data )
    print "Classes:", preproc.categories()
    print "Succeed:", len( preproc.sents() )
      
    dp.save_opinions( preproc.data( tagged=dp.TaggedType.MANUAL ) )
     
end_time(start_time)
 
 
 
'''
---------------------------------------------
      Adding embeddings to database
---------------------------------------------
'''
start_time = time.time()

dp.update_embeddings('../embeddings/emb39-word2vec.npy', '../embeddings/emb39-word2vec.txt')
 
end_time(start_time,case='EMBEDDINGS')
 


'''
---------------------------------------------
      Negation Scope stage
---------------------------------------------
''' 
from cldas.neg.model import NegScopeLSTM, NegScopeFFN
 
tagged   = dp.get_tagged(tag_as=dp.TaggedType.MANUAL)
untagged = dp.get_untagged()
vec_size = len( dp.get_null_embedding() )
 
path = './neg/models/'

 
######### Feed-Forward Neural Network ######### 
# start_time = time.time()

# wleft, wright = 2, 2
# ffn = NegScopeFFN( wleft, wright, vec_size )
 
# fname = "NegScopeFFN_l%i_r%i" % (wleft,wright)
# if os.path.exists(path+fname):
#     lstm.load_model(path+fname)
# else:
#     X,Y = dp.get_ffn_dataset( tagged, wleft, wright )
#     ffn.fit( X,Y )     
#     ffn.save_model(fname, './neg/models')
     
# negations = {} ; total = len( untagged )
# for opinion in untagged:
#     progress("Predicting on new data",total,idx)
#     X, _ = dp.get_ffn_dataset( [opinion], wleft , wright, test_frac=0.0 )
#     Y = ffn.predict( X )
#     Y = Y[0].tolist()
#     negations[ opinion['_id'] ] = Y  
#     if idx % 500 == 0: # Optimization
#         dp.save_negations(negations, dp.TaggedType.AUTOMATIC)
#         negations = {}
# if negations: 
#     dp.save_negations(negations, dp.TaggedType.AUTOMATIC)    

# end_time(start_time,case='FFN')
 
 
####### LSTM Recurrent Neural Network ########
start_time = time.time()

win = 10
lstm = NegScopeLSTM( win, vec_size )
 
fname = "NegScopeLSTM_w%i.h5" % win 
if os.path.exists(path+fname):
    lstm.load_model(path+fname)
else:
    X,Y = dp.get_lstm_dataset( tagged, win )
    lstm.fit( X,Y )
    lstm.save_model(fname, './neg/models')
     
negations = {} ; total = len( untagged )
for idx,opinion in enumerate(untagged):
    progress("Predicting on new data",total,idx)
    X ,_ = dp.get_lstm_dataset( [opinion], win , verbose=False, test_frac=0.0 )
    Y = lstm.predict( X )
    Y = Y.flatten().tolist()[: len( opinion['text'] ) ] # Only necessary with LSTM
    negations[ opinion['_id'] ] = Y 
    if idx % 500 == 0: # Optimization
        dp.save_negations(negations, dp.TaggedType.AUTOMATIC)
        negations = {}   
if negations:
    dp.save_negations(negations, dp.TaggedType.AUTOMATIC)    
 
end_time(start_time,case='LSTM')
 
 
 
'''
---------------------------------------------
      Statistics over dataset
---------------------------------------------
'''
# from cldas.db.stats import *
 
def table_print(fs):
    print '%-38s | %s' % ("Metric","Value")
    print '%-38s-+-%s' % ("-"*38,"-"*20)
    for f in fs:
        fname = f.__name__.replace('_',' ')
        fname = fname[0].upper()+fname[1:]
        res = f()
        if type(res) == list:
            print '%-38s | %s' % ( fname, "")
            for r in res:
                val = r.pop('count')
                key = r.keys()[0]
                key = "   %s: %s" % ( key, r[key] )
                print '%-38s | %s' % ( key, val if type(val) == int else round(val,3) )
        else:
            print '%-38s | %s' % ( fname, res if type(res) == int else round(res,3) ) if res is not None else "None"
    print 
                 
stats = []
stats.append( size_vocabulary             )
stats.append( size_vocabulary_by_word     )
stats.append( size_vocabulary_by_lemma    )

stats.append( size_corporea               )
stats.append( size_corporea_by_source     )

stats.append( avg_tokens_by_source        )

stats.append( size_reviews_category       )

stats.append( size_embeddings             ) 
stats.append( size_embeddings_unused      )
stats.append( size_embeddings_used        ) 
stats.append( size_embeddings_exact_match )
stats.append( size_embeddings_near_match  )
stats.append( size_embeddings_null_match  )

stats.append( size_manually_tagged        )
stats.append( size_manually_tagged_by_cat )

stats.append( size_nagated_words          )
stats.append( size_negators               )

stats.append( size_positive_reviews       )
stats.append( size_neutral_reviews        )
stats.append( size_negative_reviews       ) 

stats.append( size_positive_words         )
stats.append( size_neutral_words          )
stats.append( size_negative_words         )

stats.append( get_balance                 )
stats.append( get_balance_by_source       )
  
  
table_print(stats)

 
'''
---------------------------------------------
                Split Corpus
---------------------------------------------
'''
independe_ids , dependent_ids = dp.split_sample(fraction=0.2, seed=121)
evaluation_ids, dependent_ids = dp.split_sample(ids=dependent_ids, fraction=0.1, seed=121)



'''
---------------------------------------------
          Independent Lexicon stage
---------------------------------------------
'''
start_time = time.time()

from cldas.indeplex import by_senti_tfidf

pos = dp.get_opinions(ids=independe_ids, cat_cond={"$gt":50} )
neg = dp.get_opinions(ids=independe_ids, cat_cond={"$lt":50} )
lemmas = dp.get_lemmas()

indep_lexicons = []

for limit in [50,100,150]:
    li = by_senti_tfidf( pos, neg, lemmas, filter_tags=USEFUL_TAGS, limit=limit, tofile='./indeplex' )
    indep_lexicons.append( (li,"tfidf") )
    
end_time(start_time,case='LI')



'''
---------------------------------------------
      Dependent Lexicon stage
---------------------------------------------
'''

from cldas.deplex import by_influence, by_distance
from cldas.utils.graph import ContextGraph

dep_lexicons = []
for corpus in dp.get_sources():
    
    opinions = dp.get_opinions(ids=dependent_ids, source=corpus )
    
    start_time = time.time()
    graph = ContextGraph( opinions, corpus, filter_tags=USEFUL_TAGS )
    end_time(start_time)    
    
    for (li,name) in indep_lexicons:

        #-----------------------------------------------------------------------------------------------------------
        
        start_time = time.time()
        ld = by_distance( graph, li, seed_name=name, filter_seeds=False, limit=300, confidence=3, tofile='./deplex')
        end_time(start_time,case='LD|DIS')
        
        eval_fraction = dp.get_opinions( ids=evaluation_ids, source=corpus )
        score = evaluate( ld, eval_fraction )
        dp.save_evaluation([{
            'type'        : 'deplex',
            'li'          : name,
            'source'      : corpus,
            'propagation' : 'distance',
            'score'       : score
        }])  

        save_result(graph, ld, score, "by_distance", './graphs')
        
        #-----------------------------------------------------------------------------------------------------------
        
        start_time = time.time()
        ld = by_influence( graph, li, seed_name=name, filter_seeds=False, limit=300, confidence=1, tofile='./deplex')
        end_time(start_time,case='LD|INF') 
        
        eval_fraction = dp.get_opinions( ids=evaluation_ids, source=corpus )
        score = evaluate( ld, eval_fraction )
        dp.save_evaluation([{
            'type'        : 'deplex',
            'li'          : name,
            'source'      : corpus,
            'propagation' : 'influence',
            'score'       : score
        }]) 

        save_result(graph, ld, score, "by_influence", './graphs')
