from reg_controller import reg_controller
import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self):
        dss.Basic.ClearAll()
        #DSS Simulation Variables and Setup
        path = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss"
        dss.run_command('Compile "' + path + '"')
        dss.run_command("set mode=daily stepsize=1h number=1")
        dss.run_command("set hour = 0")


        #Import Regulators and generate action list
        self.regulator_list = dss.RegControls.AllNames()
        self.reg_ctrlrs = []
        for name in self.regulator_list:
            self.reg_ctrlrs.append(reg_controller(name))
        self.action_list = (len(self.regulator_list) * 33) #33 (+-16 and 0) total actions

        #Index List for actions 0 -> No Action, 1-16 -> Switch Tap to 1-16 (mapped directly), 17-33 -> Switch to Negative Taps 1-16

        #DQN Parameters
        self.bufferSize = 2048
        self.done = False

    def step( self, action):
        return

    def reset(self):
        observation = self.step(0)
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    def losses(self):
        return

    def reg_from_action(self, act_num):
        reg = math.floor(act_num/33)
        return self.regulator_list[reg]

    def tap_from_action(self, act_num):
        if act_num % 33 == 0: #If Action is "No Action"
            return 0
        elif (act_num % 33) > 0 and (act_num % 33) <= 16: #If Action is "1 to 16"
            return act_num % 33
        else: # If Action is "-1 to -16"
            return -((act_num % 33) - 16)