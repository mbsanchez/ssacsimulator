import csv
import pandas as pd
from keras.models import load_model
import numpy as np

def loadModel(model):
        try:
                saved_model = load_model(model)
                return saved_model
        except FileNotFoundError as error:
                print("Error opening model file: " + str(error))
                return None

def getPredictions(model, data):          
        try:
            data = data.replace(np.nan , 0)
            predictions = model.predict(data)

            output = pd.DataFrame(predictions, columns=['prediction'])
            ltz = output[output < 0.5].count()

            return int(output.shape[0] - ltz)
        except FileNotFoundError as error:
            print("Error opening data files: " + str(error))
            return None

def get_station(column):
        col = column.split("_")
        station = "_".join(col[0:2])

        return station

def time_to_min(tm):
        return round(float(tm) * 10 * 60, 2)
     
model = None	 
try:
        model = loadModel(basePath + '\\bosch_predictive_model.h5')
except FileNotFoundError as error:
        print("Error opening data files: " + str(error))

features = pd.read_csv(basePath + '\\test_numeric.csv')
basePath = 'C:\\Users\\mbsanchez\\Documents\\Bosch'

with open(basePath + '\\test_date.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        outFile = open(basePath + '\\test_date_events.td', 'w')
        writeFile = csv.writer(outFile)
        writeFile.writerow(['Id', 'source', 'target', 'duration', 'start', 'prediction'])
        index = 0
        stopIndex = -1
        min_time = -1
        max_time = -1
        for row in reader:
                if stopIndex > 0 and index == stopIndex:
                        break
                                
                CaseId = None
                source = None
                target = None
                start = None
                startV1 = None
                startV2 = None
                prediction = -1
                saved = True
                        
                for idxCol, v1 in row.items():
                        if (idxCol == 'Id'):
                                CaseId = str(int(v1))
                                f_row = features.iloc[index].to_frame().T
                                f_row = f_row.drop(columns=['Id'])

                                if model:
                                        prediction = getPredictions(model, f_row)                 
                                        saved = False
                                continue

                        if idxCol == 'L3_S51_D4263' and source and CaseId and startV1 > 0:
                                writeFile.writerow([CaseId, source, 'END', 0, startV1, -1])
                                continue
                                
                        if (not v1):
                                continue
                                 
                        if (not source):
                                source = get_station(idxCol)
                                startV1 = time_to_min(v1)
                        else:
                                target = get_station(idxCol)
                                startV2 = time_to_min(v1)

                        if (CaseId and source and target and startV1 and startV2):
                                if(source == target and startV1 == startV2):
                                        target = None
                                        startV2 = None
                                        continue

                                
                                predict = -1 if saved else prediction
                                        
                                row = [CaseId, source, target, startV2-startV1, startV1, predict]
                                writeFile.writerow(row)
                                source = target
                                startV1 = startV2
                                target = None
                                startV2 = None
                                saved = True
                index += 1
        outFile.close();
        print("test_date_events.td saved successfully.")
        print("Removing duplicates and Sorting data...")
        events_df = pd.read_csv(basePath+'\\test_date_events.td', sep=",")
        events_df = events_df.drop_duplicates()
        max_time = events_df['start'].max()
        min_time = events_df['start'].min()
        rows = events_df.shape[0]
        events_df = events_df.sort_values(by=['start', 'Id']);
        events_df.to_csv(basePath+'\\test_date_events.td', index=False)
        print('Events: ' + str(rows))
        print('Min time: ' + str(min_time))
        print('Max time: ' + str(max_time))

        input('Preprocessing finished with success, press enter to exit')
