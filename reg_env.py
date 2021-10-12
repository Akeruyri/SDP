import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self):

        ### DSS Simulation Variables and Setup ###
        #self.path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\123Bus\IEEE123Master.dss"
        #self.output_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output\Output.csv"

        self.path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"
        self.output_path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\Output\Output.csv"

        #DSS Loadshape
        self.cur_point = 0
        self.max_points = 24

        #Solve initial state
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"')
        dss.Text.Command("set mode=snapshot")
        dss.Text.Command("Solve")
        #dss.Text.Command("Batchedit Load..* daily=default") #Select Default Loadshape

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

        self.tracked_total_reward = 0
        self.tracked_total_steps = 1
        self.output_file = open(self.output_path,'w+')
        self.output_state(12345) #Initial State

    ### Gym Functions ###

    def step(self, action):
        # Regulator tap change
        if (action > 0 or action < self.action_list): #If we have an action, switch taps. No Action (action = 0) do nothing.
            self.switch_taps(action)

        # Solve for current state
        self.solve_cur_load(self.load_mult(self.cur_point))

        # Update state
        self.update_reg_state()
        self.update_volt_state()

        # Calculate reward
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        reward = self.get_reward() # Get reward

        # Run 100 Steps at current load, then increment to run at next load multiplier
        done = False
        self.cur_step += 1
        if (self.cur_step == self.max_steps):
            print("Average Reward :", self.tracked_total_reward / self.tracked_total_steps,"- Summed Reward :", self.tracked_total_reward, "- Current Step:", self.cur_step,"- Current Pt:", self.cur_point, "- Current Load:", self.load_mult(self.cur_point), "- Total Steps :", self.tracked_total_steps)
            self.cur_step = 0 # Reset Solve Steps
            # Adjust loadshape point every # max_steps
            if (self.cur_point == self.max_points):
                done = True
            else:
                self.cur_point += 1 # Increment Measurement Point

        # Tracked Vars#
        self.tracked_total_steps += 1
        self.tracked_total_reward += reward
        self.output_state(reward)

        return observation, reward, done, {"Info":self.reg_tap_list}

    def reset(self):
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"') # Recompile circuit after reset
        dss.Text.Command("set mode=daily stepsize=5m number=1")
        self.cur_hour = 0
        self.cur_step = 0
        self.update_reg_state() # Get starting state
        self.update_volt_state() 
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        self.done = False
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    ### Other Class Functions ###

    # Action Functions
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

    # Solve Command
    def solve_cur_load(self, load_mult):
        dss.Solution.LoadMult(load_mult) #Set current non-fixed Load Multiplier.
        dss.Text.Command("Solve")

    # Loadshape Functions
    def load_mult(self, index):
        if (index > self.max_points):
            return 0
        return self.load_func(float(index)/self.max_points)
    def load_func(self, x): #Simple Ramp function from 0 to 1 over x range 0 to 1
        A1 = 1
        A2 = 0
        return A1*x+A2

    # Update Functions
    def update_reg_state(self): # Update Current Regulator Tap positions
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() # Update its Tap Number
    def update_volt_state(self): # Update Current Bus Voltage Magnitudes
        self.volt_list = dss.Circuit.AllBusMagPu()

    # Reward Functions
    def get_reward(self):
        # The less system loss, the higher the reward. This may need to be a stored sum over the course of an episode (multiple steps)
        volt_reward_weight = 0
        volt_violation_penalty = -100
        loss_reward_weight = 10
        #tap_change_penalty = -10 # Work on this later

        # We need to get the node voltages at each target note of our regulators
        volt_reward = 0
        if (volt_reward_weight != 0):
            for reg in range(self.reg_size):
                dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
                dss.ActiveClass.Name(dss.RegControls.MonitoredBus()) # Set Active Bus based on Active Regulator's Monitored Bus <- This step may be wrong
                voltages = dss.Bus.PuVoltage() # List of pu Voltages at Bus. This should be 3 normally, but I'm not sure
                reward = np.zeros(len(voltages)) # List of equal length to store the reward for this regulator's monitored bus.
                for i in range(len(voltages)):
                    if (voltages[i] > 1.05 or voltages[i] < 0.95): #If Voltage is outside 5% limits, give large penalty
                        reward[i] = volt_violation_penalty
                    else: #Else use the voltage reward curve
                        reward[i] = self.reward_curve(voltages[i])
                reward_reg = sum(reward)/len(reward) # Average out the rewards for this regulator's monitored bus
                volt_reward += reward_reg # Add to total reward, reward from specific regulators could be weighted more than others, for instance the large one at the main sub

        # Our reward should also minimize loss, so additional reward is added for that
        loss_reward = 0
        if (loss_reward_weight != 0):
            loss_reward = -1 * np.sum(dss.Circuit.LineLosses()) # For this the system losses are inverted then summed.

        # Each chunk of reward can be weighted. For just these initial tests we will focus on minimizing loss (voltage reward = 0).
        total_reward = (volt_reward*volt_reward_weight) + (loss_reward*loss_reward_weight)
        return total_reward
    def reward_curve(self, voltage_pu):
        # https://www.desmos.com/calculator/7umau0phxf
        # Link to Function Graph.
        A = 10
        return -1000*A*(voltage_pu-0.95)(voltage_pu-1.05)

    # Output Functions
    def output_state(self, reward):
        line = "Step," + str(self.cur_step) + ",Point," + str(self.cur_point) + ",Load_Mult," + str(self.load_mult(self.cur_point)) + ",Reward," + str(reward) + ',Tap,'
        for reg in self.reg_tap_list:
            line += str(reg) + ','
        line += 'Volt (pu),'
        for volt in self.volt_list:
            line += str(volt) + ','
        line += '\n'
        self.output_file.write(line)
    def close_output_file(self):
        self.output_file.close()