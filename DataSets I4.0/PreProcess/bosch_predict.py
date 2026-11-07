import argparse
from keras.models import load_model
import pandas as pd
import numpy as np

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    
    # Required
    parser.add_argument('--model', dest='model', required=True, help='(REQUIRED) path to the file containing the h5 model')
    parser.add_argument('--input', dest='input', required=True, help='(REQUIRED) path to input data file for predictions')
    # Optional
    parser.add_argument('--nrows', '-e', dest='nrows', default=-1, type=int, required=False, help='number of inputs to predict')
    
    args = parser.parse_args()

    test = None

    if(args.nrows > 0):
       test = pd.read_csv(args.input, nrows=args.nrows)
    else:
       test = pd.read_csv(args.input)
       
    test_input = test.drop(columns=['Id'])
    test_input = test_input.replace(np.nan , 0)
    saved_model = load_model(args.model)
    predictions = saved_model.predict(test_input)

    #print (len(predictions))
    #print(predictions)

    output = pd.DataFrame(predictions, columns=['prediction'])
    output.to_csv('predictions.csv', index=False)

    ltz = output[output < 0.5].count();
    print( "Success: " + str(ltz) )
    print( "Failures: " + str(output.shape[0] - ltz) )
    #print (output['prediction'].value_counts(dropna=False))
    #fails = output.loc[(output['prediction_0'] == 0) & (output['prediction_1'] == 0)]
    #print(fails.shape)

    print('Results saved to predictions.csv file')
    
