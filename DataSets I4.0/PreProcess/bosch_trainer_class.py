#Importing Data and Removing Unnecessary Coloumns
import pandas as pd

train_numeric = pd.read_csv('train_numeric.csv', nrows=10000)
train_date = pd.read_csv('train_date.csv', nrows=10000)
train_categorical = pd.read_csv('train_categorical.csv', nrows=10000, dtype=str)

train_date = train_date.drop("Id", axis=1)
train_categorical = train_categorical.drop("Id", axis=1)

#Changing Object Type Coloumns to Categorical Type Columns and then Cat Codes are being generated

c_names = list(train_categorical)
for col in c_names:
    train_categorical[col] = train_categorical[col].astype('category')
    train_categorical[col] = train_categorical[col].cat.codes

#Concatinating 3 Dataframes to 1 Dataframe

Data_Set = pd.concat([train_numeric, train_date], axis=1)
Data_Set = pd.concat([Data_Set, train_categorical], axis=1)

#Moving the Responce Columns(Label) to End of Dataframe

cols_at_end = ['Response']
Data_Set = Data_Set[[c for c in Data_Set if c not in cols_at_end] 
        + [c for c in cols_at_end if c in Data_Set]]

#Filling Null Values and Converting Dataframe to Numpy Array

Data_Set = Data_Set.fillna(0)
Data_Set_Arr = Data_Set.values

#Creating 80 20 Split to Generate Test and Training Data

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(Data_Set_Arr[:,1:4266], Data_Set_Arr[:,-1], test_size=0.2)

#Initializing Balanced Bagging Classifier and Fitting Classifier on the Training Dataset

from sklearn.ensemble import RandomForestClassifier
from imblearn.ensemble import BalancedBaggingClassifier

#model = RandomForestClassifier(class_weight=cw).fit(X_train, y_train)
model = BalancedBaggingClassifier(random_state=42, n_jobs=-1).fit(X_train, y_train)

#Validating the Classifier on Test Dataset and display of results via Confusion Matrix and Classification Report.

from sklearn.metrics import classification_report, confusion_matrix
predictions = model.predict(X_test)
print(confusion_matrix(y_test, predictions))
print(classification_report(y_test, predictions))

#Last Matthews correlation coefficient is being evaluated

from sklearn.metrics import matthews_corrcoef

print(matthews_corrcoef(y_test, predictions))
