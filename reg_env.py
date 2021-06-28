import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self, path):
        dss.Basic.ClearAll()
        #DSS Simulation Variables and Setup
        dss.Text.Command('Compile "' + path + '"')
        dss.Text.Command("set mode=daily stepsize=1h number=1")
        dss.Text.Command("set hour = 0")

        #Import Regulators, Generate Action and State Lists
        self.regulator_list = dss.RegControls.AllNames()
        self.action_list = (len(self.regulator_list) * 33) #33 actions for each regulator * num of regulators (+-16 and 0) 

        #INCOMPLETE NEEDS WORK - THIS IS WHAT SHOULD STORE OUR REG OBJECTS
        self.state_list = 0

        #DQN Parameters
        self.bufferSize = 2048
        self.done = False
        self.action_space = spaces.Discrete(self.action_list) #Action spaced defined as a discrete list of each tap change actions, rather than multiple actions per step for simplicity
        self.observation_space = spaces.Box() # INCOMPLETE NEEDS DISCUSSION

    def step(self, action):
        
        #Get regulator to apply action too, attempt tap change
        dss.RegControls.Name(self.reg_from_action(action))  # Set active SVR
        self.switch_taps(action) # Attempt tap change

        #Solve
        dss.Text.Command("Solve")

        return temp_observation, reward, done, info

    def reset(self):
        observation = self.step(0)
        self.done = False
        dss.Text.Command()
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    #Class Specific Functions
    def reg_from_action(self, act_num):
        reg = math.floor(act_num/33)
        return self.regulator_list[reg] #Returns name of regulator

    #Other Functions
    def Reward(losses): #The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)
        return 1/losses 
   
    def switch_taps(action_num):
        tap_num = tap_from_action(action_num)
        if tap_num == 0:
            return
        else:
            dss.RegControls.TapNumber(tap_num)  # Attempt a tap change on Active Regulator
        return
    
    def losses():
        return sum(dss.Circuit.LineLosses()) #All System Line Losses, used for reward. 

    def tap_from_action(act_num):
        if act_num % 33 == 0: #If Action is "No Action"
            return 0
        elif (act_num % 33) > 0 and (act_num % 33) <= 16: #If Action is "1 to 16"
            return act_num % 33
        else: # If Action is "-1 to -16"
            return -((act_num % 33) - 16)