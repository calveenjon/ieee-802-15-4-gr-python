#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Calveen Jon Elvin.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#
#   MAC frame structures definition as below:
#    -----------------------------------------------------------------------------------------------------------------
#   | Frame type | Padding Bits | Destination Address | Source Address | Data                    | FCS (CRC Checksum) |
#   | (2 bits)   | (6 bits)     | (16 bits)           | (16 bits)      | (varying, max 944 bits) | (16 bits)          |
#    -----------------------------------------------------------------------------------------------------------------
#   
#   Frame type definitions:
#       1) Data frame: 0x1
#       2) ACK frame: 0x2
#
#   MAC state definitions:
#       1) Idle: 0x0
#       2) Receiving ACK: 0x1


import numpy as np
from gnuradio import gr
import pmt
import time

class mac_frame_pack(gr.basic_block):
    """
    docstring for block mac_frame_pack
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="mac_frame_pack",
            in_sig=[np.uint8],
            out_sig=[])

        self.message_port_register_in(pmt.intern('cmdin'))
        self.message_port_register_out(pmt.intern('mpduout'))
        self.set_msg_handler(pmt.intern('cmdin'), self.handle_cmd_in)

        self.state = 0
        self.prev_time = time.time()
        self.timeout_threshold = 3.0
        
        self.buffer = []
        self.buff_max_len = 118
        self.device_addr = [0, 255]
        self.dest_addr = [255, 0]


    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required


    def general_work(self, input_items, output_items):
        ninput_items = len(input_items[0])
        total_item = 0

        # Return if current state is not idle
        if self.state != 0:
            self.consume_each(ninput_items)
            return 0

        for i in range(ninput_items):
            self.load_data(input_items[0][i])
            total_item += 1

            if self.buffer_full():
                break

        self.send_data_frame()
        self.buffer = []
        self.state = 1 # Receiving ACK
        self.prev_time = time.time()
        # print("Receiving ACK frame state")
        
        self.consume_each(total_item)
        return 0
    

    def load_data(self, data):
        self.buffer.append(data)
    

    def buffer_full(self) -> bool:
        if len(self.buffer) == self.buff_max_len:
            return True
        else:
            return False
    

    def send_data_frame(self):
        frame_type = [1]
        mpdu_frame = np.concatenate([
            np.array(frame_type, dtype=np.uint8),
            np.array(self.dest_addr, dtype=np.uint8),
            np.array(self.device_addr, dtype=np.uint8),
            np.array(self.buffer, dtype=np.uint8)
        ], dtype=np.uint8)
        
        # print("[MPDU_PACK] Frame size: {}".format(len(mpdu_frame)))

        self.message_port_pub(
            pmt.intern('mpduout'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt(mpdu_frame))
        )
    

    def handle_mpdu_in(self, msg):
        mpdu_frame = pmt.to_python(msg)[1]

        # Check if MPDU frame type is ACK
        if mpdu_frame[0] == 2:
            self.state = 0


    def handle_cmd_in(self, msg):
        cmd:dict = pmt.to_python(msg)[1]
        _cmd = cmd.get('mac_command', None)

        if _cmd is None:
            return
        
        # Frame sent
        if _cmd == 2:
            self.state = 0
            # print("MPDU frame sent!")