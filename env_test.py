from stable_baselines3 import DQN
from stable_baselines3.dqn import MlpPolicy
from reg_env import reg_env

# Paths
dss_file = r"repository\Example Files\123Bus\IEEE123Master.dss"
output_path = r"repository\Example Files\Output"

# RL Parameter Setpoints
total_timesteps = 400000
learning_rate = [0.01]
gamma = [0.99]

test_env = True

for i in range(len(learning_rate)):
    for j in range(len(gamma)):
        p = dict({
            "l":learning_rate[i],
            "g":gamma[j],
            "p":'MlpPolicy',
            "m":"snapshot",
            "s":total_timesteps
        })
        def format_params(s):
            x = s.strip("{}")
            x = x.replace(":", "_")
            x = x.replace(",", "_")
            x = x.replace("'", "")
            x = x.replace(" ", "")
            return x
        p_str = format_params(str(p))

        # Train Agent
        env = reg_env(p_str, mode=p.get("m"), m_file=dss_file, out=output_path)
        model = DQN(MlpPolicy, env,gamma=p.get("g"), learning_rate=p.get("l"), buffer_size=2048,learning_starts=0, verbose=1)

        print("Train")
        model.learn(total_timesteps=total_timesteps)

        # Test Agent
        if test_env:
            print("Test")
            env.set_mode("daily")
            obs = env.reset() # Reset model to use daily
            for i in range(1440): # Run through a daily load flow
                action, _states = model.predict(obs, deterministic=True)
                obs, penalty, done, info = env.step(action)
                if i % 10 == 0:
                    env.output_step_term()