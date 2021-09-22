import stable_baselines3
import opendssdirect as dss
from stable_baselines3 import DQN
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env

from reg_env import reg_env
import numpy as np
import math
import gym

env = reg_env()

#check_env(env, warn=True)

model = DQN(MlpPolicy, env, learning_rate=0.01, buffer_size=2048, learning_starts=1, target_update_interval=48, verbose=1)

model.learn(total_timesteps=2000, log_interval=80)