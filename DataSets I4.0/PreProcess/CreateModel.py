import pandas as pd
import itertools

baseFileName = input("Base filename: ")
modelName = input("Model name: ")
throughputTime = input ("Enter throughput time in min: ")

try:
    throughputTm = int(throughputTime)
except ValueError as error:
    print("Error processing the data: " + str(error))
    exit(1)


times_df = None
cases_df = None
actors_df = None
visibility_df = None

try:
    times_df = pd.read_csv(baseFileName+"_times.csv", sep=",")
    cases_df = pd.read_csv(baseFileName+"_cases.csv", sep=",")
    actors_df = pd.read_csv(baseFileName+"_actors.csv", sep=",")
except FileNotFoundError as error:
    print("Error opening data files: " + str(error))
    exit(1)

visFileExists = True
try:
    visibility_df = pd.read_csv(baseFileName+"_vis.csv", sep=",")
except FileNotFoundError as error:
    visFileExists = False
    print("Warning: Visibility data file not found, all edges must be not shown. " + str(error))
    

num_c_times = times_df.shape[1]
num_c_cases = cases_df.shape[1]

if(actors_df.shape[0] != 1 or actors_df.shape[0] != 1):
    print("Invalid actors file")
    exit(1)

if num_c_times != num_c_cases:
    print("Error: number of columns mismatched!")
    exit(1)
    
actorsStr = actors_df.iloc[0].head(1).item()
actorsList = actorsStr.split(",")
beginActors = [s for s in actorsList if s.startswith("+")]
endActors = [s for s in actorsList if s.startswith("-")]

if(len(beginActors)!=1):
    print('Error you must define one begin actor using (+)')
    exit(1)

if(len(endActors)==0):
    print('Error you must define at least one end actor using (-)')
    exit(1)

totalCases = 0
df_combined = pd.DataFrame(columns=['transitions:'])
for ( idxRow, s1 ), ( _, s2 ) in zip( times_df.iterrows(), cases_df.iterrows() ) :
    concat = '';
    for ( idxCol, v1 ), ( _, v2 ) in zip( s1.iteritems(), s2.iteritems() ) :
        if idxCol == 'actor':
            continue
        if (not pd.isna(v1)) and (not pd.isna(v2)):
            if "+" + str(s2.head(1).item()) in beginActors:
                totalCases = totalCases + v2

            visibility = '0'
            if visFileExists:
                vis = visibility_df[idxCol].iloc[idxRow]
                visibility = '0' if pd.isna(vis) or vis != 1  else '1'
            
            concat = concat + ";".join([idxCol,str(v1),str(v2), str(visibility)])+"!"
    df_combined.loc[idxRow] = s1[0] + '=' + concat[:-1]

if(df_combined.shape[0]==0 or df_combined.shape[1]!=1):
    print("Error: the transitions graph is empty")
    exit(1)

modelFile = open(baseFileName + "_model.pg", 'w')

modelFile.write("process:"+modelName+'\n')
modelFile.write("actors:"+actorsStr+'\n')
modelFile.write("process_througout_time:"+str(throughputTm)+'\n')
modelFile.write("total_cases:"+str(int(totalCases))+'\n')
modelFile.write("transitions:"+'\n')

for v1 in df_combined['transitions:']:
    modelFile.write(v1+'\n')

modelFile.close()
#df_combined.to_csv(baseFileName + "_model.pg", index=False)

print("Model create successfully")
