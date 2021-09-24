import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self):
        ### DSS Simulation Variables and Setup ###
        self.path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"

        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"')
        dss.Text.Command("set mode=daily stepsize=5m number=1")
        dss.Text.Command("set hour = 0")
        dss.Text.Command("Solve")

        ### Action Space Setup ###

        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.action_list = 1 + (len(self.reg_names) * 33) #1 No Action + 33 actions for each regulator * num of regulators (+-16 and 0)

        print(self.reg_names, " : ", len(self.reg_names))

        ### Observation Space Setup ###
        # Setup Initial State of System, Keeps track of current tap of each regulator
        self.reg_tap_list = []
        self.reg_size = len(self.reg_names)
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Reg to pull tap information
            self.reg_tap_list.append(dss.RegControls.TapNumber()) # Append Tap
        
        # Bus Voltages. For now we will simply import all bus voltages in per unit
        self.volt_list = dss.Circuit.AllBusMagPu()
        self.volt_size = len(self.volt_list)

        # Concatenate both list
        self.obs_list = np.append(self.reg_tap_list, self.volt_list) # Observe current sate of regulators and system voltages
        self.obs_size = self.reg_size + self.volt_size

        ### RL Parameters ###
        self.cur_step = 0
        self.max_steps = 100
        self.bufferSize = 2048
        self.Reward = 0
        self.done = False
        self.state = np.array(self.obs_list) # No sure about this (Starting State?)
        self.action_space = spaces.Discrete(self.action_list) # Action space defined as a discrete list of each tap change actions, 1 Action per step for now
        self.observation_space = spaces.Box(low=-16.0, high=16, shape=(self.obs_size,), dtype=np.float32) # INCOMPLETE NEEDS DISCUSSION

        ### Tracking Vars ###
        self.tracked_avg_reward = 0
        self.tracked_total_steps = 0
        self.output_file = open(r"C:\Users\louis\PycharmProjects\SDP\Example Files\Output\Output.csv",'w+')

    def step(self, action):
        #Tracked
        self.tracked_total_steps += 1

        # Regulator tap change
        done = False
        if (action > 0 or action < self.action_list): #If we have an action, switch taps. No Action (action = 0) do nothing.
            self.switch_taps(action)

        # Solve for current state
        dss.Text.Command("Solve")

        # Update state and calculate reward
        self.update_reg_state()
        self.update_volt_state()
        temp_observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        reward = self.get_reward() # Get reward

        #Run 100 Steps
        if (self.cur_step == self.max_steps):
            done = True
            self.cur_step = 0
            if (self.tracked_total_steps != 0):
                print("Average Reward : ", self.tracked_avg_reward / self.tracked_total_steps)
        else:
            self.cur_step += 1

        self.tracked_avg_reward += reward
        self.output_state(reward)
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

    ### Other Class Functions ###

    def update_reg_state(self): # Update Current Regulator Tap positions
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() # Update its Tap Number

    def update_volt_state(self): # Update Current Bus Voltage Magnitudes
        self.volt_list = dss.Circuit.AllBusMagPu()

    def get_reward(self):
        # The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)

        # We need to get the node voltages at each target note of our regulators
        volt_reward = 0
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            dss.ActiveClass.Name(dss.RegControls.MonitoredBus()) # Set Active Bus based on Active Regulator's Monitored Bus <- This step may be wrong
            voltages = dss.Bus.PuVoltage() # List of pu Voltages at Bus. This should be 3 normally, but I'm not sure
            reward = np.zeros(len(voltages)) # List of equal length to store the reward for this regulator's monitored bus.
            for i in range(len(voltages)):
                reward[i] = self.reward_curve(voltages[i])
            reward_reg = sum(reward)/len(reward) # Average out the rewards for this regulator's monitored bus
            volt_reward += reward_reg # Add to total reward, reward from specific regulators could be weighted more than others, for instance the large one at the main sub

        # Our reward should also minimize loss, so additional reward is added for that
        loss_reward = 1 / np.sum(dss.Circuit.LineLosses()) # For this the system losses are inverted then summed.

        # Each chunk of reward can be weighted. For just these initial tests we will focus on minimizing loss (voltage reward = 0).
        volt_reward_weight = 100
        loss_reward_weight = 0
        total_reward = (volt_reward*volt_reward_weight) + (loss_reward*loss_reward_weight)
        return total_reward

    def reward_curve(self, voltage_pu):
        # https://www.desmos.com/calculator/7umau0phxf
        # Link to Function Graph.
        k = 12   # Amplitude
        a = 12 # Left Skew
        b = -1*a # Right Skew
        x0 = 1      # Shift
        y0 = 10  # Vertical Offset
        return ((4*k)/((1+math.exp(-a*(voltage_pu-x0)))*(1+math.exp(b*(voltage_pu-x0))))) - y0

    def reg_from_action ( self, action_num ):
        return self.reg_names[math.floor((action_num - 1) / 33)]  # Returns name of regulator

    def tap_from_action ( self, action_num ):
        return ((action_num - 1) % 33) - 16 #Returns a tap position

    def switch_taps(self, action_num):
        dss.RegControls.Name(self.reg_from_action(action_num)) # Set active SVR
        tap_num = self.tap_from_action(action_num)
        if tap_num == 0:
            return
        else:
            dss.RegControls.TapNumber(tap_num)  # Attempt a tap change on Active Regulator
        return

    def output_state(self, reward):
        line = "Step," + str(self.cur_step) + ',Tap,'
        for reg in self.reg_tap_list:
            line += str(reg) + ','
        line += 'Volt (pu),'
        for volt in self.volt_list:
            line += str(volt) + ','
        line += '\n'
        self.output_file.write(line)

    def close_output_file(self):
        self.output_file.close()


