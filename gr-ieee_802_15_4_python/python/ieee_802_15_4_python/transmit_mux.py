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

class transmit_mux(gr.basic_block):
    """
    docstring for block transmit_mux
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="transmit_mux",
            in_sig=[np.complex64, np.complex64],
            out_sig=[np.complex64])

        self.message_port_register_in(pmt.intern('tx_cmd'))
        self.set_msg_handler(pmt.intern('tx_cmd'), self.handle_tx_cmd)
        
        self.chan_num = 0

    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required


    def general_work(self, input_items, output_items):
        # For this sample code, the general block is made to behave like a sync block
        # ninput_items = min([len(items) for items in input_items])
        # noutput_items = min(len(output_items[0]), ninput_items)
        # output_items[0][:noutput_items] = input_items[0][:noutput_items]

        # ninput_items = len(input_items[self.chan_num])
        # noutput_items = min(len(output_items[0]), ninput_items)
        # output_items[0][:noutput_items] = input_items[self.chan_num][:noutput_items]
        # print("[TX_CMD] Input item size: {}".format(ninput_items))
        # print("[TX_CMD] Selected channel: {}".format(self.chan_num))

        # self.consume_each(noutput_items)
        # return noutput_items

        in0_len = len(input_items[0])
        if in0_len != 0:
            noutput_items = min(len(output_items[0]), in0_len)
            output_items[0][:noutput_items] = input_items[0][:noutput_items]
            # print("[TX_CMD] Input 0 item size: {}".format(in0_len))
            
            self.consume_each(noutput_items)
            return noutput_items

        ninput_items = len(input_items[1])
        # print("[TX_CMD] Input 1 item size: {}".format(ninput_items))
        noutput_items = min(len(output_items[0]), ninput_items)
        output_items[0][:noutput_items] = input_items[1][:noutput_items]
        
        self.consume_each(noutput_items)
        return noutput_items
    

    def handle_tx_cmd(self, msg):
        data = pmt.to_python(msg)[1]
        # print("[TX_CMD] Received message data: {}".format(data))
        self.chan_num = data['chan']
        
