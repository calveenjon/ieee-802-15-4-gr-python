import numpy as np
import os
import pickle
import sys
import matplotlib.pyplot as plt


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
# DATASET_PATH = os.path.join(ROOT_PATH, 'rf_psd_data', 'bluetooth_stream_4MHz.dat')
# DATASET_PATH = os.path.join(ROOT_PATH, 'rf_psd_data', 'bluetooth_beacon_4MHz.dat')
# DATASET_PATH = os.path.join(ROOT_PATH, 'rf_psd_data', 'microwave_oven_4MHz.dat')
# DATASET_PATH = os.path.join(ROOT_PATH, 'rf_psd_data', 'wifi_stream_4MHz.dat')
DATASET_PATH = os.path.join(ROOT_PATH, 'rf_psd_data', 'wifi_beacon_4MHz.dat')

psd_data = np.fromfile(os.path.join(DATASET_PATH, DATASET_PATH), dtype=np.float32)
print(len(psd_data))

plt.plot(psd_data)
plt.grid(True)
plt.show()