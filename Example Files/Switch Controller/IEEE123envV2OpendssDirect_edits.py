# This file is designed for OpenDSSDirect.py, which support Linux system. The OpenDSS does not have Linux version, so use that py to call Opendss
# https://dss-extensions.org/OpenDSSDirect.py/notebooks/Example-OpenDSSDirect.py.html
# 2/14/2021 Hongda at WSU - Trimmed for presentation by Louis Pelletier

import opendssdirect as dss 
from opendssdirect.utils import run_command
import numpy as np
import gym
from gym import spaces

# the Env class to be used for Gym-like packages
class rlEnv(gym.Env):

    # initialize training environment
    def __init__(self):

        #DSS Simulation Variables, This runs off the 123 Bus system which has 9 switches
        self.case_path = r'C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss' # r'..\cases\34Bus\ieee34Mod2.dss'
        self.dssCircuit = dss.Circuit
        self.dssElem = dss.CktElement
        self.dssBus = dss.Bus
        self.Command = run_command
        self.Command("Compile " + self.case_path)
        self.Command("set mode=daily stepsize=1h number=1")
        self.Command("set hour = 0")
        dss.Basic.ClearAll()

        self.maxStep = 24                   # 24 hours
        self.currStep = 0

        # DQN parameters
        self.bufferSize = 2048
        self.svNum = 3+9                    # Observation states number P for three phases
        self.actNum = 9                     # 1~8 switches on/off changes 0 means no switch action
        self.SWnum = np.array(range(9))     # Switch No from 0 to 8, switch 0 is for no action
        self.SWstates = np.concatenate((np.zeros(1),np.ones(6),np.zeros(2))) #Initial status, SW 1-6 NC, SW 7-8 NO
        self.SWstatesRd = np.zeros(self.actNum)
        self.done = bool(0)
        self.Reward = 0
        self.state = np.zeros(self.svNum)
        self.action_space = spaces.Discrete(self.actNum) #[0,1] if discrete(2)
        self.observation_space = spaces.Box(low=-1.0, high=20000, shape=(self.svNum, ), dtype=np.float32)
        self.brnName = "Line.L115"
        self.SwitchOpenNo = 4 # Switch number 4 is open at 1st step to isolate the fault
        self.SwitchOpen = 'SwtControl.Sw' + str(self.SwitchOpenNo)

    # get system state from OpenDSS
    def takeSample ( self ):
        self.dssCircuit.SetActiveElement(self.brnName)
        ob_powers = list(self.dssElem.Powers()[0:5:2])
        return ob_powers

    # obtain next system state using action vector
    def step(self, action):
        # action is the number of switch selected to change its state

        #First step is open the switch or switches to islolate the fault
        if self.currStep == 0:
            self.Command(self.SwitchOpen + ".Action = Open")
            self.SWstates[self.SwitchOpenNo] = 0
            done = bool(0)
        else:   # Action starts at step 2 
            # modify the case object according to action 
            if action == 0 or action == self.SwitchOpenNo:
                done = bool(0) # if action is 8, that means no action neededN()
            elif action <= 8:
                if self.SWstates[action] == 0: #action ranges from 0 to 8, and SW states only from 0~8 Status[0] does not use
                    CloseAction = 1                
                else:
                    CloseAction = 0
                k=action
                self.SWstates =self.SwitchAction(self.SWnum, CloseAction, k, self.SWstates)
                done = bool(0)
            else: # for more actions like DG and load shedding other than switches options
                done = bool(0)

        # advance and take new sample
        self.Command("Solve")

        #After solve check if any loops in feeders
        for k in self.SWnum:
            if k !=0:
                SwctrlName = "SwtControl.Sw"+str(self.SWnum[k]) 
                dss.SwtControls.Name(SwctrlName.split(".")[1])
                self.SWstatesRd[k] = dss.SwtControls.State()

        # Check for max simulation time
        if self.currStep == self.maxStep:
            done = bool(1)
        self.done = done

        #Calculate Reward
        ob = self.takeSample()
        for i in range(len(ob)):
            self.state[i]=ob[i]
        ob_tmp = np.append(ob, self.SWstatesRd)
        Reward = self.LoadsMeasure()
        self.currStep += 1
        return ob_tmp, Reward, done, {"SW Status":self.SWstates}

    # reset the environment and return initial observation
    def reset(self):
        # dss.Basic.ClearAll()
        self.currStep = 0 
        self.done = False
        # load case file
        run_command("compile " + self.case_path )

        # solve the case
        run_command("set maxcontroliter=50")
        run_command("Solve")
        self.SWstates = np.concatenate((np.zeros(1),np.ones(6),np.zeros(2)))
        
        # get initial observation
        ob0, R, done, _ = self.step(0)
        return ob0

    def close(self):
        dss.Basic.ClearAll()
        return 

#Actions list, unique to this application

    # Switch operation
    def SwitchAction(self, SWnum, CloseAction, k, SWstates):
        " CloseAction = 0               # 0 for open 1 for close"
        "k=4 # number of Switch % switch 4 for 60-160"
        
        SwctrlName = "SwtControl.Sw"+str(SWnum[k]) 
        dss.SwtControls.Name(SwctrlName.split(".")[1])
        if CloseAction==0: # Open the switch
            dss.SwtControls.Action(1)
            dss.SwtControls.Delay(0)
            #Defined in OpenDSS
            if dss.SwtControls.State() == 2: # dssActionClose = 2, Close a switch
                SWstates[k] = 0 # 0 for open status in switch states
            else: 
                print("Switch {}  does not open at step {}, switch state {} with action {} and states{}".format(str(SWnum[k]), str(self.currStep), str(dss.SwtControls.State()), str(k), str(self.SWstates)))
        else:  # Close the switch
            dss.SwtControls.Action(2) #switch action has default delay 120s so state does not change immediately
            dss.SwtControls.Delay(0)
            if dss.SwtControls.State() == 1: # dssActionOpen = 1, Open a switch
                SWstates[k] = 1 # 1 for closed status
            else: 
                 print("Switch {}  does not close at step {}, switch state {} with action {}".format(str(SWnum[k]), str(self.currStep), str(dss.SwtControls.State()), str(k)))
        return SWstates;



    # Get Power Measurement of all loads
    def LoadsMeasure(self):
        """ LoadNames: Current active loads names. Loads names may changes after shedding or connecting actions.
        LoadStates: ON/OFF of the loads after step action"""
        LoadNames = dss.Loads.AllNames()
        LoadsNum = len(LoadNames)
        LoadPQt = np.zeros((LoadsNum, 2))
        m=0
        for loadName in LoadNames:
            dss.Loads.Name(loadName)
            self.dssCircuit.SetActiveElement(loadName)
            LoadPQt[m,:] = self.dssElem.Powers()[0:2]
            m += 1
        TotalLoadPt= sum(LoadPQt[:,0])
        return TotalLoadPt