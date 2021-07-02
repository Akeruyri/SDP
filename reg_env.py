from regulator import regulator
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
        dss.Text.Command("set mode=daily stepsize=5m number=1")
        #dss.Text.Command("set hour = 0")

        #Action Space Setup
        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.regulator_size = len(self.reg_names)
        self.action_list = (len(self.reg_names) * 33) #33 actions for each regulator * num of regulators (+-16 and 0)

        #Observation Space Setup
        # 1. Setup Initial State of System, Keeps track of current tap of each regulator
        self.reg_list = [] #Store current regulator list
        for reg in range(self.regulator_size):
            dss.RegControls.Name(self.reg_names[reg]) #Set Active Reg to pull tap information
            self.reg_list.append(regulator(self.reg_names[reg],dss.RegControls.TapNumber())) #Append Name and Tap
        
        # 2. Node Voltages
        self.volt_list = [] #Store list of



        #DQN Parameters
        self.bufferSize = 2048
        self.Reward = 0
        self.done = False
        self.action_space = spaces.Discrete(self.action_list) #Action spaced defined as a discrete list of each tap change actions, rather than multiple actions per step for simplicity
        self.observation_space = spaces.Box(low=-16.0, shape=(), dtype=np.float32) # INCOMPLETE NEEDS DISCUSSION
        

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

    #Class Functions
    def get_reg_state(self): #Update Current Regulator Tap positions
        for reg in range(self.regulator_size):
            dss.RegControls.Name(self.reg_list[reg].reg_name) #Set Active Regulator
            self.reg_list[reg].reg_tap_num = dss.RegControls.TapNumber() #Get its Tap Number
    
    def reg_from_action(self, act_num):
        reg = math.floor(act_num/33)
        return self.reg_names[reg] #Returns name of regulator

    def Reward(self, losses): #The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)
        return 1/losses 
   
    def switch_taps(self, action_num):
        tap_num = self.tap_from_action(action_num)
        if tap_num == 0:
            return
        else:
            dss.RegControls.TapNumber(tap_num)  # Attempt a tap change on Active Regulator
        return
    
    def losses(self): #Return SUM of all losses in the system
        #Find Magnitude, use Numpy SUM

        return dss.Circuit.LineLosses() #All System Line Losses, used for reward.

    def tap_from_action(self, act_num):
        if act_num % 33 == 0: #If Action is "No Action"
            return 0
        elif (act_num % 33) > 0 and (act_num % 33) <= 16: #If Action is "1 to 16"
            return act_num % 33
        else: # If Action is "-1 to -16"
            return -((act_num % 33) - 16)

    