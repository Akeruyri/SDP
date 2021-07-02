from regulator import regulator
import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self, path):
        self.path = path
        dss.Basic.ClearAll()
        #DSS Simulation Variables and Setup
        dss.Text.Command('Compile "' + self.path + '"')
        dss.Text.Command("set mode=daily stepsize=5m number=1")
        #dss.Text.Command("set hour = 0")

        #Action Space Setup
        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.action_list = (len(self.reg_names) * 33) #33 actions for each regulator * num of regulators (+-16 and 0)

        #Observation Space Setup
        # 1. Setup Initial State of System, Keeps track of current tap of each regulator
        self.reg_tap_list = []
        self.reg_size = len(self.reg_names)
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) #Set Active Reg to pull tap information
            self.reg_tap_list.append(dss.RegControls.TapNumber()) #Append Tap
        
        # 2. Bus Voltages, For now we will simply import all bus voltages
        self.volt_list = dss.Circuit.AllBusVMag()
        self.volt_size = len(self.volt_list)

        #Concatenate both list
        self.obs_list = np.append(self.reg_list, self.volt_list)
        self.obs_size = self.reg_size + self.volt_size

        #DQN Parameters
        self.bufferSize = 2048
        self.Reward = 0
        self.done = False
        #self.state = np.array(self.obs_list) # No sure about this
        self.action_space = spaces.Discrete(self.action_list) #Action spaced defined as a discrete list of each tap change actions, rather than multiple actions per step for simplicity
        self.observation_space = spaces.Box(low=-16.0, shape=(self.obs_size,), dtype=np.float32) # INCOMPLETE NEEDS DISCUSSION
        
    def step(self, action):
        #Regulator tap change
        self.switch_taps(action)

        #Solve for current state
        dss.Text.Command("Solve")

        #NEEDS A FINISHED CONDITION 

        #Update state and calculate reward
        self.update_reg_state()
        self.update_volt_state()
        temp_observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        reward = self.Reward() # Get reward
        return temp_observation, reward, done, {"Info":self.reg_tap_list}

    def reset(self):
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"') # Recompile circuit after reset
        dss.Text.Command("set mode=daily stepsize=5m number=1") 
        self.update_reg_state() #Get starting state
        self.update_volt_state() 
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        self.done = False
        dss.Text.Command()
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    #Class Functions
    def update_reg_state(self): #Update Current Regulator Tap positions
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) #Set Active Regulator
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() #Update its Tap Number

    def update_volt_state(self): #Update Current Bus Voltage Magnitudes
        self.volt_list = dss.Circuit.AllBusVMag()

    def reg_from_action(self, act_num):
        reg = math.floor(act_num/33)
        return self.reg_names[reg] #Returns name of regulator

    def Reward(self, losses): #The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)
        return 1/losses 
   
    def switch_taps(self, action_num):
        dss.RegControls.Name(self.reg_from_action(action_num)) # Set active SVR
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

    