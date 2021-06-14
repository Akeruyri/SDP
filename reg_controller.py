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
import numpy as np
import math

class reg_controller():

    # This controller needs to have a function that takes in the name of the RegControl Object in order to
    # perform tap changes on it.
    # This can be modeled after the SwitchAction function from the Switching
    # THis needs to work without reference to a specific name of anything in the model

    def __init__(self, name):
        self.reg_name = name

        # When starting up, the controller needs access to information from the circuit
        dss.LoadShape.First()  # Sets first loadshape as active loadshape
        self.total_timesteps = dss.LoadShape.Npts()  # A tap change may occur on each loadshape interval

        self.tap_scale = dss.LoadShape.HrInterval()  # Returns the interval between each loadshape points in hrs
        self.total_time = self.tap_scale * self.total_timesteps  # Length of the loadshape in hours
        self.tap_list = np.zeros((self.total_timesteps,),dtype=int)  # Store a 2D array that will hold all of our tap changes for each SVR

        #Create Tap List from Loadshape
        self.loadshape_to_tap() # Populate the tap_list and other values

        #Loss information
        self.system_losses = np.zeros((self.total_timesteps,), dtype=complex)
        self.line_losses = np.zeros((self.total_timesteps,), dtype=complex)
        self.transformer_losses = np.zeros((self.total_timesteps,), dtype=complex)

    #This method is a simple implementation.
    def loadshape_to_tap(self): #Simple way, a more advanced method can be developed later
        self.tap_scale = dss.LoadShape.HrInterval()  # Returns the interval between each loadshape points in hrs
        self.total_time = self.tap_scale * self.total_timesteps  # Length of the loadshape in hours
        mult_unscaled = dss.LoadShape.PMult() #pull list of multipliers
        multipliers = np.interp(mult_unscaled, (min(mult_unscaled),max(mult_unscaled)),(-16,16)) #Range them to the taps.
        for each in range(multipliers.size):
            multipliers[each] = math.trunc(multipliers[each])  # Truncate the tap values
            self.tap_list[each] = multipliers[each] # Assign the taps. All SVRs will run off the same tap for now.

    def switch_taps(self, timestep):
        dss.RegControls.Name(self.reg_name) #Set active SVR
        dss.RegControls.TapNumber(self.tap_list[timestep]) #Attempt a tap change.
    
    def get_losses(self, timestep):
        self.system_losses[timestep] = dss.Circuit.Losses()[0] + dss.Circuit.Losses()[1] * 1j
        self.line_losses[timestep] = dss.Circuit.LineLosses()[0] + dss.Circuit.LineLosses()[1] * 1j
        self.transformer_losses[timestep] = (dss.Circuit.Losses()[0] - dss.Circuit.LineLosses()[0]) + ((dss.Circuit.Losses()[1] * 1j) - (dss.Circuit.LineLosses()[1] * 1j))