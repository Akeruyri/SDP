# This file is designed for OpenDSSDirect.py, which support Linux system. OpenDSS does not support Linux, thus
# use the Direct.py package to call OpenDSS
# https://dss-extensions.org/OpenDSSDirect.py/notebooks/Example-OpenDSSDirect.py.html
# 6/4/2021 WSU Senior Design Team Aquarius

# This file sets up the parameters and methods to control a SVR RegControl Object implementation in OpenDSS
# Information on this Object is found on page 200 in the included OpenDSS Instruction.

# Relevant Documentation
# https://dss-extensions.org/OpenDSSDirect.py/index.html


# Control individual device -> evaluate -> control individual device -> evaluate .. ect. until all devices have operated then loop back
# Control all devices -> evaluate then loop back

# Should reg devices be controlled individually or in cases where they are banked control all three,
# or even from the RL evaluation should it control all regulators in the system per step

import opendssdirect as dss
from opendssdirect.utils import run_command
import numpy as np

class svr_controller():

    # This controller needs to have a function that takes in the name of the RegControl Object in order to
    # perform tap changes on it.
    # This can be modeled after the SwitchAction function from the Switching
    # THis needs to work without reference to a specific name of anything in the model import


    #Constructor Method
    def __init__(self):
        # When starting up, the controller needs access to information from the circuit
        self.circuit = dss.Circuit
        self.svr_list = dss.RegControls.AllNames() #List of all the step voltage regulators.

        self.svr_curr = ""
        self.total_svrs = len(self.svr_list)

    def import_model(self):
        #Test test test
        #Pull Request test

    def new_function(self):
        #Added to the New Function