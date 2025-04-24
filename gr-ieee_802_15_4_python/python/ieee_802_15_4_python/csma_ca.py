#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Calveen Jon Elvin.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Module state definitions
# 0 - Idle
# 1 - Clear channel assessment (CCA)
# 2 - Backoff
# 3 - Interference Mitigation

import numpy as np
from gnuradio import gr
import pmt
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import random
import pickle
import time

ONE_HOT_ENCODER_LABEL = ['BL_Beacon', 'BL_Stream', 'Microwave_Oven', 'WiFi_Beacon', 'WiFi_Stream']
MITIGATION_STRATEGY = {
        'BL_Stream': 1,
        'BL_Beacon': 1,
        'Microwave_Oven': 0,
        'WiFi_Beacon': 0,
        'WiFi_Stream': 0
    }
MITIGATION_STRATEGY_PROPOSED = {
        'BL_Stream': 0,
        'BL_Beacon': 1,
        'Microwave_Oven': 0,
        'WiFi_Beacon': 0,
        'WiFi_Stream': 1
    }


class csma_ca(gr.basic_block):
    """
    docstring for block csma_ca
    """
    def __init__(self, rf_classifier_path, ml_data_scaler, window_size=16):
        gr.basic_block.__init__(self,
            name="csma_ca",
            in_sig=[(np.float32, 1024)],
            out_sig=[])
        
        self.message_port_register_in(pmt.intern('mpduin'))
        self.message_port_register_out(pmt.intern('mpduout'))
        self.message_port_register_out(pmt.intern('sdrcmd'))
        self.set_msg_handler(pmt.intern('mpduin'), self.handle_mpdu_in)

        self.state = 0 # Idle state

        self.buffer = []
        self.buff_max_len = 8
        self.mpdu_frame_buff = None
        
        self.current_channel = 0 # Current channel
        
        # ML classifier
        self.buff_max_len_ml = window_size
        # self.clf: DecisionTreeClassifier = None
        self.scaler: StandardScaler = StandardScaler()
        self.clf: DecisionTreeClassifier = DecisionTreeClassifier(random_state=400)
        self.onehot_enc = OneHotEncoder().fit(np.array(ONE_HOT_ENCODER_LABEL).reshape(-1, 1))

        self.load_model_file(rf_classifier_path, ml_data_scaler)

        # CSMA/CA parameters
        self.energy_detect_threshold_db = -60.0
        self.num_backoff_max = 14
        self.backoff_exp = 0
        self.num_backoff = 0
        self.backoff_frame = 0
        self.backoff_frame_iter = 0
        self.max_backoff = 5
        self.renew_backoff_frame = False


    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required


    def general_work(self, input_items, output_items):
        ninput_items = len(input_items[0])
        total_item = 0

        # Module in idle state
        if self.state == 0:
            self.consume_each(ninput_items)
            return 0
        
        # Module in clear channel assessment state
        if self.state == 1:
            # print("Performing CCA...")
            for i in range(ninput_items):
                self.load_data(np.max(input_items[0][i]))
                total_item += 1

                if self.buffer_full():
                    if self.channel_busy():
                        print("[CSMA_CA] Channel is busy")
                        self.update_backoff_param()
                        self.state = 2 # Enter channel backoff state
                        self.buffer.clear()
                    else:
                        # print("[CSMA_CA] Transmit message...")
                        self.send_mpdu()
                        self.state = 0 # Enter module idle
                        self.buffer.clear()
                    
                    break
            
            self.consume_each(ninput_items)
            return 0

        
        # Module transmit backoff state
        if self.state == 2:
            
            # Check if backoff state needs update
            if self.renew_backoff_frame is True:
                self.backoff_frame = random.randint(0, pow(2, self.backoff_exp) - 1)
                self.renew_backoff_frame = False
            
            # Backoff mechanism failed
            if self.num_backoff >= self.max_backoff:
                print("[CSMA_CA] Backoff failed!")
                self.state = 3
                self.consume_each(ninput_items)
                return 0
            
            # print("Enter backoff state. Module backoff by {} frames".format(self.backoff_frame))
            for i in range(ninput_items):
                self.backoff_frame_iter += 1
                
                if self.backoff_frame_iter >= self.backoff_frame:
                    # print("To CCA process...")
                    self.state = 1 # perform CCA
                    self.backoff_frame_iter = 0
                    
                    break
            
            self.consume_each(ninput_items)
            return 0
        
        
        # Module in interference mitigation state
        if self.state == 3:            
            for i in range(ninput_items):
                self.load_data(np.max(input_items[0][i]))
                
                if len(self.buffer) >= self.buff_max_len_ml:
                    print("[CSMA_CA] ML inferencing time...")
                    
                    preproc_start_time = time.time() # start program countdown
                    # preproc_data = self.ml_feature_extraction().reshape(1, -1)
                    preproc_data = self.ml_feature_extraction_proposed().reshape(1, -1)
                    preproc_end_time = time.time() # stop program countdown
                    print("[CSMA_CA] Preprocessing duration: {}s".format(preproc_end_time - preproc_start_time))
                    # print("Spectrum features: {}".format(preproc_data))
                    
                    ml_start_time = time.time() # start inference countdown
                    preproc_data = self.scaler.transform(preproc_data)
                    rf_class = self.clf.predict(preproc_data)
                    ml_stop_time = time.time() # start inference countdown
                    print("[CSMA_CA] Inferencing duration: {}s".format(ml_stop_time - ml_start_time))
                    print("RF class number: {}".format(rf_class))
                    
                    # self.do_mitigation(rf_class) # Perform previous method mitigation procedure
                    # self.do_mitigation_proposed(rf_class) # Perform proposed method mitigation procedure
                    
                    self.buffer.clear()
                    self.reset_backoff_param()
                    self.state = 2
                    
                    break
            
            self.consume_each(ninput_items)
            return 0
        
        
        return 0

    
    def load_data(self, data):
        self.buffer.append(data)
    
    
    def buffer_full(self) -> bool:
        if len(self.buffer) >= self.buff_max_len:
            return True
        else:
            return False
    
    
    def channel_busy(self) -> bool:
        if np.mean(self.buffer) > self.energy_detect_threshold_db and not (np.mean(self.buffer) == 0.0):
        # if np.mean(self.buffer) > self.energy_detect_threshold_db:
            return True
        else:
            return False


    def handle_mpdu_in(self, msg):
        # Ignore message if current state is not idle
        if self.state != 0:
            return
        
        self.mpdu_frame_buff = pmt.to_python(msg)[1]  # store mpdu temporarily

        # Perform message transmission
        self.state = 2 # backoff before perform CCA
        self.send_mpdu()


    def send_mpdu(self):
        self.message_port_pub(
            pmt.intern('mpduout'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt(self.mpdu_frame_buff))
        )
        # print("Data sent!")
    
    
    def update_backoff_param(self):
        self.backoff_exp = min(self.backoff_exp + 1, 14)
        self.num_backoff += 1
        self.renew_backoff_frame = True
    
    
    def reset_backoff_param(self):
        self.backoff_exp = 0
        self.num_backoff = 0
        self.backoff_frame = 0
        self.backoff_frame_iter = 0
    
    
    def sdr_change_channel(self):
        self.current_channel += 1
        
        if self.current_channel > 1:
            self.current_channel = 0
        
        self.message_port_pub(
            pmt.intern('sdrcmd'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt({'chan': self.current_channel}))
        )
        print('[CSMA] SDR change channel {}'.format(self.current_channel))
    
    
    def ml_feature_extraction(self) -> np.ndarray:
        x = np.zeros(self.buff_max_len_ml, dtype=np.uint8)
        
        for i in range(self.buff_max_len_ml):
            if self.buffer[i] >= self.energy_detect_threshold_db:
                x[i] = 1
            else:
                x[i] = 0
        
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
            
            cl_max = 0 # Max chan clear duration
            if len(cl_t_count) > 0: 
                cl_max = np.max(cl_t_count) 
            
            periodicity = n/(tx_max + cl_max) # Periodicity
            usage_ratio = np.sum(tx_t_count)/n # Chan usage ratio
            results = np.array([tx_max, cl_max, periodicity, usage_ratio])
        else:
            results = None
        
        return results
    

    def ml_feature_extraction_proposed(self):
        x = np.zeros(self.buff_max_len_ml, dtype=np.uint8)
        
        for i in range(self.buff_max_len_ml):
            if self.buffer[i] >= self.energy_detect_threshold_db:
                x[i] = 1
            else:
                x[i] = 0
        
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
            if len(cl_t_count) > 0: 
                cl_max = np.max(cl_t_count)
            
            usage_ratio = np.sum(tx_t_count)/n # Chan usage ratio
            results = np.array([tx_max, tx_min, cl_max, usage_ratio])
        else:
            results = None
        
        return results
    

    def do_mitigation(self, ml_output:np.ndarray) -> None:
        rf_label_idx = np.argmax(ml_output)
        rf_label = ONE_HOT_ENCODER_LABEL[rf_label_idx]
        print("[CSMA_CA] Detected inteferer signal source: {}".format(rf_label))
        
        mitigate_idx = MITIGATION_STRATEGY_PROPOSED.get(rf_label)
        if mitigate_idx == 0:
            print("[CSMA_CA] Mitigation strategy: Change Channel")
            self.sdr_change_channel()
        else:
            print("[CSMA_CA] Mitigation strategy: Retransmit packet")

        return
    

    def do_mitigation_proposed(self, ml_output:np.ndarray) -> None:
        rf_label_idx = np.argmax(ml_output)
        rf_label = ONE_HOT_ENCODER_LABEL[rf_label_idx]
        print("[CSMA_CA] Detected inteferer signal source: {}".format(rf_label))

        mitigate_idx = MITIGATION_STRATEGY_PROPOSED.get(rf_label)
        if mitigate_idx == 0:
            print("[CSMA_CA] Mitigation strategy: Change Channel")
            self.sdr_change_channel()
        else:
            print("[CSMA_CA] Mitigation strategy: Retransmit packet")

        return
    

    def load_model_file(self, ml_model_path:str, scaler_model_path:str) -> None:
        with open(scaler_model_path, 'rb') as f:
            params = pickle.load(f)
            self.scaler.mean_ = params['scaler_mean']
            self.scaler.scale_ = params['scaler_std']
            f.close()

        with open(ml_model_path, 'rb') as f:
            self.clf = pickle.load(f)
            f.close()
        
        return