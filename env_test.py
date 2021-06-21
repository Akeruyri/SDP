import stable_baselines3
import opendssdirect as dss
from reg_env import reg_env
import numpy as np
import math
import gym

path = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss"

env = reg_env(path)

for each in range(200):
    print(env.tap_from_action(each))