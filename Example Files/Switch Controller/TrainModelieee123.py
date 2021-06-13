# -*- coding: utf-8 -*-
"""
Created on Fri Jan  8 15:48:24 2021
https://github.com/araffin/rl-tutorial-jnrr19/blob/sb3/4_callbacks_hyperparameter_tuning.ipynb
@author: Hongda
"""

# import gym
from IEEE123envV2OpendssDirect_edits import rlEnv  # Import the Custom Environment
from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.evaluation import evaluate_policy

import os
from stable_baselines3.common.cmd_util import make_vec_env
from stable_baselines3.common.results_plotter import load_results, ts2xy
import matplotlib.pyplot as plt

# matplotlib notebook

# Check Environment for Validity If the environment don't follow the interface, an error will be thrown
from stable_baselines3.common.env_checker import check_env

env = rlEnv()
check_env(env, warn=True)

from stable_baselines3.common.callbacks import BaseCallback
class PlottingCallback(BaseCallback):
    """
    Callback for plotting the performance in realtime.

    :param verbose: (int)
    """

    def __init__ ( self, verbose = 1 ):
        super(PlottingCallback, self).__init__(verbose)
        self._plot = None

    def _on_step ( self ) -> bool:
        # get the monitor's data
        x, y = ts2xy(load_results(log_dir), 'timesteps')
        if self._plot is None:  # make the plot
            plt.ion()
            fig = plt.figure(figsize=(6, 3))
            ax = fig.add_subplot(111)
            line, = ax.plot(x, y)
            self._plot = (line, ax, fig)
            plt.show()
        else:  # update and rescale the plot
            self._plot[0].set_data(x, y)
            self._plot[-2].relim()
            self._plot[-2].set_xlim([12000 * -0.02,
                                     12000 * 1.02])
            self._plot[-2].autoscale_view(True, True, True)
            self._plot[-1].canvas.draw()

# Create log dir
log_dir = r"C:\Users\louis\Desktop\SeniorDesignProject\Python\Switch Controller\Diagram Output"
os.makedirs(log_dir, exist_ok=True)

# Create and wrap the environment
env = make_vec_env(rlEnv, n_envs=1, monitor_dir=log_dir)

# Create Callback
plotting_callback = PlottingCallback()

# Instantiate the agent
model = DQN(MlpPolicy, env, learning_rate=0.001, buffer_size=35, learning_starts=1, target_update_interval=48, verbose=1)
# Train the agent
model.learn(total_timesteps=2000, callback=plotting_callback, log_interval=80)

# Evaluate the agent
# NOTE: If you use wrappers with your environment that modify rewards,
#       this will be reflected here. To evaluate with original rewards,
#       wrap environment in a "Monitor" wrapper before other wrappers.
mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)
print(f"mean_reward:{mean_reward:.2f} +/- {std_reward:.2f}")

# Enjoy trained agent
obs = env.reset()
for i in range(24):
    action, _states = model.predict(obs, deterministic=True)
    obs, rewards, dones, info = env.step(action)
    print('obs=', obs, 'reward=', rewards, 'done=', dones)
    # env.render()
