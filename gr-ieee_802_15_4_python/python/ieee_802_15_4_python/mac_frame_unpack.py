#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Calveen Jon Elvin.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
import pmt
import time

class mac_frame_unpack(gr.basic_block):
    """
    docstring for block mac_frame_unpack
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="mac_frame_unpack",
            in_sig=[],
            out_sig=[np.uint8])

        self.message_port_register_in(pmt.intern('mpduin'))
        self.message_port_register_out(pmt.intern('cmdout'))
        self.set_msg_handler(pmt.intern('mpduin'), self.handle_mpdu_in)

        self.data_buffer = []

        self.prev_time = time.time()
        self.total_data_recv = 0

    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required
    
    
    def general_work(self, input_items, output_items):
        if len(self.data_buffer) == 0:
            return 0
        
        noutput_items = min(len(output_items[0]), len(self.data_buffer))
        # print("output items: {}".format(noutput_items))
        output_items[0][:noutput_items] = self.data_buffer[:noutput_items]
        self.data_buffer = []

        # Calculate frame rate
        self.total_data_recv += noutput_items
        curr_time = time.time()
        
        if (curr_time - self.prev_time) > 1.0:
            data_rate = (self.total_data_recv * 8) / (curr_time - self.prev_time)
            print("Total data received: {}, Network data rate: {} bps".format(self.total_data_recv, round(data_rate, 3)))
            
            self.total_data_recv = 0
            self.prev_time = time.time()

        return noutput_items


    def handle_mpdu_in(self, msg):
        mpdu = pmt.to_python(msg)[1]
        self.data_buffer = mpdu[5:]
        self.send_mac_cmd()
        # print("Frame received! Sending ACK frame")


    def send_mac_cmd(self):
        self.message_port_pub(
            pmt.intern('cmdout'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt({'mac_command': 2}))
        )
        