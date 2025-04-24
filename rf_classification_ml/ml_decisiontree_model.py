import numpy as np
import pandas as pd
import os
from sklearn.tree import DecisionTreeClassifier #plot_tree
from sklearn.utils.multiclass import unique_labels
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, confusion_matrix
import pickle
import sys
import matplotlib.pyplot as plt
import seaborn as sns


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
DATASET_FOLDER_NAME = 'spectrum_energy_dataset_1k_samples'
DATASET_PATH = os.path.join(ROOT_PATH, 'proposed_method', DATASET_FOLDER_NAME, 'preprocessed_dataset')
REPORT_PATH = os.path.join(ROOT_PATH, 'proposed_method', DATASET_FOLDER_NAME, 'report')
MODEL_SAVE_PATH = os.path.join(ROOT_PATH, 'proposed_method', DATASET_FOLDER_NAME, 'model')
FIGURE_SAVE_PATH = os.path.join(ROOT_PATH, 'proposed_method', DATASET_FOLDER_NAME, 'figure')
# DATASET_PATH = os.path.join(ROOT_PATH, 'previous_method', DATASET_FOLDER_NAME, 'preprocessed_dataset')
# REPORT_PATH = os.path.join(ROOT_PATH, 'previous_method', DATASET_FOLDER_NAME, 'report')
# MODEL_SAVE_PATH = os.path.join(ROOT_PATH, 'previous_method', DATASET_FOLDER_NAME, 'model')
# FIGURE_SAVE_PATH = os.path.join(ROOT_PATH, 'previous_method', DATASET_FOLDER_NAME, 'figure')
DATASET_NAME = [
    'rf_features_dataset_16.csv',
    'rf_features_dataset_32.csv',
    'rf_features_dataset_64.csv',
    'rf_features_dataset_128.csv',
    'rf_features_dataset_256.csv',
    # 'rf_features_dataset_512.csv',
    # 'rf_features_dataset_1024.csv',
    # 'rf_features_dataset_2048.csv',
    # 'rf_features_dataset_4096.csv',
    ]


# Create path
os.makedirs(REPORT_PATH, exist_ok=True)
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
os.makedirs(FIGURE_SAVE_PATH, exist_ok=True)

model_acc_list = []
model_size_list = []
dataset_mean = []
dataset_std = []
print("[*] Decision tree model training started...")
for idx, i in enumerate(DATASET_NAME):
    ''' Dataset Preprocessing '''
    df = pd.read_csv(os.path.join(DATASET_PATH, i))
    row, col = np.shape(df.values)
    x = df.values[:,:col - 1].astype('float32')
    y = df['rf_label'].values
    column_name = df.columns.values.tolist()
    
    # Predictor labeling
    y_label = unique_labels(y).reshape(-1, 1)
    enc = OneHotEncoder().fit(y_label)
    Y = enc.transform(y.reshape(-1, 1)).toarray() # type: ignore
    
    # Feature scaling
    scaler = StandardScaler()
    scaler.fit(x)
    X = scaler.transform(x)
    dataset_mean = scaler.mean_
    dataset_std = scaler.scale_
    
    ''' Dataset splitting for training and test '''
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.3)
    
    ''' Create and train classification model '''
    # Hyperparameter search using grid search
    params = {
        'max_leaf_nodes': np.arange(2,50),
        'max_depth': np.arange(1,50),
        }
    gs_clf = GridSearchCV(
        estimator=DecisionTreeClassifier(random_state=400),
        param_grid=params,
        cv=5
        )
    gs_clf.fit(X_train, Y_train)
    clf = gs_clf.best_estimator_ # Develop model based on chosen hyperparameter
    
    ''' Machine learning model size '''
    p = pickle.dumps(clf)
    model_size = sys.getsizeof(p)
    model_size_list.append(model_size)
    print("[*] Machine learning model size: {} bytes".format(model_size))

    ''' Save classifier model '''
    model_file_name = os.path.join(MODEL_SAVE_PATH, '{}_model.pickle'.format(DATASET_NAME[idx]))
    with open(model_file_name, 'wb') as f:
        f.write(p)
        f.close()
    
    ''' Save scaler model '''
    scaler_file_name = os.path.join(MODEL_SAVE_PATH, '{}_scaler.pickle'.format(DATASET_NAME[idx]))
    with open(scaler_file_name, 'wb') as f:
        scaler_params = {
            'scaler_mean': dataset_mean,
            'scaler_std': dataset_std
        }
        pickle.dump(scaler_params, f)
        f.close()
    
    ''' Accuracy score '''
    Y_pred = clf.predict(X_test)
    acc_score = accuracy_score(Y_test, Y_pred)
    model_acc_list.append(acc_score)
    print("[*] Machine learning model best accuracy: {}".format(acc_score))
    
    ''' Confusion matrix score '''
    cat_label = enc.categories_[0].tolist()
    cm = confusion_matrix(Y_test.argmax(axis=1), Y_pred.argmax(axis=1))
    cm = (cm/np.shape(Y_test)[0])*100
    cm_heatmap = sns.heatmap(cm, xticklabels=cat_label, yticklabels=cat_label, annot=True)
    fig_save_path = os.path.join(FIGURE_SAVE_PATH, "dtClassifier_heatmap_{}.png".format(i))
    plt.savefig(fig_save_path)
    plt.close()
    
    ''' Report overall process complete '''
    print("[*] Decision Tree training for '{}' dataset completed!".format(i))


''' Write model training report '''
report_f_name = os.path.join(REPORT_PATH, "dtClassifier_report.txt")
with open(report_f_name, "w") as f:
    f.write("Dataset name: {}\nBest model accuracy: {}\nModel size (bytes): {}\n".format(
        DATASET_NAME, model_acc_list, model_size_list))
    f.write("Dataset mean: {}\nDataset std: {}\n".format(dataset_mean, dataset_std))
f.close()
