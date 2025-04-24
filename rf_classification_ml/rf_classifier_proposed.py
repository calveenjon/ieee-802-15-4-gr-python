import numpy as np
import os
import pickle
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ONE_HOT_ENCODER_LABEL = ['BL_Beacon', 'BL_Stream', 'Microwave_Oven', 'WiFi_Beacon', 'WiFi_Stream']

class RFClassifier:
    threshold = -60.0 # in dBm
    window_size = 64
    buffer = []
    action = None
    rf_detect = None
    clf = None
    scaler = StandardScaler()
    
    ''' [TBC] Mitigation strategy value: {0 => switch channel, 1 => retransmit} '''
    mitigation_strategy = {
        'BL_Stream': 0,
        'BL_Beacon': 1,
        'Microwave_Oven': 0,
        'WiFi_Beacon': 0,
        'WiFi_Stream': 1
    }
    

    def __init__(self, threshold:float, window_size:int, ml_model_path:str, scaler_params:str) -> None:
        self.threshold = threshold
        self.window_size = window_size
        self.onehot_enc = OneHotEncoder().fit(np.array(ONE_HOT_ENCODER_LABEL).reshape(-1, 1))

        with open(scaler_params, 'rb') as f:
            params = pickle.load(f)
            self.scaler.mean_ = params['scaler_mean']
            self.scaler.scale_ = params['scaler_std']
            f.close()

        with open(ml_model_path, 'rb') as f:
            self.clf = pickle.load(f)
            f.close()


    def push_data(self, data:np.ndarray) -> None:
        self.action = None
        self.rf_detect = None
        self.buffer.append(np.max(data.flatten()))

        if len(self.buffer) >= self.window_size:
            a = np.array(self.buffer)
            a = self.thresholding(a)
            a = self.feature_extraction(a)
            
            if a is None:
                self.buffer.clear()
                return

            a = self.make_inference(a)
            self.rf_detect = a
            self.action = self.mitigation_scheme(a)
            self.buffer.clear()
        
        return
    

    ''' Convert RSSI values to binary traces (duty cycle) '''
    def thresholding(self, x:np.ndarray) -> np.ndarray:
        bin_thres = np.zeros(self.window_size, dtype=np.int8)

        for i in range(self.window_size):
            if x[i] >= self.threshold:
                bin_thres[i] = 1
            else:
                bin_thres[i] = 0

        return bin_thres
    

    ''' Feature extraction function. Output: [tx_max, cl_max, periodicity, usage_ratio] '''
    def feature_extraction(self, x:np.ndarray):
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
    

    ''' Machine learning inferencing function '''
    def make_inference(self, input_data:np.ndarray) -> str:
        x = input_data.reshape(1, -1)
        x = self.scaler.transform(x)
        y = self.clf.predict(x) # type: ignore
        rf_label_idx = np.argmax(y)
        rf_label = ONE_HOT_ENCODER_LABEL[rf_label_idx]

        return rf_label


    ''' [TBC] Make interference mitigation decision '''
    def mitigation_scheme(self, rf_label:str):
        return self.mitigation_strategy.get(rf_label, None)



''' UNIT TESTING '''
# a = np.random.randint(-60, -40, size=10)
# b = rssi2bt(a, -54)
# c = feature_extraction(b)

# print(a)
# print(b)
# print(c)