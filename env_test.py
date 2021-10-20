from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env

from reg_env import reg_env
import numpy as np
import math
import gym

###Louis Path
#path = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss"
###David Path
#path = r"D:\Program Files\OpenDSS\IEEETestCases\123Bus\IEEE123Master.dss"
#env = reg_env(path)

###Should be new path
env = reg_env()

#check_env(env, warn=True)

model = DQN(MlpPolicy, env, learning_rate=0.01, buffer_size=2048, learning_starts=1, target_update_interval=48, verbose=1)

model.learn(total_timesteps=2000, log_interval=10)