from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from stable_baselines3.common.env_checker import check_env
from reg_env import reg_env

# Paths
# Desktop
dss_file = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\123Bus\IEEE123Master.dss"
output_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output"
# Laptop
#path = r"C:\Users\louis\PycharmProjects\SDP\Example Files\123Bus\IEEE123Master.dss"
#output_path = fr"C:\Users\louis\PycharmProjects\SDP\Example Files\Output"

# RL Parameters Setpoints
total_timesteps = 40000
learning_rate = [0.01]
gamma = [0.995]
policy_name = 'MlpPolicy'

# Train
for i in range(len(learning_rate)):
    for j in range(len(gamma)):
        p = dict({
            "l":learning_rate[i],
            "g":gamma[j],
            "p":policy_name,
        })
        def format_params(s):
            x = s.strip("{}")
            x = x.replace(":", "_")
            x = x.replace(",", "_")
            x = x.replace("'", "")
            x = x.replace(" ", "")
            return x
        p_str = format_params(str(p))

        env = reg_env(p_str, dss=dss_file, out=output_path)

        model = DQN(MlpPolicy, env,gamma=p.get("g"), learning_rate=p.get("l"), buffer_size=2048,learning_starts=0, verbose=1)

        model.learn(total_timesteps=total_timesteps)

# Test