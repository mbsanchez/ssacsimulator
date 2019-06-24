from keras.models import load_model
import pandas as pd
import numpy as np

def getPredictions(model, inputfile, nrows):
    test = None

try:
    if(nrows > 0):
       test = pd.read_csv(inputfile, nrows=nrows)
    else:
       test = pd.read_csv(inputfile)
       
    test_input = test.drop(columns=['Id'])
    test_input = test_input.replace(np.nan , 0)
    saved_model = load_model(model)
    print('getting predictions from input file')
    predictions = saved_model.predict(test_input)

    output = pd.DataFrame(predictions, columns=['prediction'])
    output.to_csv('predictions.csv', index=False)

    ltz = output[output < 0.5].count();
    print( "Success: " + str(ltz) )
    print( "Failures: " + str(output.shape[0] - ltz) )

    return output
except FileNotFoundError as error:
    print("Error opening data files: " + str(error))
    return None
    
