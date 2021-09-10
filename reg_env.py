import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self, path):
        ### DSS Simulation Variables and Setup ###
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + path + '"')
        dss.Text.Command("set mode=daily stepsize=5m number=1")
        dss.Text.Command("set hour = 0")
        dss.Text.Command("Solve")

        ### Action Space Setup ###

        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.action_list = (len(self.reg_names) * 33) #33 actions for each regulator * num of regulators (+-16 and 0)

        ### Observation Space Setup ###
        # Setup Initial State of System, Keeps track of current tap of each regulator
        self.reg_tap_list = []
        self.reg_size = len(self.reg_names)
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Reg to pull tap information
            self.reg_tap_list.append(dss.RegControls.TapNumber()) # Append Tap
        
        # Bus Voltages. For now we will simply import all bus voltages
        self.volt_list = dss.Circuit.AllBusVMag()
        self.volt_size = len(self.volt_list)

        # Concatenate both list
        self.obs_list = np.append(self.reg_tap_list, self.volt_list) # Observe current sate of regulators and system voltages
        self.obs_size = self.reg_size + self.volt_size

        ### DQN Parameters ###
        self.bufferSize = 2048
        self.Reward = 0
        self.done = False
        self.state = np.array(self.obs_list) # No sure about this (Starting State?)
        self.action_space = spaces.Discrete(self.action_list) # Action space defined as a discrete list of each tap change actions, 1 Action per step for now
        self.observation_space = spaces.Box(low=-16.0, high=100000, shape=(self.obs_size,), dtype=np.float32) # INCOMPLETE NEEDS DISCUSSION
        
    def step(self, action):
        # Regulator tap change
        self.switch_taps(action)

        # Solve for current state
        dss.Text.Command("Solve")

        # NEEDS A FINISHED CONDITION

        # Update state and calculate reward
        self.update_reg_state()
        self.update_volt_state()
        temp_observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        reward = self.get_reward() # Get reward
        done = False
        return temp_observation, reward, done, {"Info":self.reg_tap_list}

    def reset(self):
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"') # Recompile circuit after reset
        dss.Text.Command("set mode=daily stepsize=5m number=1") 
        self.update_reg_state() # Get starting state
        self.update_volt_state() 
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        self.done = False
        dss.Text.Command()
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    # Other Class Functions
    def update_reg_state(self): # Update Current Regulator Tap positions
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() # Update its Tap Number

    def update_volt_state(self): # Update Current Bus Voltage Magnitudes
        self.volt_list = dss.Circuit.AllBusVMag()

    def reg_from_action(self, act_num):
        reg = math.floor(act_num/33)
        return self.reg_names[reg] # Returns name of regulator

    def get_reward(self):
        # The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)

        # To properly define reward we need to make a measurement of our target metric, being that all regulators need
        # to ensure their target nodes are within 5% of the nominal voltage in the system, and that the losses in a system are minimized.

        # We need to get the node voltages at each target note of our regulators
        volt_reward = 0
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            dss.ActiveClass.Name(dss.RegControls.MonitoredBus()) # Set Active Bus based on Active Regulator's Monitored Bus <- This step may be wrong
            voltages = dss.Bus.PuVoltage() # List of pu Voltages at Bus. This should be 3 normally, but I'm not sure
            reward = np.zeros(len(voltages)) # List of equal length to store the reward for this regulator's monitored bus.
            for i in range(len(voltages)):
                reward[i] = self.reward_curve(voltages[i])
            reward_reg = sum(reward)/len(reward) # average out the rewards for this regulator's monitored bus
            volt_reward += reward_reg # Add to total reward, reward from specific regulators could be weighted more than others, for instance the large one at the main sub

        # Our reward should also minimize loss, so additional reward is added for that
        loss_reward = sum(1 / self.losses()) # For this the system losses are inverted then summed.

        # Each chunk of reward can be weighted. For just these initial tests we will focus on minimizing loss (voltage reward = 0).
        volt_reward_weight = 0
        loss_reward_weight = 1
        total_reward = (volt_reward*volt_reward_weight) + (loss_reward*loss_reward_weight)

        return total_reward

    def losses(self): # Return SUM of all losses in the system
        print(dss.Circuit.LineLosses())
        return dss.Circuit.LineLosses() #All System Line Losses, used for reward.

    def reward_curve(self, voltage_pu):
        # https://www.desmos.com/calculator/7umau0phxf
        # Link to Function Graph.
        k = 2   # Amplitude
        a = 100 # Left Skew
        b = 100 # Right Skew
        x0 = 1  # Shift
        y0 = 0  # Offset
        return ((4*k)/((1+math.exp(-a*(voltage_pu-x0)))*(1+math.exp(b*(voltage_pu-x0))))) - y0

    def switch_taps(self, action_num):
        dss.RegControls.Name(self.reg_from_action(action_num)) # Set active SVR
        tap_num = self.tap_from_action(action_num)
        if tap_num == 0:
            return
        else:
            dss.RegControls.TapNumber(tap_num)  # Attempt a tap change on Active Regulator
        return

    def tap_from_action(self, act_num):
        if act_num % 33 == 0: #If Action is "No Action"
            return 0
        elif (act_num % 33) > 0 and (act_num % 33) <= 16: #If Action is "1 to 16"
            return act_num % 33
        else: # If Action is "-1 to -16"
            return -((act_num % 33) - 16)

    