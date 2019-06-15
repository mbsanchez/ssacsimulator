import csv
import pandas as pd

def get_station(column):
        col = column.split("_")
        station = "_".join(col[0:2])

        return station

def time_to_min(tm):
        return round(float(tm) * 10 * 60, 2)
                
		
with open('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\test_date.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        outFile = open('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\test_date_events.td', 'w')
        writeFile = csv.writer(outFile)
        writeFile.writerow(['Id', 'source', 'target', 'duration', 'start']);
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
                        
                for idxCol, v1 in row.items():
                        if (idxCol == 'Id'):
                                CaseId = str(int(v1))
                                continue

                        if idxCol == 'L3_S51_D4263' and source and CaseId and startV1 > 0:
                                writeFile.writerow([CaseId, source, 'END', 0, startV1])
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
                                                
                                row = [CaseId, source, target, startV2-startV1, startV1]
                                writeFile.writerow(row)
                                source = target
                                startV1 = startV2
                                target = None
                                startV2 = None
                index += 1
        outFile.close();
        print("test_date_events.td saved successfully");
        input('Press enter to exit to continue to next phase')

        print("Removing duplicates and Sorting data")
        events_df = pd.read_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\test_date_events.td', sep=",")
        events_df = events_df.drop_duplicates()
        max_time = events_df['start'].max()
        min_time = events_df['start'].min()
        rows = events_df.shape[0]
        #events_df.loc[-1] = [" "+str(rows), str(min_time), str(max_time), 0, 0]
        events_df = events_df.sort_values(by=['start', 'Id']);
        events_df.to_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\test_date_events.td', index=False)
        print('Events: ' + str(rows))
        print('Min time: ' + str(min_time))
        print('Max time: ' + str(max_time))

        input('Preprocessing finished with success, press enter to exit')
