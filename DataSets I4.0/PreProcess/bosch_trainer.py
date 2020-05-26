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
import pickle


from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout

from keras.callbacks import Callback
from keras.callbacks import ModelCheckpoint
from keras.callbacks import EarlyStopping
from keras.utils import to_categorical
from keras.layers.advanced_activations import LeakyReLU
from keras.regularizers import l2
from keras.models import load_model
from keras import backend as K

from sklearn import datasets, linear_model
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import matthews_corrcoef
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import f1_score
from sklearn.metrics import auc
from imblearn.ensemble import BalancedBaggingClassifier
from imblearn.ensemble import BalancedRandomForestClassifier
from matplotlib import pyplot

class ModelMetrics(Callback):
  
  def on_train_begin(self,logs={}):
    self.precisions=[]
    self.recalls=[]
    self.f1_scores=[]
  def on_epoch_end(self, batch, logs={}):
    
    y_val_pred=self.model.predict_classes(x_val)
   
    _precision,_recall,_f1,_sample=score(y_val,y_val_pred)  
    
    self.precisions.append(_precision)
    self.recalls.append(_recall)
    self.f1_scores.append(_f1)
    print([_precisions, _recall, _f1])


def recall_m(y_true, y_pred):
    y_true = K.ones_like(y_true) 
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    all_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    
    recall = true_positives / (all_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    y_true = K.ones_like(y_true) 
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_score_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

def matt_coef(y_true, y_pred):
    y_pred_pos = K.round(K.clip(y_pred, 0, 1))
    y_pred_neg = 1 - y_pred_pos

    y_pos = K.round(K.clip(y_true, 0, 1))
    y_neg = 1 - y_pos

    tp = K.sum(y_pos * y_pred_pos)
    tn = K.sum(y_neg * y_pred_neg)

    fp = K.sum(y_neg * y_pred_pos)
    fn = K.sum(y_pos * y_pred_neg)

    numerator = (tp * tn - fp * fn)
    denominator = K.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))

    return numerator / (denominator + K.epsilon())

def joinDSAndSave(rows):
    print ("Loading the Bosch training datasets")
    
    train_numeric = pd.read_csv('train_numeric.csv', nrows=rows, low_memory=False)
    train_date = pd.read_csv('train_date.csv', nrows=rows, low_memory=False)
    train_categorical = pd.read_csv('train_categorical.csv', nrows=rows, dtype=str, low_memory=False)

    train_date = train_date.drop("Id", axis=1)
    train_categorical = train_categorical.drop("Id", axis=1)

    print("Changing Object Type Columns to Categorical Type Columns and then Cat Codes are being generated")
    c_names = list(train_categorical)
    for col in c_names:
        train_categorical[col] = train_categorical[col].astype('category')
        train_categorical[col] = train_categorical[col].cat.codes

    print("Concatinating 3 Dataframes to 1 Dataframe")
    Data_Set = pd.concat([train_numeric, train_date], axis=1)
    Data_Set = pd.concat([Data_Set, train_categorical], axis=1)

    print("Moving the Responce Columns(Label) to End of Dataframe")
    cols_at_end = ['Response']
    Data_Set = Data_Set[[c for c in Data_Set if c not in cols_at_end] 
            + [c for c in cols_at_end if c in Data_Set]]

    print("Filling Null Values and Converting Dataframe to Numpy Array")
    Data_Set = Data_Set.fillna(0)
    #Data_Set_Arr = Data_Set.values
    Data_Set.to_csv('combined-ds.csv', index=False)

    print("The dataset combined was saved to disk")

def calculateMetrics(classifier, test_input, test_output, filename):
    print("Calculating predictions")
    isCnn = "cnn" in filename
    predictions = classifier.predict(test_input)
    if(isCnn):
      predictions = predictions.round()
    cfm = confusion_matrix(test_output, predictions)
    cl_report = classification_report(test_output, predictions)
    mcc = matthews_corrcoef(test_output, predictions)
    print("\nConfusion Matrix\n\n{}\n\nClassification Report\n\n{}\n".format(cfm, cl_report))  
    print("MCC: ", mcc)

    # generate a no skill prediction (majority class)
    ns_probs = [0 for _ in range(len(test_output))]

    # predict probabilities
    lr_probs = classifier.predict_proba(test_input)
    # keep probabilities for the positive outcome only
    if(not isCnn):
      lr_probs = lr_probs[:, 1]
    else:
      lr_probs = lr_probs[:, 0]
    # calculate scores
    ns_auc = roc_auc_score(test_output, ns_probs)
    lr_auc = roc_auc_score(test_output, lr_probs)
    # summarize scores
    print('No Skill: ROC AUC=%.3f' % (ns_auc))
    print('Logistic: ROC AUC=%.3f' % (lr_auc))
    # calculate roc curves
    ns_fpr, ns_tpr, _ = roc_curve(test_output, ns_probs)
    lr_fpr, lr_tpr, _ = roc_curve(test_output, lr_probs)
    # plot the roc curve for the model
    fig = pyplot.figure()
    pyplot.plot(ns_fpr, ns_tpr, linestyle='--', label='No Skill')
    pyplot.plot(lr_fpr, lr_tpr, marker='.', label='Logistic')
    # axis labels
    pyplot.xlabel('False Positive Rate')
    pyplot.ylabel('True Positive Rate')
    # show the legend
    pyplot.legend()
    # save the plot
    fig.savefig("{}-roc.png".format(filename))
    pyplot.close(fig)

    # predict class values
    lr_precision, lr_recall, _ = precision_recall_curve(test_output, lr_probs)
    lr_f1, lr_auc = f1_score(test_output, predictions), auc(lr_recall, lr_precision)
    # summarize scores
    print('Logistic: f1=%.3f auc=%.3f' % (lr_f1, lr_auc))
    # plot the precision-recall curves
    no_skill = len(test_output[test_output==1]) / len(test_output)
    fig = pyplot.figure()
    pyplot.plot([0, 1], [no_skill, no_skill], linestyle='--', label='No Skill')
    pyplot.plot(lr_recall, lr_precision, marker='.', label='Logistic')
    # axis labels
    pyplot.xlabel('Recall')
    pyplot.ylabel('Precision')
    # show the legend
    pyplot.legend()
    # save the plot
    fig.savefig("{}-pr.png".format(filename))
    pyplot.close(fig)

    #Write info to file
    file = open("{}-info.txt".format(filename),"w")
    file.write("Confusion Matrix\n\n{}\n\nClassification Report\n\n{}\n".format(cfm, cl_report))

    file.write("\nMCC: %0.4f\n" % (mcc))
    file.write('No Skill: ROC AUC=%.4f\n' % (ns_auc))
    file.write('Logistic: ROC AUC=%.4f\n' % (lr_auc))
    file.write('Logistic: f1=%.4f auc=%.4f\n' % (lr_f1, lr_auc))
    file.close()
    

def loadCombinedDSAndSplit(rows):
    train_numeric = pd.read_csv('combined-ds.csv', nrows=rows, low_memory=False)
    Data_Set_Arr = train_numeric.values
    print("Creating 80 20 Split to Generate Test and Training Data")
    return train_test_split(Data_Set_Arr[:,1:4266], Data_Set_Arr[:,-1], test_size=0.2)


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
    model.add(Dense(int(ninputs/2), kernel_regularizer=l2(0.001), activation='relu', input_shape=(ninputs,)))
    #model.add(Dropout(0.5))
    #model.add(LeakyReLU(alpha=0.3))
    model.add(Dense(int(ninputs/4), kernel_regularizer=l2(0.001), activation='relu'))
    #model.add(Dropout(0.5))
    #model.add(LeakyReLU(alpha=0.3))
    model.add(Dense(int(ninputs/8), kernel_regularizer=l2(0.001), activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy', recall_m, precision_m, f1_score_m, matt_coef])
    
    return model

def buildBaggingClassifier():
    return BalancedBaggingClassifier(random_state=54, n_jobs=-1)

def buildBalancedRandomForestClassifier(class_weights):
    return BalancedRandomForestClassifier(n_estimators=100, random_state=54, class_weight=class_weights)

def trainRandomForestClassifier(train_input, train_output, test_input, test_output, savepath='./', num_epochs=30):
    print("\nStarting Balanced Random Forest Training method")
    print("Creating new output folder")
    # Make the directory
    os.makedirs( savepath, exist_ok=True )
    
    y = train_output
    class_weights = class_weight.compute_class_weight('balanced',
                                                 np.unique(y),
                                                 y)
    class_weight_dict = dict(enumerate(class_weights))

    print("Creating the Random Forest classifier")
    classifier = buildBalancedRandomForestClassifier(class_weight_dict)
    
    print("Training the Random Forest classifier")
    classifier.fit(train_input, train_output)

    #Save the model
    filename = '{}/rf-{}'.format(savepath, datetime.now().strftime('%Y%m%d%H%M%S'))
    pickle.dump(classifier, open("{}.sav".format(filename), 'wb'))

    #calculate and save metrics
    calculateMetrics(classifier, test_input, test_output, filename)

def trainBaggingClassifier(train_input, train_output, test_input, test_output, savepath='./', num_epochs=30):
    print("\nStarting Balanced Bagging Training method")
    print("Creating new output folder")
    # Make the directory
    os.makedirs( savepath, exist_ok=True )

    print("Creating the Bagging classifier")
    classifier = buildBaggingClassifier()
    
    print("Training the Baggin classifier")
    classifier.fit(train_input, train_output)

    #Save the model
    filename = '{}/bagging-{}'.format(savepath, datetime.now().strftime('%Y%m%d%H%M%S'))
    pickle.dump(classifier, open("{}.sav".format(filename), 'wb'))

    #calculate and save metrics
    calculateMetrics(classifier, test_input, test_output, filename)

def trainSVM(train_input, train_output, test_input, test_output, savepath='./'):
    print("\nStarting SVM Training method")
    print("Creating new output folder")
    # Make the directory
    os.makedirs( savepath, exist_ok=True )
    
    from sklearn.svm import SVC
    print("Creating the SVM classifier")
    classifier = SVC(kernel='linear', 
                  class_weight='balanced', # penalize
                  probability=True)

    print("Training the SVM classifier")
    classifier.fit(train_input, train_output)
    
    #Save the model
    filename = '{}/svm-{}'.format(savepath, datetime.now().strftime('%Y%m%d%H%M%S'))
    pickle.dump(classifier, open("{}.sav".format(filename), 'wb'))

    #calculate and save metrics
    calculateMetrics(classifier, test_input, test_output, filename)

def trainLDA(train_input, train_output, test_input, test_output, savepath='./'):
    print("\nStarting LDA Training method")
    print("Creating new output folder")
    # Make the directory
    os.makedirs( savepath, exist_ok=True )
    
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    print("Creating the LDA classifier")
    classifier = LDA()

    print("Training the LDA classifier")
    classifier.fit(train_input, train_output)

    #Save the model
    filename = '{}/lda-{}'.format(savepath, datetime.now().strftime('%Y%m%d%H%M%S'))
    pickle.dump(classifier, open("{}.sav".format(filename), 'wb'))

    #calculate and save metrics
    calculateMetrics(classifier, test_input, test_output, filename)

def trainLinearDiscriminantAnalysis(train_input, train_output, test_input, test_output, savepath='./'):
    print("\nStarting LinearDiscriminantAnalysis Training method")
    print("Creating new output folder")
    # Make the directory
    os.makedirs( savepath, exist_ok=True )
    
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
    print("Creating the LinearDiscriminantAnalysis classifier")
    classifier = LinearDiscriminantAnalysis()

    print("Training the LinearDiscriminantAnalysis classifier")
    classifier.fit(train_input, train_output)

    #Save the model
    filename = '{}/linearda-{}'.format(savepath, datetime.now().strftime('%Y%m%d%H%M%S'))
    pickle.dump(classifier, open("{}.sav".format(filename), 'wb'))

    #calculate and save metrics
    calculateMetrics(classifier, test_input, test_output, filename)



def trainCNNModel(train_input, train_output, test_input, test_output, output_dir='./', num_epochs=30 ):
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
    #train_df = pd.read_csv(trainfile)
    #train_df = train_df.replace(np.nan , 0)
    #train_input = train_df.drop(columns=['Id','Response'])  
    #train_output = train_df[['Response']]
    #train_output = to_categorical(train_df.Response) #1 0 not fail, 0 1 fail   
    ninputs = train_input.shape[1]

    unique, counts = np.unique(train_output, return_counts=True)
    print (dict(zip(unique, counts)))

    y = train_output
    class_weights = class_weight.compute_class_weight('balanced',
                                                 np.unique(y),
                                                 y)
    class_weight_dict = dict(enumerate(class_weights))

    print(class_weight_dict)

    # Make the directory
    os.makedirs( output_dir, exist_ok=True )

    # Create our callbacks to saves the model weights after each epoch if the validation loss decreased
    savepath = os.path.join( output_dir, 'e-{epoch:03d}-vl-{val_loss:.4f}-va-{val_acc:.4f}-vp-{val_precision_m:.4f}-vr-{val_recall_m:.4f}-vf1-{val_f1_score_m:.4f}-{val_matt_coef:.4f}.h5' )
    checkpointer = ModelCheckpoint(filepath=savepath, monitor='acc', mode='max', verbose=1, save_best_only=True)
    
    # patient early stopping
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=3)

    #x_train, x_test, y_train, y_test = train_test_split(train_input, train_output, test_size=0.33)

    classifier = buildClassifier(ninputs)
    metrics=ModelMetrics()
    history = classifier.fit(train_input, train_output,
                   validation_data=(test_input, test_output),
                   class_weight=class_weight_dict,
                   epochs=num_epochs,
                   callbacks=[es, checkpointer])

    #loss, accuracy, f1_score_m, precision, recall = model.evaluate(x_test, y_test, verbose=0)
    #print ([loss, accuracy, f1_score_m, precision, recall])

    # plot loss during training
    fig = pyplot.figure()
    pyplot.subplot(211)
    pyplot.title('Loss')
    pyplot.plot(history.history['loss'], label='train')
    pyplot.plot(history.history['val_loss'], label='test')
    pyplot.legend()
    # plot accuracy during training
    pyplot.subplot(212)
    pyplot.title('Accuracy')
    pyplot.plot(history.history['acc'], label='train')
    pyplot.plot(history.history['val_acc'], label='test')
    pyplot.legend()
    # save the plot
    filename = '{}/cnn-{}'.format(output_dir, datetime.now().strftime('%Y%m%d%H%M%S'))
    fig.savefig("{}-loss-acc.png".format(filename))
    pyplot.close(fig)
    
    calculateMetrics(classifier, test_input, test_output, filename)
   
    return classifier


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    # Required
    #parser.add_argument('--train', dest='train', required=True, help='(REQUIRED) path to the train data ')
    # Optional
    parser.add_argument('--nrows', '-nr', dest='nrows', default=1000000, required=True, type=int, help='Number of rows to load from Dataset')
    parser.add_argument('--output', '-o', dest='output', default='./', required=False, help='location of the output directory (default:./)')
    parser.add_argument('--epochs', '-e', dest='epochs', default=30, type=int, required=False, help='number of epochs to run (default:30)')
    parser.add_argument('--skip-cnn', '-sc', dest='trainCNN', action='store_false', help='train Convolutional Neural Network')
    parser.add_argument('--skip-rf', '-srf', dest='trainRF', action='store_false', help='train Random Forest Classifier')
    parser.add_argument('--skip-bg', '-sbc', dest='trainBC', action='store_false', help='train Bagging Classifier')
    parser.add_argument('--skip-svm', '-ssvm', dest='trainSVM', action='store_false', help='train SVM Classifier')
    parser.add_argument('--skip-lda', '-slda', dest='trainLDA', action='store_false', help='train LDA Classifier')
    parser.add_argument('--skip-linearda', '-slda2', dest='trainLinearDA', action='store_false', help='train LinearDiscriminantAnalysis Classifier')
    parser.add_argument('--skip-join-ds', '-sjds', dest='joinDS', action='store_false', help='Skip merging the three Datasets into one')
    
    args = parser.parse_args()

    if(args.joinDS):
      joinDSAndSave(args.nrows)
    
    train_input, test_input, train_output, test_output = loadCombinedDSAndSplit(args.nrows)

    now = datetime.now()
    nowstr = now.strftime('bosch-%Y%m%d%H%M%S')

    outputdir = os.path.join( args.output, nowstr)
    
    if(args.trainCNN):
      trainCNNModel(train_input, train_output, test_input, test_output, outputdir, args.epochs)
    if(args.trainRF):
      trainRandomForestClassifier(train_input, train_output, test_input, test_output, outputdir, args.epochs)
    if(args.trainBC):
      trainBaggingClassifier(train_input, train_output, test_input, test_output, outputdir, args.epochs)
    if(args.trainLDA):
      trainLDA(train_input, train_output, test_input, test_output, outputdir)
    if(args.trainSVM):
      trainSVM(train_input, train_output, test_input, test_output, outputdir)
    if(args.trainLinearDA):
      trainLinearDiscriminantAnalysis(train_input, train_output, test_input, test_output, outputdir)
