
import opendssdirect as dss
from opendssdirect.utils import run_command
import numpy as np
import math

# Setup Functions
def load_circuit_model(self, path):
    dss.run_command('compile ' + path)  # This will be done in the environment, this here just so the controller loads the model for now.
