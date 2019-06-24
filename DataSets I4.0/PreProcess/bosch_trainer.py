'''
This script builds and trains a simple Convolutional Nerual Network (CNN)
against a supplied data set. It is used in a tutorial demonstrating
how to build Keras models and run them in native C++ Tensorflow applications.


MIT License

Copyright (c) 2017 bitbionic

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from datetime import datetime
import os
import argparse

import pandas as pd
import numpy as np


from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout

from keras.callbacks import ModelCheckpoint
from keras.callbacks import EarlyStopping
from keras.utils import to_categorical
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2
from keras.models import load_model

from sklearn import datasets, linear_model
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
from sklearn.preprocessing import LabelEncoder
from matplotlib import pyplot


def buildClassifier( ninputs ):
    '''
    Builds a very simple CNN outputing num_categories.
    
    Args:
             ninputs (int): number of input to the model
 
    Returns:
        keras.models.Model: a simple CNN
    
    '''

    #create model
    model = Sequential()

    #add layers to model
    model.add(Dense(ninputs, kernel_regularizer=l2(0.001), activation='relu', input_shape=(ninputs,)))
    #model.add(Dropout(0.5))
    #model.add(LeakyReLU(alpha=0.3))
    model.add(Dense(ninputs*2+1, activation='relu'))
    #model.add(Dropout(0.5))
    #model.add(LeakyReLU(alpha=0.3))
    #model.add(Dense(250, activation='relu'))
    #model.add(Dropout(0.5))
    #model.add(LeakyReLU(alpha=0.3))
    model.add(Dense(1))
    
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    
    return model


def trainModel( trainfile, output_dir='./', num_epochs=30 ):
    '''
    Trains the supplied model agaist train and test files specified
    in the args. During the training, each epoch will be evaluated for 
    val_loss and the model will be saved if val_loss is lower than
    previous.
    
    Args:
        classifier trainfile (str): the location of the training file
                       output_dir (str): the directory where output files are saved
                       num_epochs (int): the number of epochs to train a model
    
    Returns:
        keras.models.Model: returns the trained CNN
    '''
    train_df = pd.read_csv(trainfile)
    train_df = train_df.replace(np.nan , 0)
    train_input = train_df.drop(columns=['Id','Response'])
    train_output = train_df[['Response']]
    #train_output = to_categorical(train_df.Response) #1 0 not fail, 0 1 fail
    ninputs = train_input.shape[1]

    print (train_output.Response.value_counts(dropna=False))

    y = train_output.Response.tolist()
    class_weights = class_weight.compute_class_weight('balanced',
                                                 np.unique(y),
                                                 y)
    class_weight_dict = dict(enumerate(class_weights))

    print(class_weight_dict)

    # Saves the model weights after each epoch if the validation loss decreased
    now = datetime.now()
    nowstr = now.strftime('bosch-%Y%m%d%H%M%S')

    now = os.path.join( output_dir, nowstr)

    # Make the directory
    os.makedirs( now, exist_ok=True )

    # Create our callbacks
    savepath = os.path.join( now, 'e-{epoch:03d}-vl-{val_loss:.3f}-va-{val_acc:.3f}.h5' )
    checkpointer = ModelCheckpoint(filepath=savepath, monitor='val_acc', mode='max', verbose=1, save_best_only=True)
    
    # patient early stopping
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=3)

    classifier = buildClassifier(ninputs)
    classifier.fit(train_input, train_output,
                   validation_split=0.2,
                   class_weight=class_weight_dict,
                   epochs=num_epochs,
                   callbacks=[es, checkpointer])
    
    return classifier


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    # Required
    parser.add_argument('--train', dest='train', required=True, help='(REQUIRED) path to the train data ')
    # Optional
    parser.add_argument('--output', '-o', dest='output', default='./', required=False, help='location of the output directory (default:./)')
    parser.add_argument('--epochs', '-e', dest='epochs', default=30, type=int, required=False, help='number of epochs to run (default:30)')
    
    args = parser.parse_args()
    
    trainModel( args.train, args.output, num_epochs=args.epochs )
    
