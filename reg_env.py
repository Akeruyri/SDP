import opendssdirect as dss
import numpy as np
import math
import gym
from gym import spaces

class reg_env (gym.Env):

    def __init__(self, p, mode, m_file, out):

        ### DSS Simulation Variables and Setup ###
        self.output_type = f"Out_{p}"
        self.path = m_file
        self.output_path = fr"{out}\Out_{p}.csv"

        # DSS Solve Mode,
        # "daily" uses OpenDSS Loadshape and solves over a daily time schedule, allows for timed elements like Solar
        # "snapshot" runs off of a user defined Loadshape, defined by the equation in load_func
        self.mode = mode
        self.cur_point = 1  # Loadshape starting point for snapshot mode
        self.max_points = 10  # In Snapshot mode, the system will run for max_steps * max_points before fully reseting back to the first point

        # Solve initial state
        self.dds_reset()
        self.solve()

        ### Action Space Setup ###

        #Import Regulators and Generate Action List
        self.reg_names = dss.RegControls.AllNames()
        self.reg_size = len(self.reg_names)
        self.n_actions = 1 + (self.reg_size * 33) #1 No Action + 33 actions for each regulator * num of regulators (+-16 and 0)
        print(f"{self.mode} : {self.reg_names} : {self.reg_size} : {self.n_actions}")

        ### Observation Space Setup ###
        self.reg_tap_list = []
        self.reg_tap_list_prev = []
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
        self.max_steps = 0
        if self.mode == "snapshot":
            self.max_steps = 1000  # 1000 steps per load multiplier point
        elif self.mode == "daily":
            self.max_steps = 60 * 24  # Minutes per Day
        self.done = False
        self.state = np.array(self.obs_list) # No sure about this (Starting State?)
        self.action_space = spaces.Discrete(self.n_actions) # Action space defined as a discrete list of each tap change actions, 1 Action per step for now
        self.observation_space = spaces.Box(low=-16.0, high=16, shape=(self.obs_size,), dtype=np.float32)

        ### Tracking Vars ###
        self.tap_change_violation_count = 0
        self.voltage_violation_count = 0
        self.tracked_total_steps = 0
        self.record_voltage = False
        self.record_tap = True
        self.started = True
        self.output_file = open(self.output_path, 'w+')
        self.output_step_file(1, -1) #Initial State

    ### Gym Functions ###

    def step(self, action):
        if action > 0 or action < self.n_actions: #For Action = 0, do nothing.
            self.switch_taps(action) # Tap Change Otherwise

        self.solve()
        self.update_state() # Update Observation State

        observation = np.append(self.reg_tap_list, self.volt_list) # Create Observation
        reward = self.step_reward() # Calculate Reward

        # Evaluate Next Step
        if self.cur_step == self.max_steps:
            self.zero_taps()  # Zero the taps
            self.output_step_term()
            self.cur_step = 1  # Reset Solve Steps
            done = True
            if self.mode == "snapshot": # In snapshot mode, load multiplier is manually changed
                # Adjust loadshape point every # max_steps
                if self.cur_point == self.max_points:
                    self.cur_point = 1 # Reset Point every max_steps * max_points
                else:
                    self.cur_point += 1  # Increment Load Mult Point
                    dss.Solution.LoadMult(self.load_mult(self.cur_point)) # Update Load Multiplier
        else:
            self.cur_step += 1

        # Update Tracked Vars
        self.output_step_file(reward, action)
        self.tap_change_violation_count = 0  # Reset out Violation Counts
        self.voltage_violation_count = 0
        self.tracked_total_steps += 1
        return observation, reward, self.done, {"Info":self.reg_tap_list}
    def reset(self):
        self.dds_reset()
        self.update_state() # Get starting state
        observation = np.append(self.reg_tap_list, self.volt_list) # Create new observation state
        dss.Solution.LoadMult(self.load_mult(self.cur_point))  # Update Load Multiplier
        self.done = False
        return observation
    def close(self):
        dss.Basic.ClearAll()
        return

    ### Other Class Functions ###

    # Action Functions
    def reg_from_action(self, action_num):
        return self.reg_names[math.floor((action_num - 1) / 33)]  # Returns name of regulator
    def tap_from_action(self, action_num):
        return ((action_num - 1) % 33) - 16 #Returns a tap position
    def switch_taps(self, action_num):
        dss.RegControls.Name(self.reg_from_action(action_num)) # Set active SVR
        dss.Transformers.Name(dss.RegControls.Transformer()) # Set active Transformer controlled by the Regulator
        tap = self.tap_from_action(action_num)
        if tap == 0:
            return
        else:
            dss.Transformers.Tap(np.interp(tap, [-16,16], [0.9,1.1]))  # Change tap on the Active Transformer
        return
    def zero_taps(self):
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            dss.Transformers.Tap(1) # Set Tap to Zero (1 pu)
            self.reg_tap_list_prev[reg] = 0 # Reset prev list
        return

    # OpenDSS Solve and Reset Command
    def solve(self):
        dss.Text.Command("Solve")
    def dds_reset(self):
        dss.Basic.ClearAll()
        dss.Text.Command(fr'Compile "{self.path}"')  # Compile System Simulation
        dss.Text.Command("batchedit regcontrol..* enabled=false")  # Disable regulator control, taps are set manually
        if self.mode == "snapshot":
            dss.Text.Command("set mode=snapshot")
            dss.Solution.LoadMult(self.load_mult(self.cur_point))  # Set Initial Load Multiplier
            self.max_steps = 1000  # 1000 steps per load mult point
        elif self.mode == "daily":
            dss.Text.Command("set mode=daily stepsize=1m")  # Per Minute Daily Solve
            self.max_steps = 60 * 24  # Minutes per Day

    # Loadshape Functions
    def load_mult(self, index):
        if index > self.max_points:
            return 0
        return self.load_func(float(index)/self.max_points)
    def load_func(self, x): # User Defined External Loadshape Function
        #return x # Ramp
        return -4*(x-0.5)*(x-0.5)+1 # Parabola

    # Observation State Update
    def update_state(self): # Update Current Regulator Tap positions
        self.volt_list = dss.Circuit.AllBusMagPu()
        for reg in range(self.reg_size):
            dss.RegControls.Name(self.reg_names[reg]) # Set Active Regulator
            self.reg_tap_list_prev[reg] = self.reg_tap_list[reg] # Update Previous State
            self.reg_tap_list[reg] = dss.RegControls.TapNumber() # Update Tap Number for Current State

    # Reward Function
    def step_reward(self):
        # Rewards can be weighted or disabled (weight = 0)
        tap_penalty_weight = 0.5
        volt_penalty_weight = 10
        loss_penalty_weight = 0.5

        # A penalty (negative penalty) should be applied for changing tap positions greater than 1.
        tap_penalty = 0
        if tap_penalty_weight != 0:
            for i in range(len(self.reg_tap_list)):
                tap_distance = abs(self.reg_tap_list_prev[i] - self.reg_tap_list[i])
                if tap_distance > 1: # If a tap was moved more than 1 position from the previous step (ex: tap -10 to -3), give penalty
                    tap_penalty -= tap_distance # Track # of tap violations -> This will usually just be 1, but when we get MultiDiscrete working this can be higher

        # The penalty should be based on our voltage criteria, that being keep levels within 5% of nominal
        volt_penalty = 0
        if volt_penalty_weight != 0:
            voltage = self.volt_list # Evaluate Voltages at all Buses
            for i in range(len(voltage)):
                if voltage[i] > 1.05 or voltage[i] < 0.95: # If Voltage is outside 5% limits, give large penalty
                    volt_penalty -= 1

        # The penalty should minimize line losses in our system
        loss_penalty = 0
        if loss_penalty_weight != 0:
            loss_penalty = -1 * np.sum(dss.Circuit.LineLosses()) # The worse the line loses, the lower this penalty. This will be dissabled for now

        total_penalty = (tap_penalty*tap_penalty_weight) + (volt_penalty*volt_penalty_weight) + (loss_penalty*loss_penalty_weight)
        return total_penalty

    # Output Functions
    def output_step_term(self):
        print(f"Current Step:{self.cur_step} - Current Pt:{self.cur_point} - Current Load:{str(dss.Solution.LoadMult())} - Total Steps :{self.tracked_total_steps}")
    def output_step_file(self, reward, action):
        self.output_file = open(self.output_path,'a')
        if self.started == True:
            self.started = False
            line = f"O{self.output_type}\n"
            line += "Index,Step,Point,Load_Mult,Reg Changed,Tap Changed,Reward,Regulator States,"
            if self.mode == "daily":
                line += "Time,"
            if self.record_tap is True:
                for reg in self.reg_names:
                    line += f"{reg},"
            if self.record_voltage is True:
                line += 'Volt (pu),'
                for i in range(len(dss.Circuit.AllNodeNames())):
                    line += f"{dss.Circuit.AllNodeNames()[i]},"
            line += '\n'
        else:
            line = f"{str(self.tracked_total_steps)},{str(self.cur_step)},{str(self.cur_point)},{str(dss.Solution.LoadMult())}," \
                   f"{self.reg_from_action(action)},{str(self.tap_from_action(action))},{str(reward)},,"
            if self.mode == "daily":
                line += f"{dss.Solution.DblHour()},"
            if self.record_tap is True:
                for reg in self.reg_tap_list:
                    line += f"{str(reg)},"
            if self.record_voltage is True:
                line += ','
                for volt in self.volt_list:
                    line += f"{str(volt)},"
            line += '\n'
        self.output_file.write(line)
        self.output_file.close()