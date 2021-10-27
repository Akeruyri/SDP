from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env

from reg_env import reg_env
import ray
from ray import tune

reg_env = reg_env()

model = DQN(MlpPolicy, reg_env, learning_rate=0.01, buffer_size=2048, learning_starts=0, target_update_interval=48, verbose=1)

model.learn(total_timesteps=40000)

#ray.init(ignore_reinit_error=True)

#config = {"env":reg_env,
#          "num_workers":2,
#          "vf_share_layers": tune.grid_search([True,False]),
#          "lr": tune.grid_search([1e-4,1e-5,1e-5])}

#results = tune.run('DQN',stop={'timesteps_total':10000},config=config)

reg_env.close_output_file()
