import pandas as pd

skip = input ("Rows to skip: ")
lenght = input ("Number of rows to load: ")
filename = input("output filename: ")

try:
    skip = int(skip)
    rows = int(lenght)

    df = None
    if skip > 0:
        if rows > 0:
            df = pd.read_csv('..\\test_date_events.td', sep=",", skiprows=range(1, skip-1), nrows=rows)
        else:
            df = pd.read_csv('..\\test_date_events.td', sep=",", skiprows=range(1, skip-1))
    else:
        if rows > 0:
            df = pd.read_csv('..\\test_date_events.td', sep=",", nrows=rows)
        else:
            df = pd.read_csv('..\\test_date_events.td', sep=",")

    print(df.head())

    max_time = df['start'].max()
    min_time = df['start'].min()
    rows = df.shape[0]
    df.loc[rows+1] = [" "+str(rows), str(min_time), str(max_time), 0, 0, -1]
    df = df.sort_values(by=['start', 'Id']);
    df.to_csv('..\\' + filename + '.td', index=False)

    print('Events: ' + str(rows))
    print('Min time: ' + str(min_time))
    print('Max time: ' + str(max_time))
except ValueError:
    print("Error processing the data")
    exit(1)

input('Preprocessing finished with success, press enter to exit')
