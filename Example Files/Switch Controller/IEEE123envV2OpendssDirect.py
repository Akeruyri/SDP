
#This file is designed for OpenDSSDirect.py, which support Linux system. The OpenDSS does not have Linux version, so use that py to call Opendss
# https://dss-extensions.org/OpenDSSDirect.py/notebooks/Example-OpenDSSDirect.py.html
# 2/14/2021 Hongda at WSU

import opendssdirect as dss 
from opendssdirect.utils import run_command
# import win32com.client
import numpy as np
# from tensorflow import keras
# from numpy_ringbuffer import RingBuffer 
# from numpy_ringbuffer import RingBuffer
# import rl
# import pickle, os
# from rl.core import Env
# from rl.memory import SequentialMemory
# from rl.policy import BoltzmannQPolicy
# from rl.agents.dqn import DQNAgent
# from keras.models import Sequential
# from keras.layers import Dense, Activation, Flatten
# from keras.optimizers import Adam
import gym
from gym import spaces

# DSSObj = win32com.client.Dispatch("OpenDSSEngine.DSS")
# DSSStart = DSSObj.Start("0")
# if DSSStart:
#     print("OpenDSS Engine started successfully")
# else:
#     print("Unable to start the OpenDSS Engine")

# the Env class to be used for Gym-like packages
class rlEnv(gym.Env):
    # initialize training environment
    def __init__(self):
        self.case_path = r'C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss' # r'..\cases\34Bus\ieee34Mod2.dss'
        # initialize OpenDSS
        # self.dssObj = win32com.client.Dispatch("OpenDSSEngine.DSS")
        # self.dssText = self.dssObj.Text
        self.dssCircuit = dss.Circuit
        # self.dssSolution = self.dssCircuit.Solution
        self.dssElem = dss.CktElement
        self.dssBus = dss.Bus
        self.Command = run_command
        self.Command("Compile " + self.case_path)
        self.Command("set mode=daily stepsize=1h number=1")
        self.Command("set hour = 0")
        # self.LoadNames = self.dssCircuit.Loads.AllNames
        self.maxStep = 24                  # 24 hours
        self.currStep = 0
        # self.counter = np.zeros((1,1))
        # self.randFault = 0
        # self.bus_list = 0
        # self.bus_3p_list = 0
        # reset DSS memory
        dss.Basic.ClearAll()
        # DQN parameters
        self.bufferSize = 2048
        self.svNum = 3+9                # Observation states number P for three phases
        self.actNum = 9                 # 1~8 switches on/off changes 0 means no switch action
        self.SWnum = np.array(range(9)) # Switch No from 0 to 8, switch 0 is for no action
        self.SWstates = np.concatenate((np.zeros(1),np.ones(6),np.zeros(2))) #Initial status
        self.SWstatesRd = np.zeros(self.actNum)
        self.done = bool(0)
        self.Reward = 0
        self.state = np.zeros(self.svNum)#RingBuffer(capacity=self.svNum-1, dtype=np.float64)
        # for i in range(self.svNum-1):
        #     self.state.append(0)
        self.action_space = spaces.Discrete(self.actNum) #[0,1] if discrete(2)
        self.observation_space = spaces.Box(low=-1.0, high=20000, shape=(self.svNum, ), dtype=np.float32)
        self.brnName = "Line.L115"
        self.SwitchOpenNo = 4 # Switch number 4 is open at 1st step to isolate the fault
        self.SwitchOpen = 'SwtControl.Sw' + str(self.SwitchOpenNo)
        
        # self.run_command = self.SwitchOpen + ".Action = Open"
        # self.run_command = self.SwitchOpen +".Lock = Yes"
        
        


    # model of the DQN l3=Action Number
    # def q_net(self, l1=128, l2=256, l3=128):
    #     # your dqn model
    #     model = Sequential()
    #     #Input layer
    #     model.add(Flatten(input_shape=(1,) + self.observation_space.shape))
    #     #Hidden layers
    #     model.add(Dense(l1))
    #     model.add(Activation('relu'))
    #     model.add(Dense(l2))
    #     model.add(Activation('relu'))
    #     model.add(Dense(l3))
    #     model.add(Activation('relu'))
    #     #Output layer
    #     model.add(Dense(self.actNum))
    #     model.add(Activation('linear'))
    #     print(model.summary())
      
        
    #     return model
      
    # get system state from OpenDSS
    def takeSample(self):
        # voltage
        # self.dssCircuit.SetActiveBus(self.busName)
        # ob_volt = list(self.dssCircuit.ActiveBus.Voltages)
        # current Power
        
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
            # self.run_command = "set mode=daily stepsize=1h number=1"
            done = bool(0)
            # # Read switches states
       
            # for k in self.SWnum:
            #     if k !=0:
            #         SwctrlName = "SwtControl.Sw"+str(self.SWnum[k]) 
            #         dss.SwtControls.Name(SwctrlName.split(".")[1])
            #         self.SWstatesRd[k] = dss.SwtControls.State()
        else:   # Action starts at step 2 
            # modify the case object according to action 
            if action == 0 or action == self.SwitchOpenNo:
                done = bool(0) # if action is 8, that means no action neededN()
            elif action <= 8:
                # self.dssCircuit.SetActiveElement(self.brnName)
                # self.dssCircuit.ActiveCktElement.Open
                if self.SWstates[action] == 0: #action ranges from 0 to 8, and SW states only from 0~8 Status[0] does not use
                    CloseAction = 1                
                else:
                    CloseAction = 0
                k=action
                self.SWstates =self.SwitchAction(self.SWnum, CloseAction, k, self.SWstates)
                done = bool(0)
                # # Read switches states
       
                # for k in self.SWnum:
                #     if k !=0:
                #         SwctrlName = "SwtControl.Sw"+str(self.SWnum[k]) 
                #         self.dssCircuit.SwtControls.Name = SwctrlName.split(".")[1]
                #         self.SWstatesRd[k] =self.dssCircuit.SwtControls.State
            else: # for more actions like DG and load shading other than switches options
                done = bool(0)
          
         # advance and take new sample
        
        self.Command("Solve")
        #After solve check if any loops in feeders
        # DSSTopology = self.dssCircuit.Topology
        # numLoops = DSSTopology.NumLoops        
        # if numLoops == 0:
        
        # Read switches states
        for k in self.SWnum:
            if k !=0:
                SwctrlName = "SwtControl.Sw"+str(self.SWnum[k]) 
                dss.SwtControls.Name(SwctrlName.split(".")[1])
                self.SWstatesRd[k] =dss.SwtControls.State()
        # check for max simulation time
        if self.currStep == self.maxStep:
            done = bool(1)
        self.done = done
        # print('Current Step =', self.currStep)   
        # print('action',action, 'obs=', obs, 'reward=', reward, 'done=', done, '\n', 'info=', info)
        # if self.currStep == 1:
        #     self.run_command = self.SwitchOpen +".Lock = Yes"
        ob = self.takeSample()
        for i in range(len(ob)):
            self.state[i]=ob[i]
        # for val in ob:
        #     self.state.append(val)
        # ob_tmp = np.array(self.state).reshape(1,self.svNum-1)
        ob_tmp = np.append(ob, self.SWstatesRd)
        Reward = self.LoadsMeasure()
        # print('action',action, 'obs=',  ob_tmp , 'reward=', Reward, 'done=', done, '\n')
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
        
        # set measurement bus to recloser location
        # self.dssCircuit.SetActiveBus(self.busName)
        
        # get initial observation
        ob0, R, done, _ = self.step(0)
        # ob = ob0.astype(int)
        return ob0

    

    # def render(self, mode):

    #     return


    def close(self):
        dss.Basic.ClearAll()
        return 
        
#Actions list
    # Switch operation
    def SwitchAction(self, SWnum, CloseAction, k, SWstates):
        " CloseAction = 0               # 0 for open 1 for close"
        "k=4 # number of Switch % switch 4 for 60-160"
        
        SwctrlName = "SwtControl.Sw"+str(SWnum[k]) 
        dss.SwtControls.Name(SwctrlName.split(".")[1])
        if CloseAction==0:
        # Open the switch
            # self.Command(SwctrlName + ".Action = Open")
            dss.SwtControls.Action(1)
            dss.SwtControls.Delay(0)
            #Defined in OpenDSS
            #dssActionNone = 0, No action
            # dssActionOpen = 1, Open a switch
            # dssActionClose = 2, Close a switch
            if dss.SwtControls.State() == 2: # dssActionClose = 2, Close a switch
                SWstates[k] = 0 # 0 for open status in switch states
            else: 
                print("Switch {}  does not open at step {}, switch state {} with action {} and states{}".format(str(SWnum[k]), str(self.currStep), str(dss.SwtControls.State()), str(k), str(self.SWstates)))
        else:
        # Close the switch
            dss.SwtControls.Action(2) #switch action has default delay 120s so state does not change immediately
            dss.SwtControls.Delay(0)
            if dss.SwtControls.State() == 1: # dssActionOpen = 1, Open a switch
                SWstates[k]= 1 # 1 for closed status
            else: 
                 print("Switch {}  does not close at step {}, switch state {} with action {}".format(str(SWnum[k]), str(self.currStep), str(dss.SwtControls.State()), str(k)))
        return SWstates;
         
    
  
       
    # def SwitchAction(self, SWnum, CloseAction, k, SWstates):
    #    " CloseAction = 0               # 0 for open 1 for close"
    #    "k=4 # number of Switch % switch 4 for 60-160"
    #    switchName = "Line.Sw"+str(SWnum[k]) 
    #    self.dssCircuit.Lines.Name = switchName.split(".")[1]
    #    if CloseAction==0:
    #     # Open the switch
    #         oldBusName = self.dssCircuit.Lines.Bus2
    #         self.dssCircuit.Lines.Bus2 = "__opened__" + oldBusName
    #         SWstates[k]=0; # 0 for open status
    #    else:
    #     # Close the switch
    #         oldBusName = self.dssCircuit.Lines.Bus2
    #         self.dssCircuit.Lines.Bus2 = oldBusName[oldBusName.index("__opened__") + 10:]
    #         SWstates[k]=1; # 0 for open status
    #    return SWstates;
   
    # Add VF reference bus for MG island    
    def AddVSDGs(self, VSDGBus): #REMOVE
        """Add Vsourece DG in islanded area for V F reference"""
        run_command("New Vsource.DG1 Bus1="+ str(VSDGBus) + " BasekV=4.16 BaseMVA=0.098 Pu=1.0 angle=0") #Add DG refrence bus at 67

    def RemoveVSDG(self): #REMOVE
        run_command("Vsource.DG1.enabled=no")
    
    #Add normal DGs in distribution feeder as initialization
    def AddNormalDGs(self, DGBuslist): #REMOVE
        """Add DGs in islaned area as PQ sources when initial time"""
        for BusNo in DGBuslist:
            run_command("New Generator.G" + str(BusNo) + " phases=3 bus1="+str(BusNo)+ " kW=100 kV=4.16 PF=0.98 conn=wye model=1") #Three phases generator
    
    #Enable or Disable DGs according to DG status
    def EnableDisableDGs(self, DGBuslist, DGstatus): #REMOVE
          for DGi in range(len(DGBuslist)):
             if DGstatus[DGi] == 0:
                 self.dssCircuit.SetActiveElement('Generator.G'+ str(DGBuslist[DGi]))
                 self.dssElem.Enabled(0) 
             else: 
                self.dssCircuit.SetActiveElement('Generator.G'+str(DGBuslist[DGi]))
                self.dssElem.Enabled(1) 
                
    #Measure all DG outputs            
    def MeasureAllDGs(self, DGBuslist): #REMOVE
        """Three phases generators"""
        DGN=len(DGBuslist)
        DGsP=np.zeros(DGN)
        k=0
        for DGs in DGBuslist:
            genName = 'Generator.'+'G'+ str(DGs)
            self.dss.Generators.Name( genName.split(".")[1])
            # self.dssCircuit.Generators.Name = 'G'+ str(DGs)
            DGsP[k] = self.dss.Generators.kW()
            # DSSCktelement = DSSCircuit.SetActiveElement('Generator.G'+ str(DGs))
            # DGsP[k]=DSSCktelement.Properties("kW").Val
            k=k+1
        return DGsP
    
    #Shed or connect loads referring to Load status
    def ShedConnectLoad(self, LoadStates): #REMOVE
        """Shed loads or connect loads based on load states from RL decision"""
        ShedLoadIndex = np.where(LoadStates == 0)[0]
        ConnectLoadIndex=np.where(LoadStates == 1)[0]
        #Define load enable or disable function 
        if len(ShedLoadIndex)!=0:
            for SDI in range(len(ShedLoadIndex)):
                self.run_command("Load."+self.LoadNames[ShedLoadIndex[SDI]]+".enabled=false")
        if len(ConnectLoadIndex)!=0:
            for CLI in range(len(ConnectLoadIndex)):
                self.run_command("Load."+self.LoadNames[ConnectLoadIndex[CLI]]+".enabled=true")
                
    def LoadsMeasure(self):
        """ LoadNames: Current actiave loads names. Loads names may changes after sheding or connecting actions.
        LoadStates: ON/OFF of the loads after step action"""
        LoadNames = dss.Loads.AllNames()
        LoadsNum = len(LoadNames)
        LoadPQt = np.zeros((LoadsNum, 2))
        m=0
        for loadName in LoadNames:
            # loadName = "Load.s24c" #s68a
            dss.Loads.Name(loadName)
            self.dssCircuit.SetActiveElement(loadName)
            LoadPQt[m,:] = self.dssElem.Powers()[0:2]
            m += 1
        TotalLoadPt= sum(LoadPQt[:,0])
        return TotalLoadPt   
    

# from stable_baselines3.common.env_checker import check_env
# env = rlEnv()
# If the environment don't follow the interface, an error will be thrown
# check_env(env, warn=True)

# # # Test the environment
env = rlEnv()
obs = env.reset() # Should include reset at beginning for test, otherwise, there is an error about 'new circuit' from OpenDSS
# # # # # # env.render()

# # # # # print(env.observation_space)
# # # # # print(env.action_space)
# # # # # print(env.action_space.sample())

action = 7
# Hardcoded best agent: always go left!
n_steps = 24
for step in range(n_steps):
  print("Step {}".format(step ))
  if step == 1:
      action = 7
      obs, reward, done, info = env.step(action)
  elif step == 2:
      action = 7
      obs, reward, done, info = env.step(action)
  elif step ==3:
      action = 7
      obs, reward, done, info = env.step(action)
  elif step ==4:
      action = 7
      obs, reward, done, info = env.step(action)
  elif step ==7:
      action = 7
      obs, reward, done, info = env.step(action)
  else:
      action = 0
      obs, reward, done, info = env.step(0)
  print('action',action, 'obs=', obs, 'reward=', reward, 'done=', done, '\n', 'info=', info)
  # env.render()
  if done:
    print("Goal reached!", "reward=", reward)
    break