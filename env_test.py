from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env
from reg_env import reg_env

# Paths
# Desktop
dss_m_file_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\123Bus\IEEE123Master.dss"
output_file_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output"
# Laptop
#path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"
#output_path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\Output"

# DSS Solve Mode
#   "daily"       uses OpenDSS Loadshape and solves over a daily time schedule, allows for timed elements like Solar
#   "snapshot"    uses user defined Mathematical Loadshape, defined by the equation in load_func
mode = "snapshot"

# RL Parameters Setpoints
total_timesteps = 40000
learning_rate = [0.01]
gamma = [0.995]

# Train
for i in range(len(learning_rate)):
    for j in range(len(gamma)):
        
        param = dict({
            "s":total_timesteps,
            "l":learning_rate[i],
            "g":gamma[j],
            "p":'MlpPolicy', # Other Policies have not been tested
            "m":mode})
        
        env = reg_env(param, mode=param.get("m"), m_path=dss_m_file_path, o_path=output_file_path)
        model = DQN(MlpPolicy, env,gamma=param.get("g"), learning_rate=param.get("l"), buffer_size=2048, learning_starts=0, verbose=1)
        model.learn(total_timesteps=param.get("s"))

# Test