from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env

from reg_env import reg_env
import numpy as np
import math
import gym

env = reg_env()

model = DQN(MlpPolicy, env, learning_rate=0.01, buffer_size=2048, learning_starts=0, target_update_interval=48, verbose=1)

model.learn(total_timesteps=2400, log_interval=100)

env.close_output_file()