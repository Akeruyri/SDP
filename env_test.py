import stable_baselines3
import opendssdirect as dss
from reg_env import reg_env
import numpy as np
import math
import gym


path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"

env = reg_env(path)

print(env.losses())

print(env.get_reward())