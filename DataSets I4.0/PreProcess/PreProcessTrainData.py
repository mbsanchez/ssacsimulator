import csv
from datetime import datetime  
from datetime import timedelta 

currentDate = datetime.fromisoformat('2017-01-01')
with open('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date.csv') as csvfile:
	reader = csv.DictReader(csvfile)
	outFile = open('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date_output.csv', 'w')
	writeFile = csv.writer(outFile)
	writeFile.writerow(['Id', 'Activity', 'Date', 'Feature']);
	index = 0
	stopIndex = -1
	for row in reader:
		if stopIndex > 0 and index == stopIndex:
			break
		for column, value in row.items():
			if(column == 'Id' or not value):
				continue
			seconds = int(float(value) * 10 * 60 * 60 );
			date = currentDate +  timedelta(seconds=seconds)
			col = column.split("_")
			event = "_".join(col[0:2])
			f = col[2][1:]
			feature = 'F'+str(int(f)-1)
			writeFile.writerow([row['Id'], event, date.strftime('%Y-%m-%d %H:%M:%S'), feature])
		index += 1
	outFile.close();
	
import pandas as pd

df_csv = pd.read_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date_output.csv', sep=",")
df_csv = df_csv.drop(columns='Feature')
df_csv = df_csv.drop_duplicates()
df_csv.to_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date_output_nd.csv', index=False)