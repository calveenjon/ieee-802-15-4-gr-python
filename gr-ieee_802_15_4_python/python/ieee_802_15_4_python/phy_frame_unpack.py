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

PREAMBLE_SIGNATURE = [0, 0, 0, 0, 167]

class phy_frame_unpack(gr.basic_block):
    """
    docstring for block phy_frame_unpack
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="phy_frame_unpack",
            in_sig=[np.uint8],
            out_sig=[])
        
        self.message_port_register_out(pmt.intern('mpdu'))

        self.state = 0
        self.preamble_buff = [0, 0, 0, 0, 0]
        self.payload_len = 0
        self.total_payload_extract = 0
        self.payload_buff = []

    
    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items] * ninputs
        return ninput_items_required


    def general_work(self, input_items, output_items):
        # ninput_items = min([len(items) for items in input_items])
        # noutput_items = min(len(output_items[0]), ninput_items)
        # output_items[0][:noutput_items] = input_items[0][:noutput_items]
        # self.consume_each(ninput_items)
        # return ninput_items

        ninput_items = len(input_items[0])
        # print("[PHY_UPACK] Total input items: {}".format(ninput_items))
        # print("[PHY_UPACK] Input data: {}".format(input_items[0][:30]))

        for i in range(ninput_items):
            # Preamble search state
            if self.state == 0:
                self.load_data(input_items[0][i])
                
                if self.preamble_found():
                    # print("[PHY_UPACK] Preamble found!")
                    # print("[PHY_UPACK] Preamble data: {}".format(self.preamble_buff))
                    self.state = 1
                    self.preamble_buff = [0, 0, 0, 0, 0]
                    # print("[PHY_UPACK] Preamble data: {}".format(self.preamble_buff))
                    continue
            
            # PHR search
            if self.state == 1:
                self.payload_len = input_items[0][i]
                # print("[PHY_UPACK] Total payload size: {}".format(self.payload_len))
                self.state = 2
                continue

            # Payload extract
            if self.state == 2:
                self.payload_buff.append(input_items[0][i])
                self.total_payload_extract += 1
                # print(self.total_payload_extract, self.payload_len)
                if self.total_payload_extract >= self.payload_len:
                    self.total_payload_extract = 0
                    self.payload_len = 0
                    self.state = 0

                    # print("[PHY_UPACK] MPDU data: {}, len: {}".format(self.payload_buff, len(self.payload_buff)))
                    self.send_mpdu()
                    self.payload_buff.clear()
                    continue
        
        self.consume_each(ninput_items)
        return 0


    def load_data(self, data:int) -> None:
        self.preamble_buff.pop(0)
        # print("[PHY_UPACK] Preamble data: {}".format(self.preamble_buff))
        self.preamble_buff.append(data)
        # print("[PHY_UPACK] Preamble data: {}".format(self.preamble_buff))


    def preamble_found(self) -> bool:
        # print("[PHY_UPACK] Preamble test result: {}".format([0, 0, 0, 0, 0] == PREAMBLE_SIGNATURE))
        return True if (self.preamble_buff == PREAMBLE_SIGNATURE) else False


    def send_mpdu(self) -> None:
        self.message_port_pub(
            pmt.intern('mpdu'), 
            pmt.cons(pmt.PMT_NIL, pmt.to_pmt(np.array(self.payload_buff, dtype=np.uint8)))
        )

