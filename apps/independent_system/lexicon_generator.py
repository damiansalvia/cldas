# -*- coding: utf-8 -*-

import sys
sys.path.append('../utilities') # To import 'utilities' modules

import time
import nltk
import codecs
import json
import glob
from collections import defaultdict
from printHelper import *

inputdir    = 'outputs/corpus/'
outputdir   = 'outputs/lexicons/single_corpus_lexicon/'
negatorsdir = 'negators_list.txt'
logdir      = '../log/'

log = Log(logdir)

MAX_RANK = 100

WINDOW_LEFT  = 2
WINDOW_RIGHT = 1

class IndependentLexiconGenerator:

    def __init__(self, input_dir=inputdir, negators_dir=negatorsdir, window_left=WINDOW_LEFT, window_right=WINDOW_RIGHT, max_rank=MAX_RANK):
        input_dir = input_dir if input_dir[-1] != "/" else input_dir[:-1]
        self.files        = glob.glob(input_dir + '/corpus*.json')
        self.polarities   = {}
        self.window_right = window_right
        self.window_size  = window_left + window_right
        self.max_rank     = max_rank
        with codecs.open(negators_dir, "r", "utf-8") as f:
            self.negators =  [x.strip() for x in f.readlines()]  
    
    def generate(self):

        def get_tokens(review):
            # obtain a list of words from a text
            return nltk.word_tokenize(review)

        def get_polarity(val):
            if val < 40:
                return '-'
            elif val > 60:
                return '+'
            else:
                return '0'

        def get_list_polarity(list):
            val = sum(list)/len(list)
            return get_polarity(val)

        def get_negation_indexes(word_list):
            # returns the indexes of the negators words in a secuence
            return [ idx for idx, word in enumerate(word_list) if word in self.negators ]
            
        def is_negated(idx, negations_indexes):
            # chek if a word is affected by any existent negators
            return any( i >= 0 and i <= self.window_size for i in [ idx - neg + self.window_right for neg in negations_indexes])

        def inverse(rank):
            # invert the rank
            return self.max_rank - rank

        # #------- Execute Function -------#
        for file in self.files:
            file_name = file.split('/')[-1]
            file_statistics = defaultdict(int)
            occurrences = defaultdict(list)
            with codecs.open(file, "r", "utf-8") as f:
                reviews = json.load(f)
            corpus_length = len(reviews)
            for idx, rev in enumerate(reviews):
                progressive_bar( 'Processing ' + file_name.replace('.json', '').replace('_', ' ') + " : ", corpus_length, idx)
                try:
                    review  = rev['review']
                    rank    = rev['rank']
                    tokens  = get_tokens(review)
                    file_statistics['rev_' + get_polarity(rank)] += 1
                    negations_indexes = get_negation_indexes(tokens)
                    file_statistics['negators'] += len(negations_indexes)

                    for tx_idx,token in enumerate(tokens):
                        if not tx_idx in negations_indexes:
                            token = token.lower()
                            # The negators shouldn't have polarities by themselves (this should be discussed)
                            if is_negated(tx_idx,negations_indexes):
                                occurrences[token].append(inverse(rank)) 
                                file_statistics['neg_word'] += 1
                            else: 
                                occurrences[token].append(rank) 
                except Exception as e:
                    log(str(e))
                    raise e

            self.polarities[file_name] = {}         
            file_polarities = { 
                word: {
                    'polarity'             : get_list_polarity(rank),
                    'positives_ocurrences' : len(filter(lambda val: get_polarity(val) == "+", rank)),
                    'negatives_ocurrences' : len(filter(lambda val: get_polarity(val) == "-", rank)),
                    'neutral_ocurrences'   : len(filter(lambda val: get_polarity(val) == "0", rank)),
                    'total_ocurrences'     : len(rank)
                } for word, rank in occurrences.iteritems() 
            }
            self.polarities[file_name]['words'] = file_polarities
            self.polarities[file_name]['analytics'] = {
                "positive_reviews"     : file_statistics['rev_+'],
                "negative_reviews"     : file_statistics['rev_-'],
                "neutral_reviews"      : file_statistics['rev_0'],
                "total_reviews"        : file_statistics['rev_+'] + file_statistics['rev_-'] + file_statistics['rev_0'],
                "positive_words"       : len(filter(lambda word: file_polarities[word]['polarity'] == "+", file_polarities.keys())),
                "negative_words"       : len(filter(lambda word: file_polarities[word]['polarity'] == "-", file_polarities.keys())),
                "neutral_words"        : len(filter(lambda word: file_polarities[word]['polarity'] == "0", file_polarities.keys())),
                "total_words"          : len(file_polarities),
                "negators"             : file_statistics['negators'],
                "negated_words"        : file_statistics['neg_word']
            }


            progressive_bar( 'Processing ' + file_name.replace('.json', '').replace('_', ' ') + " : ", corpus_length, idx + 1)
            print

    def get_polarities(self):
        return self.polarities

    def save(self, output_dir = outputdir):
        for (file_name, pol) in self.polarities.iteritems():
            cdir = output_dir + file_name.replace('corpus', 'polarities')
            with codecs.open(cdir, "w", "utf-8") as f:
                json.dump(pol, f,indent=4,sort_keys=True,ensure_ascii=False)
            print "Result was saved in %s\n" % cdir


if __name__ == "__main__":

    start_time = time.time()

    generator = IndependentLexiconGenerator()
    generator.generate()
    generator.save()

    print '\nElapsed time: %.2f Sec' % (time.time() - start_time)
