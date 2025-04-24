#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Calveen Jon Elvin.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

CHIPS_TO_BITS_LUT = {
    (3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2) : 0, # D9C3522E
    (3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2) : 1, # ED9C3522
    (0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1, 0, 2) : 2, # 2ED9C352
    (0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3, 1, 1) : 3, # 22ED9C35
    (1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0, 0, 3) : 4, # 522ED9C3
    (0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1, 3, 0) : 5, # 3522ED9C
    (3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1, 2, 1) : 6, # C3522ED9
    (2, 1, 3, 0, 0, 3, 1, 1, 0, 2, 0, 2, 3, 2, 3, 1) : 7, # 9C3522ED
    (2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3) : 8, # 8C96077B
    (2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3) : 9, # B8C96077
    (1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 1, 3) : 10, # 7B8C9607
    (1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0) : 11, # 77B8C960
    (0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1, 1, 2) : 12, # 077B8C96
    (1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0, 2, 1) : 13, # 6077B8C9
    (2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0, 3, 0) : 14, # 96077B8C
    (3, 0, 2, 1, 1, 2, 0, 0, 1, 3, 1, 3, 2, 3, 2, 0) : 15 # C96077B8
}

# CHIPS_TO_BITS_LUT = {
#     (217, 195, 82, 46) : 0, # D9C3522E
#     (237, 156, 53, 34) : 1, # ED9C3522
#     (46, 217, 195, 82) : 2, # 2ED9C352
#     (34, 237, 156, 53) : 3, # 22ED9C35
#     (82, 46, 217, 195) : 4, # 522ED9C3
#     (53, 34, 237, 156) : 5, # 3522ED9C
#     (195, 82, 46, 217) : 6, # C3522ED9
#     (156, 53, 34, 237) : 7, # 9C3522ED
#     (140, 150, 7, 123) : 8, # 8C96077B
#     (184, 201, 140, 119) : 9, # B8C96077
#     (123, 140, 150, 7) : 10,  # 7B8C9607
#     (119, 184, 201, 140) : 11,  # 77B8C960
#     (7, 123, 140, 150) : 12,  # 077B8C96
#     (140, 119, 184, 201) : 13,  # 6077B8C9
#     (150, 7, 123, 140) : 14,  # 96077B8C
#     (201, 140, 119, 184) : 15 # C96077B8
# }

class chips_to_bits_mapper(gr.basic_block):
    """
    docstring for block chips_to_bits_mapper
    """
    def __init__(self):
        gr.basic_block.__init__(self,
            name="chips_to_bits_mapper",
            in_sig=[np.uint8],
            out_sig=[np.uint8])
        
        # self.buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # self.buffer = [0, 0, 0, 0]
        self.buffer = []


    def forecast(self, noutput_items, ninputs):
        ninput_items_required = [noutput_items]
        return ninput_items_required


    def general_work(self, input_items, output_items):
        ninput_items = len(input_items[0])
        noutput_items = min(len(output_items[0]), ninput_items)

        # print("CTB inputs: {}".format(input_items[0][:30]))
        # print("CTB input size: {}".format(ninput_items))
        # print("CTB inputs: {}".format(input_items[0]))
        
        buff = []
        for i in range(noutput_items):
            self.load_data_buffer(input_items[0][i])
            res = CHIPS_TO_BITS_LUT.get(tuple(self.buffer))

            if res is not None:
                buff.append(res)
                self.reset_data_buffer()
                
        output_items[0][:len(buff)] = np.array(buff, dtype=np.uint8)
        
        # print("CTB output size: {}".format(len(buff)))
        # print("CTB outputs: {}".format(output_items[0][:30]))
        # print("CTB outputs: {}".format(buff))
        
        self.consume_each(noutput_items)
        return len(buff)
    

    def load_data_buffer(self, data:float) -> None:
        if len(self.buffer) < 16:
            self.buffer.append(data)
        else:
            self.buffer.pop(0)
            self.buffer.append(data)
    

    def reset_data_buffer(self) -> None:
        # self.buffer = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.buffer.clear()