#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: WSN Test Bench Baseline CSMA/CA
# Author: Calveen Jon Elvin
# GNU Radio version: 3.10.1.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from gnuradio import analog
from gnuradio import blocks
import numpy
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import ieee_802_15_4_python
from gnuradio.fft import logpwrfft



from gnuradio import qtgui

class wsn_testbench_baseline_csma_ca(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "WSN Test Bench Baseline CSMA/CA", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("WSN Test Bench Baseline CSMA/CA")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "wsn_testbench_baseline_csma_ca")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 4e6

        ##################################################
        # Blocks
        ##################################################
        self.logpwrfft_x_0 = logpwrfft.logpwrfft_c(
            sample_rate=samp_rate,
            fft_size=1024,
            ref_scale=2,
            frame_rate=100,
            avg_alpha=1.0,
            average=False,
            shift=False)
        self.ieee_802_15_4_python_phy_frame_unpack_0 = ieee_802_15_4_python.phy_frame_unpack()
        self.ieee_802_15_4_python_phy_frame_pack_0 = ieee_802_15_4_python.phy_frame_pack()
        self.ieee_802_15_4_python_mac_frame_unpack_0 = ieee_802_15_4_python.mac_frame_unpack()
        self.ieee_802_15_4_python_mac_frame_pack_0 = ieee_802_15_4_python.mac_frame_pack()
        self.ieee_802_15_4_python_csma_ca_0 = ieee_802_15_4_python.csma_ca('/home/user/gnuradio_mod/rf_classification_ml/proposed_method/spectrum_energy_dataset_100k_samples/model/rf_features_dataset_16.csv_model.pickle', '/home/user/gnuradio_mod/rf_classification_ml/proposed_method/spectrum_energy_dataset_100k_samples/model/rf_features_dataset_16.csv_scaler.pickle', 16)
        self.ieee_802_15_4_python_chips_to_bits_mapper_1 = ieee_802_15_4_python.chips_to_bits_mapper()
        self.ieee_802_15_4_python_bits_to_chips_mapper_0 = ieee_802_15_4_python.bits_to_chips_mapper()
        self.blocks_unpacked_to_packed_xx_0 = blocks.unpacked_to_packed_bb(4, gr.GR_MSB_FIRST)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_char*1, samp_rate,True)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_char*1)
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_random_source_x_0 = blocks.vector_source_b(list(map(int, numpy.random.randint(0, 255, 1000))), True)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, 0.001, 0)
        self.analog_const_source_x_0 = analog.sig_source_c(0, analog.GR_CONST_WAVE, 0, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.ieee_802_15_4_python_csma_ca_0, 'mpduout'), (self.ieee_802_15_4_python_phy_frame_pack_0, 'mpdu_in'))
        self.msg_connect((self.ieee_802_15_4_python_mac_frame_pack_0, 'mpduout'), (self.ieee_802_15_4_python_csma_ca_0, 'mpduin'))
        self.msg_connect((self.ieee_802_15_4_python_mac_frame_unpack_0, 'cmdout'), (self.ieee_802_15_4_python_mac_frame_pack_0, 'cmdin'))
        self.msg_connect((self.ieee_802_15_4_python_phy_frame_pack_0, 'ppdu_out'), (self.ieee_802_15_4_python_bits_to_chips_mapper_0, 'ppdu_in'))
        self.msg_connect((self.ieee_802_15_4_python_phy_frame_unpack_0, 'mpdu'), (self.ieee_802_15_4_python_mac_frame_unpack_0, 'mpduin'))
        self.connect((self.analog_const_source_x_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.analog_random_source_x_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.logpwrfft_x_0, 0))
        self.connect((self.blocks_throttle_0, 0), (self.ieee_802_15_4_python_mac_frame_pack_0, 0))
        self.connect((self.blocks_unpacked_to_packed_xx_0, 0), (self.ieee_802_15_4_python_phy_frame_unpack_0, 0))
        self.connect((self.ieee_802_15_4_python_bits_to_chips_mapper_0, 0), (self.ieee_802_15_4_python_chips_to_bits_mapper_1, 0))
        self.connect((self.ieee_802_15_4_python_chips_to_bits_mapper_1, 0), (self.blocks_unpacked_to_packed_xx_0, 0))
        self.connect((self.ieee_802_15_4_python_mac_frame_unpack_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.logpwrfft_x_0, 0), (self.ieee_802_15_4_python_csma_ca_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "wsn_testbench_baseline_csma_ca")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle_0.set_sample_rate(self.samp_rate)
        self.logpwrfft_x_0.set_sample_rate(self.samp_rate)




def main(top_block_cls=wsn_testbench_baseline_csma_ca, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
