import stable_baselines3
import opendssdirect as dss
from reg_env import reg_env
import numpy as np
import math
import gym

path = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\123BusSW\IEEE123MasterSW.dss"
dss.run_command('Compile "' + path + '"')
dss.run_command("set mode=daily stepsize=1h number=1")
dss.run_command("set hour = 0")


env = reg_env()

print(env.tap_from_action(167))