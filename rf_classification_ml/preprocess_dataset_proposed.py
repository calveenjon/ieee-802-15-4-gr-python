import numpy as np
import pandas as pd
import os


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
DATASET_FOLDER_NAME = 'spectrum_energy_dataset_1k_samples'
DATASET_PATH = os.path.join('D:\\', 'VM_Shared', DATASET_FOLDER_NAME)
PREPROCESSED_DATASET_PATH = os.path.join(ROOT_PATH, 'proposed_method', DATASET_FOLDER_NAME, 'preprocessed_dataset')
# PREPROCESSED_DATASET_PATH = os.path.join(ROOT_PATH, 'previous_method', DATASET_FOLDER_NAME, 'preprocessed_dataset')
DATASET_NAME = [
    'bluetooth_beacon_4MHz.dat',
    'bluetooth_stream_4MHz.dat',
    'microwave_oven_4MHz.dat',
    'wifi_beacon_4MHz.dat',
    'wifi_stream_4MHz.dat',
    ]
CLASS_LABEL = ['BL_Beacon', 'BL_Stream', 'Microwave_Oven', 'WiFi_Beacon', 'WiFi_Stream']
DETECTION_SENSITIVITY = -60.0
SAMPLE_WINDOW_SIZE = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
FFT_WINDOW_SIZE = 1024


''' Convert RSSI values to binary traces (duty cycle) '''
def rf_presence_conv(x:np.ndarray) -> np.ndarray:
    rssi_val_len = np.shape(x)[0]
    bt_rssi = np.zeros((rssi_val_len,), dtype=np.uint8)
    
    for i in range(rssi_val_len):
        if np.max(x[i]) >= DETECTION_SENSITIVITY: # Energy above threshold
        # if x[i] >= DETECTION_SENSITIVITY: # Energy above threshold
            bt_rssi[i] = 1
        else: # Energy below threshold
            bt_rssi[i] = 0
    
    return bt_rssi


''' Feature extraction function '''
def feature_extraction(x:np.ndarray):
    n = np.shape(x)[0]
    loc_run_start = np.empty(n, dtype=bool)
    loc_run_start[0] = True
    np.not_equal(x[:-1], x[1:], out=loc_run_start[1:])
    run_starts = np.nonzero(loc_run_start)[0]
    
    # find run values
    run_values = x[loc_run_start]
    
    # find run lengths
    run_lengths = np.diff(np.append(run_starts, n))
    
    tx_t_count = run_lengths[np.nonzero(run_values == 1)[0]]
    cl_t_count = run_lengths[np.nonzero(run_values == 0)[0]]
    if len(tx_t_count) > 0:
        tx_max = np.max(tx_t_count) # Max chan usage duration
        tx_min = np.min(tx_t_count) # Min chan usage duration
        
        cl_max = 0 # Max chan clear duration
        cl_min = 0 # Min chan clear duration
        if len(cl_t_count) > 0: 
            cl_max = np.max(cl_t_count) 
            cl_min = np.max(cl_t_count) 
        
        periodicity = n/(tx_max + cl_max) # Periodicity
        usage_ratio = np.sum(tx_t_count)/n # Chan usage ratio
        # results = np.array([tx_max, tx_min, cl_max, cl_min, periodicity, usage_ratio])
        # results = np.array([tx_max, cl_min, usage_ratio])
        # results = np.array([tx_max, usage_ratio])
        # results = np.array([tx_max, cl_max])
        results = np.array([tx_max, tx_min, cl_max, usage_ratio])
    else:
        results = None
    
    return results


''' Reshape array of binary traces based on window size '''
def arr_windowing(x:np.ndarray, window_size):
    rssi_val_len = np.shape(x)[0]
    excess_datapoint = rssi_val_len % window_size
    bt_window = x[:rssi_val_len-excess_datapoint]
    bt_window_len = np.shape(bt_window)[0]
    bt_window = np.reshape(bt_window, (int(bt_window_len/window_size), window_size))
    
    return bt_window


''' Feature extraction loop '''
def fe_loop(x:np.ndarray):
    x_len = np.shape(x)[0]
    fe_tx = []
    
    for i in range(x_len):
        a = feature_extraction(x[i])
        if a is not None:
            fe_tx.append(a)
    
    return np.vstack(fe_tx)


''' Main program '''
print("[*] Dataset generator script is running...")
# header = ["tx_period_max", "cl_period_max", "periodicity", "duty_cycle", "rf_label"]
# header = ["tx_period_max", "tx_period_min", "cl_period_max", "cl_period_min", "periodicity", "duty_cycle", "rf_label"]
# header = ["tx_period_max", "cl_period_min", "duty_cycle", "rf_label"]
# header = ["tx_period_max", "duty_cycle", "rf_label"]
# header = ["tx_period_max", "cl_period_min", "rf_label"]
header = ["tx_period_max", "tx_period_min", "cl_period_max", "duty_cycle", "rf_label"]

# Create path
os.makedirs(PREPROCESSED_DATASET_PATH, exist_ok=True)

for k in range(len(SAMPLE_WINDOW_SIZE)):
    dataset = None
    for i in range(len(DATASET_NAME)):
        raw_data = np.fromfile(os.path.join(DATASET_PATH, DATASET_NAME[i]), dtype=np.float32)
        raw_data = np.reshape(raw_data, (-1, FFT_WINDOW_SIZE))
        proc_data = rf_presence_conv(raw_data)
        proc_data = arr_windowing(proc_data, SAMPLE_WINDOW_SIZE[k])
        fe_data = fe_loop(proc_data)
        data_label = np.full(np.shape(fe_data)[0], CLASS_LABEL[i]).reshape(-1, 1)
        data_concat = np.concatenate((fe_data, data_label), axis=1)
        data_unique = np.unique(data_concat, axis=0) # Remove redundant features
    
        if dataset is None:
            dataset = data_unique
        else:
            dataset = np.concatenate((dataset, data_unique), axis=0)
    
    df = pd.DataFrame(dataset, columns=header)
    df = df.sample(frac=1).reset_index(drop=True)
    df_f_name = os.path.join(
        PREPROCESSED_DATASET_PATH, 
        "rf_features_dataset_{}.csv".format(SAMPLE_WINDOW_SIZE[k]))
    df.to_csv(df_f_name, index=False)
    print("[*] Dataset for {} window size has been saved!".format(SAMPLE_WINDOW_SIZE[k]))