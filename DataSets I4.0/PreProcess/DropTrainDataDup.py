import pandas as pd

df_csv = pd.read_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date_output.csv', sep=",")
df_csv = df_csv.drop(columns='Feature')
df_csv = df_csv.drop_duplicates()
df_csv.to_csv('D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\train_date_output_nd.csv', index=False)