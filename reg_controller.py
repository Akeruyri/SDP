# This file is designed for OpenDSSDirect.py, which support Linux system. OpenDSS does not support Linux, thus
# use the Direct.py package to call OpenDSS
# https://dss-extensions.org/OpenDSSDirect.py/notebooks/Example-OpenDSSDirect.py.html
# 6/4/2021 WSU Senior Design Team Aquarius

# This file sets up the parameters and methods to control a SVR RegControl Object implementation in OpenDSS
# Information on this Object is found on page 200 in the included OpenDSS Instruction.

# Relevant Documentation
# https://dss-extensions.org/OpenDSSDirect.py/index.html

import opendssdirect as dss

class reg_controller():

    def __init__(self, name):
        self.reg_name = name

    def switch_taps ( self, action_num ):
        dss.RegControls.Name(self.reg_name)  # Set active SVR
        if action_num == 0:
            return
        else:
            dss.RegControls.TapNumber()  # Attempt a tap change.