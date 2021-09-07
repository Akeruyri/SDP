import stable_baselines3
import opendssdirect as dss
from reg_env import reg_env
import numpy as np
import math
import gym

###Louis Path
path = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss"
###David Path
env = reg_env(path)

print(env.get_reward())