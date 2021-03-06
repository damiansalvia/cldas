# -*- encoding: utf-8 -*-
'''
Module with a set of models for determining the scope negation 

@author: Nicolás Mechulam, Damián Salvia
'''

import os
os.environ['TF_CPP_MIN_VLOG_LEVEL'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'

import numpy as np
np.random.seed(666)

from cldas.utils import Log, Level
from cldas.utils.metrics import *
from cldas.utils.visual import title

from keras.models import Sequential,load_model
from keras.layers import Dense,LSTM
from keras.layers.core import Dropout
from keras.callbacks import EarlyStopping, Callback


_DEFAULT_LAYER_SIZE = 750
_DEFAULT_DROPOUT    = 0.0
_DEFAULT_ACTIVATION = 'relu'

log = Log("./log")



class _NegScopeModel(object):
    '''
    Base class of negation scope models.
    '''
    
    def __init__(self, dimension,
            layers    = [{'units':750, 'activation': 'relu', 'dropout': 0.2 }],
            metrics   = [binacc, precision, recall, fmeasure, mse, bce],
            loss      = 'binary_crossentropy', 
            optimizer = 'adam',
            verbose   = 2,
        ):
        self._dimension = dimension 
        self._layers    = layers
        self._metrics   = metrics
        self._loss      = loss
        self._optimizer = optimizer
        self._verbose   = verbose
        
        print title( self.__str__(), width=61 )
    
       
    def __repr__(self):
        return "< %s.%s >" % ( self.__class__.__module__, self.__str__() )
    
    
    def __str__(self):
        return "%s (%s,%s,%i,%s)" % (
            self.__class__.__name__.replace("NegScope",""), 
            ','.join( str(x) for x in self._parms.values() ),
            str(self._dimension), 
            len(self._layers), 
            self._optimizer
        )
    
    
    def save_model(self, filename, dirpath= './'):
        dirpath = dirpath if dirpath [-1] == "/" else dirpath+'/'
        if not os.path.isdir(dirpath): 
            os.makedirs(dirpath)
        filename = filename+'.h5' if not filename.endswith('.h5') else filename
        self._model.save( dirpath+filename )
        print "Model saved at",dirpath+filename
       
        
    def load_model(self, source):
        self._model = load_model(source , custom_objects={
            'binary_accuracy':binacc,
            'precision': precision,
            'recall':recall,
            'fmeasure':fmeasure,
            'mean_squared_error':mse,
            'binary_crossentropy':bce,
        })        
        self._dimension = None


    def fit(self, X, Y, testing_fraction=0.2, early_monitor='val_binary_accuracy', verbose=1):        
        callbacks = []
        if early_monitor:
            callbacks.append( EarlyStopping( monitor=early_monitor, min_delta=0, patience=2, mode='auto', verbose=0 ) )            
        history = self._model.fit( X, Y, 
            callbacks=callbacks, 
            batch_size=32 , epochs=100, 
            validation_split=testing_fraction, 
            verbose=verbose 
        )
        return history

    
    def predict(self,X):
        Y = self._model.predict( X )
        Y = np.array(Y).round() == 1 
        return Y
    
    
    def get_scores(self, X, Y, verbose=2):
        scores = self._model.evaluate(X,Y,batch_size=32,verbose=verbose)
        return zip( self._model.metrics_names , [ round(score*100,1) for score in scores ] )

    

class NegScopeFFN(_NegScopeModel):
    '''
    Class of Feed-Forward Network model
    '''
    
    def __init__(self, window_left, window_right, dimension, **kwargs):
        self._parms = { 'wleft':window_left,'wright':window_right }
        super(NegScopeFFN,self).__init__(dimension,**kwargs)
    
        # Model definition     
        self._model = Sequential()
        
        # Input layer
        layer = self._layers[0]
        config = {
            'input_dim'  : self._dimension * (window_left + window_right + 1),
            'activation' : layer.get('activation',_DEFAULT_ACTIVATION),
            'units'      : layer.get('units',_DEFAULT_LAYER_SIZE)
        }
        self._model.add( Dense( **config ) )
        self._model.add( Dropout( layer.get('dropout',_DEFAULT_DROPOUT) , seed=666 ) )
         
        # Intermediate layers
        for layer in self._layers[1:]:
            config = {
                'activation' : layer.get('activation',_DEFAULT_ACTIVATION),
                'units'      : layer.get('units',_DEFAULT_LAYER_SIZE)
            }
            self._model.add( Dense( **config ) )
            self._model.add( Dropout( layer.get('dropout',_DEFAULT_DROPOUT) , seed=666 ) )
         
        # Output layer
        self._model.add( Dense( 1, activation='sigmoid' ) )
        
        # Compile model from parameters
        self._model.compile( loss=self._loss, optimizer=self._optimizer , metrics=self._metrics )
        
        # Print model
        if self._verbose != 0: print self._model.summary()

    
    
class NegScopeLSTM(_NegScopeModel):
    '''
    Class of Long Short Term Memory model
    '''
    
    def __init__(self, window, dimension, **kwargs):
        self._parms = { 'win':window }
        super(NegScopeLSTM,self).__init__(dimension,**kwargs)
        
        # Model definition     
        self._model = Sequential()
        
        # Input layer
        layer = self._layers[0]
        config = {
            'input_shape'       : (window, self._dimension),
            'activation'        : layer.get('activation',_DEFAULT_ACTIVATION), 
            'dropout'           : layer.get('dropout', _DEFAULT_DROPOUT) ,  
            'use_bias'          : layer.get('bias',True),
            'recurrent_dropout' : layer.get('recurrent_dropout', 0.0),
            'return_sequences'  : len(self._layers[-1]) == 1
        }
        self._model.add( LSTM(layer.get('units',_DEFAULT_LAYER_SIZE), **config) )
        
        # Intermediate layers
        for idx,layer in enumerate(self._layers[1:]):
            config = {
                    'activation'        : layer.get('activation',_DEFAULT_ACTIVATION), 
                    'dropout'           : layer.get('dropout', _DEFAULT_DROPOUT) ,  
                    'use_bias'          : layer.get('bias',True),
                    'recurrent_dropout' : layer.get('recurrent_dropout', 0.0),
                    'return_sequences'  : len(self._layers[-1])-2 != idx 
            }
            self._model.add( LSTM(layer.get('units',_DEFAULT_LAYER_SIZE), **config) )
        
        # Output layer
        self._model.add( Dense( window, activation='sigmoid')  )
        
        # Compile model from parameters
        self._model.compile( loss=self._loss, optimizer=self._optimizer , metrics=self._metrics )
        
        # Print model
        if self._verbose != 0: print self._model.summary()



