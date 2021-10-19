import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self):

        ### DSS Simulation Variables and Setup ###
        #Desktop
        self.path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\123Bus\IEEE123Master.dss"
        self.output_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output\Output.csv"

        #Laptop
        #self.path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"
        #self.output_path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\Output\Output.csv"

        #DSS Loadshape
        self.cur_point = 1
        self.max_points = 24

        #Solve initial state
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"')
        dss.Text.Command("set mode=snapshot")
        dss.Text.Command("batchedit regcontrol..* enabled=false")  # Disable regulator control, taps are set manually
        dss.Text.Command("Solve")
        dss.Solution.LoadMult(self.load_mult(self.cur_point)) #Set Initial Load Multiplier

        ### Action Space Setup ###

        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.action_list = 1 + (len(self.reg_names) * 33) #1 No Action + 33 actions for each regulator * num of regulators (+-16 and 0)
        print(self.reg_names, " : ", len(self.reg_names))

        ### Observation Space Setup ###
        # Setup Initial State of System, Keeps track of current tap of each regulator
        self.reg_tap_list = []
        self.reg_tap_list_prev = []
        self.reg_size = len(self.reg_names)
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Reg to pull tap information
            self.reg_tap_list.append(dss.RegControls.TapNumber()) # Append Tap
            self.reg_tap_list_prev.append(0)
        
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
        self.observation_space = spaces.Box(low=-16.0, high=16, shape=(self.obs_size,), dtype=np.float32)

        ### Tracking Vars ###
        self.tap_change_violation_count = 0
        self.voltage_violation_count = 0
        self.tracked_total_reward = 0
        self.tracked_total_steps = 0
        self.output_file = open(self.output_path,'w+')
        self.output_state(0.1, -1) #Initial State

    ### Gym Functions ###

    def step(self, actions):
        # Set for reward function comparison
        for reg in range(self.reg_size):
            self.reg_tap_list_prev[reg]= self.reg_tap_list[reg]

        # Regulator tap change
        if (actions > 0 or actions < self.action_list): #If we have an action, switch taps. No Action (action = 0) do nothing.
            self.switch_taps(actions)

        # Solve for current state
        self.solve()

        # Update state
        self.update_reg_state()
        self.update_volt_state()

        # Calculate reward
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        reward = self.step_reward() # Get reward of current step

        # Run 100 Steps at current load, then increment to run at next load multiplier
        done = False
        if (self.cur_step == self.max_steps):
            self.tracked_total_steps += 100
            print("Average Reward :", self.tracked_total_reward / (self.tracked_total_steps+1), "- Current Step:",
                  self.cur_step, "- Current Pt:", self.cur_point, "- Current Load:", self.load_mult(self.cur_point),
                  "- Total Steps :", self.tracked_total_steps)
            self.cur_step = 1  # Reset Solve Steps
            # Adjust loadshape point every # max_steps
            if (self.cur_point == self.max_points):
                done = True
            else:
                self.cur_point += 1  # Increment Load Mult Point
                dss.Solution.LoadMult(self.load_mult(self.cur_point)) # Update Load Multiplier
        else:
            self.cur_step += 1

        # Tracked Vars#
        self.tracked_total_reward += reward
        self.output_state(reward, actions)
        self.tap_change_violation_count = 0  # Reset out Violation Counts
        self.voltage_violation_count = 0
        return observation, reward, done, {"Info":self.reg_tap_list}

    def reset(self):
        dss.Basic.ClearAll()
        dss.Text.Command('Compile "' + self.path + '"') # Recompile circuit after reset
        dss.Text.Command("set mode=snapshot")
        dss.Text.Command("batchedit regcontrol..* enabled=false")
        self.update_reg_state() # Get starting state
        self.update_volt_state()
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        dss.Solution.LoadMult(self.load_mult(self.cur_point))  # Update Load Multiplier
        self.done = False
        return observation

    def close(self):
        dss.Basic.ClearAll()
        return

    ### Other Class Functions ###

    # Action Functions
    def reg_from_action (self, action_num):
        return self.reg_names[math.floor((action_num - 1) / 33)]  # Returns name of regulator
    def tap_from_action (self, action_num):
        return ((action_num - 1) % 33) - 16 #Returns a tap position
    def pu_from_tap(self, tap):
        return np.interp(tap, [-16,16], [0.9,1.1])
    def switch_taps(self, action_num):
        dss.RegControls.Name(self.reg_from_action(action_num)) # Set active SVR
        dss.Transformers.Name(dss.RegControls.Transformer()) # Set active Transformer controlled by the Regulator
        tap = self.tap_from_action(action_num)
        if tap == 0:
            return
        else:
            dss.Transformers.Tap(self.pu_from_tap(tap))  # Change tap on the Active Transformer
        return

    # Solve Command
    def solve(self):
        dss.Text.Command("Solve")

    # Loadshape Functions
    def load_mult(self, index):
        if (index > self.max_points):
            return 0
        return self.load_func(float(index)/self.max_points)
    def load_func(self, x): #Simple Ramp function from 0 to 1 over x range 0 to 1, can be redefined to test various loadshapes
        A1 = 1
        A2 = 0
        return A1*x+A2

    # State Update Functions
    def update_reg_state(self): # Update Current Regulator Tap positions
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() # Update its Tap Number
    def update_volt_state(self): # Update Current Bus Voltage Magnitudes
        self.volt_list = dss.Circuit.AllBusMagPu()

    # Step Reward Functions
    def step_reward(self):
        # Rewards can be weighted or disabled (weight = 0)
        volt_reward_weight = 10
        loss_reward_weight = 10
        tap_reward_weight = 10

        # Rewards can be negative (penalties)
        volt_violation_penalty = -100
        tap_change_penalty = -10

        # A penalty (negative reward) should be applied for changing tap positions greater than 1.
        tap_reward = 0
        if (tap_reward_weight != 0):
            for i in range(len(self.reg_tap_list)):
                tap_distance = abs(self.reg_tap_list_prev[i] - self.reg_tap_list[i])
                if (tap_distance > 1): # If a tap was moved more than 1 position from the previous step (ex: tap -10 to -3), give penalty
                    tap_reward += tap_change_penalty * tap_distance # the larger this jump the more negative the reward.
                    self.tap_change_violation_count += 1 # Track # of tap violations -> This will usually just be 1, but when we get MultiDiscrete working this can be higher

        # The reward should be based on our voltage criteria, that being keep levels within 5% of nominal
        volt_reward = 0
        if (volt_reward_weight != 0):
            voltage = self.volt_list # Evaluate Voltages at all Buses
            reward = np.zeros(len(voltage)) # Store a reward for each
            for i in range(len(voltage)):
                if (voltage[i] > 1.05 or voltage[i] < 0.95): # If Voltage is outside 5% limits, give large penalty
                    reward[i] = volt_violation_penalty
                    self.voltage_violation_count += 1
                else: # Else use the voltage reward curve, the closer to 1.0 the better, for now a simple parabola
                    reward[i] = -10000*(voltage[i]-0.95)*(voltage[i]-1.05)
            volt_reward = sum(reward) # Add to total reward, reward from specific regulators could be weighted more than others, for instance the large one at the main sub

        # The reward should minimize line losses in our system
        loss_reward = 0
        if (loss_reward_weight != 0):
            loss_reward = -1 * np.sum(dss.Circuit.LineLosses()) # For this the system losses are inverted then summed.

        total_reward = (tap_reward*tap_reward_weight) + (volt_reward*volt_reward_weight) + (loss_reward*loss_reward_weight)
        return total_reward

    # Output File Functions
    def output_state(self, reward, action):
        if (reward == 0.1):
            line = "Step,Point,Load_Mult,Tap Violations,Voltage Violations,Reg Changed,Tap Changed,Reward,Regulator States,"
            for reg in self.reg_names:
                line += reg + ','
            line += 'Volt (pu),'
            for i in range(len(dss.Circuit.AllNodeNames())):
                line += dss.Circuit.AllNodeNames()[i] + ','
            line += '\n'
        else:
            line = str(self.cur_step) + "," + str(self.cur_point) + "," + str(dss.Solution.LoadMult())
            line += "," + str(self.tap_change_violation_count) + "," + str(self.voltage_violation_count)
            line += "," + self.reg_from_action(action) + "," + str(self.tap_from_action(action))
            line += "," + str(reward) + ',,'
            for reg in self.reg_tap_list:
                line += str(reg) + ','
            line += ','
            for volt in self.volt_list:
                line += str(volt) + ','
            line += '\n'
        self.output_file.write(line)
    def close_output_file(self):
        self.output_file.close()