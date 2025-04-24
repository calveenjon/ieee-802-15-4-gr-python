import zmq
import numpy as np
import time
# from rf_classifier import RFClassifier
from rf_classifier_proposed import RFClassifier
import os


SENSITIVITY_DB = -60.0
CLASSIFIER_WINDOW_SIZE = 4096 # 16, 32, 64, 128, 256, 512, 1024, 2048, 4096
MAIN_PATH = '/media/sf_VM_Shared/rf_classification_ml'
# METHOD = 'previous_method'
METHOD = 'proposed_method'
ML_MODEL_PATH = os.path.join(MAIN_PATH, METHOD, 'spectrum_energy_dataset_100k_samples', 'model', 'rf_features_dataset_{}.csv_model.pickle'.format(CLASSIFIER_WINDOW_SIZE))
SCALER_MODEL_PATH = os.path.join(MAIN_PATH, METHOD, 'spectrum_energy_dataset_100k_samples', 'model', 'rf_features_dataset_{}.csv_scaler.pickle'.format(CLASSIFIER_WINDOW_SIZE))
RESULT_PATH = os.path.join(MAIN_PATH, METHOD, 'spectrum_energy_dataset_100k_samples', 'report', 'stream_clf_result_wifi_stream_{}.txt'.format(CLASSIFIER_WINDOW_SIZE))

def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5000") # connect, not bind, the PUB will bind, only 1 can bind
    socket.setsockopt(zmq.SUBSCRIBE, b'') # subscribe to topic of all (needed or else it won't work)

    rf_clf = RFClassifier(SENSITIVITY_DB, CLASSIFIER_WINDOW_SIZE, ML_MODEL_PATH, SCALER_MODEL_PATH)

    global detection
    detection_count = 0

    print("[ML_CLF] Start listening to incoming data...")

    while True:
        if socket.poll(10) != 0: # check if there is a message on the socket
            msg = socket.recv() # grab the message
            raw_data = np.frombuffer(msg, dtype=np.float32, count=-1)
            # print(np.shape(raw_data))

            rf_clf.push_data(raw_data)
            if rf_clf.action is None:
                continue
            
            if rf_clf.rf_detect is not None:
                detection += rf_clf.rf_detect + "\n"

            print("[ML_CLF] Detected RF source: {}. Mitigation action: {}".format(rf_clf.rf_detect, rf_clf.action))
            
            detection_count += 1
            if detection_count >= 10:
                break

        else:
            # print("[!] Server not found. Retrying...")
            time.sleep(0.1) # wait 100ms and try again

detection = ""
try:
    main()
except KeyboardInterrupt:
    pass

with open(RESULT_PATH, 'w') as f:
    f.write(detection)
    f.close()

# print("[ML_CLF] Detection result: \n")
# print(detection)