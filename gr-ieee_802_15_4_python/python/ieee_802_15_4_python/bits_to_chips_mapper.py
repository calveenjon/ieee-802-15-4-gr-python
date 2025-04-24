#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Calveen Jon Elvin.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
import pmt

BITS_TO_CHIPS_LUT = {
    0 : (3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2), # D9C3522E
    1 : (3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2), # ED9C3522
    2 : (0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2), # 2ED9C352
    3 : (0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1), # 22ED9C35
    4 : (1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3), # 522ED9C3
    5 : (0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0), # 3522ED9C
    6 : (3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1), # C3522ED9
    7 : (2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1), # 9C3522ED
    8 : (2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3), # 8C96077B
    9 : (2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3), # B8C96077
    10 : (1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3), # 7B8C9607
    11 : (1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0), # 77B8C960
    12 : (0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2), # 077B8C96
    13 : (1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1), # 6077B8C9
    14 : (2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0), # 96077B8C
    15 : (3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0) # C96077B8
}

# BITS_TO_CHIPS_LUT = {
#     0 : (217, 195, 82, 46), # D9C3522E
#     1 : (237, 156, 53, 34), # ED9C3522
#     2 : (46, 217, 195, 82), # 2ED9C352
#     3 : (34, 237, 156, 53), # 22ED9C35
#     4 : (82, 46, 217, 195), # 522ED9C3
#     5 : (53, 34, 237, 156), # 3522ED9C
#     6 : (195, 82, 46, 217), # C3522ED9
#     7 : (156, 53, 34, 237), # 9C3522ED
#     8 : (140, 150, 7, 123), # 8C96077B
#     9 : (184, 201, 140, 119), # B8C96077
#     10 : (123, 140, 150, 7),  # 7B8C9607
#     11 : (119, 184, 201, 140),  # 77B8C960
#     12 : (7, 123, 140, 150),  # 077B8C96
#     13 : (140, 119, 184, 201),  # 6077B8C9
#     14 : (150, 7, 123, 140),  # 96077B8C
#     15 : (201, 140, 119, 184) # C96077B8
# }

class bits_to_chips_mapper(gr.basic_block):
    """
    docstring for block bits_to_chips_mapper
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="bits_to_chips_mapper",
            in_sig=[],
            out_sig=[np.uint8,])
        
        self.message_port_register_in(pmt.intern('ppdu_in'))
        self.message_port_register_out(pmt.intern('tx_mux'))
        self.set_msg_handler(pmt.intern('ppdu_in'), self.handle_ppdu_in)

        self.ppdu_buffer = []
        self.ppdu_buffer_len = 0
    

    def general_work(self, input_items, output_items):
        if self.ppdu_buffer_len == 0:
            # print("[BTC] No data avail!")
            # noutput_items = len(output_items[0])
            # output_items[0][:noutput_items] = np.zeros((noutput_items), dtype=np.uint8).flatten()
            # return noutput_items
            self.change_tx_chan_mux(1)
            return 0
        
        # print("[BTC] Output size: {}".format(noutput_items))
        # print("[BTC] Buffer size: {}".format(self.ppdu_buffer_len))
        self.change_tx_chan_mux(0)
        buff = []
        for i in range(self.ppdu_buffer_len):
            data = self.ppdu_buffer[i]
            data_1 = (data & 0xf0) >> 4
            data_2 = (data & 0x0f) >> 0
            buff.append(BITS_TO_CHIPS_LUT[data_1])
            buff.append(BITS_TO_CHIPS_LUT[data_2])
            # print("[BTC] data_1: {}, data_2: {}".format(data_1, data_2))
        
        self.ppdu_buffer = []
        self.ppdu_buffer_len = 0
        # print("[BTC] Buffer: {}".format(buff[:30]))
        
        data = np.array(buff, dtype=np.uint8).flatten()
        noutput_items = len(data)
        # print("[BTC] Output size: {}".format(noutput_items))
        
        output_items[0][:noutput_items] = data
        return noutput_items


    def handle_ppdu_in(self, msg):
        self.ppdu_buffer = pmt.to_python(msg)[1]
        self.ppdu_buffer_len = len(self.ppdu_buffer)
        # print("[BTC] Input data size: {}".format(self.ppdu_buffer_len))
        # print("[BTC] Input data: {}".format(self.ppdu_buffer[:30]))


    def change_tx_chan_mux(self, chan=0):
        self.message_port_pub(
            pmt.intern('tx_mux'),
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt({'chan': chan}))
        )
