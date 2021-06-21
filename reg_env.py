import opendssdirect as dss
from opendssdirect.utils import run_command
import numpy as np
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self, path):
        #
    def step( self, action):

    def reset(self):
        observation = self.step(0)
        return observation
    def close(self):
        dss.Basic.ClearAll()
        return

    def losses(self):
