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

class phy_frame_pack(gr.basic_block):
    """
    docstring for block phy_frame_pack
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="phy_frame_pack",
            in_sig=[],
            out_sig=[])
        
        self.message_port_register_in(pmt.intern('mpdu_in'))
        self.message_port_register_out(pmt.intern('ppdu_out'))
        self.set_msg_handler(pmt.intern('mpdu_in'), self.handle_mpdu_in)

        self.mpdu_buffer = []
        self.mpdu_buffer_len = 0
        self.ppdu_buffer_leftover = []


    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items]
        return ninput_items_required


    def general_work(self, input_items, output_items):
        return 0


    def handle_mpdu_in(self, msg):
        self.mpdu_buffer = pmt.to_python(msg)[1]
        self.mpdu_buffer_len = len(self.mpdu_buffer)
        
        # print("[PHY_PACK] MPDU data size: {}".format(len(self.mpdu_buffer)))

        if len(self.mpdu_buffer) > 128:
            self.mpdu_buffer = self.mpdu_buffer[:128]
            self.mpdu_buffer_len = 128
            print("WARNING: MPDU data is larger than 128 bytes! Data beyond 128 bytes will be dropped")
        
        # Create PPDU packet
        ppdu = np.concatenate([
            np.array([0, 0, 0, 0, 167, self.mpdu_buffer_len], dtype=np.uint8), 
            self.mpdu_buffer],
        dtype=np.uint8)

        # print("[PHY_PACK] PPDU data: {}".format(ppdu[:30]))

        # Send PPDU packet
        self.send_ppdu(ppdu)
        

    def send_ppdu(self, ppdu: np.ndarray):
        self.message_port_pub(
            pmt.intern('ppdu_out'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt(ppdu))
        )
        self.mpdu_buffer = []
        self.mpdu_buffer_len = 0

