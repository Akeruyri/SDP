import pandas as pd
import matplotlib.pyplot as plt

path = r"repository\Example Files\Output\.{CSV NAME}"

df = pd.read_csv(path)
print(df)

TSBOARD_SMOOTHING = [0.99]

smooth = []
for ts_factor in TSBOARD_SMOOTHING:
    smooth.append(df.ewm(alpha=(1 - ts_factor)).mean())

for ptx in range(1):
    # plt.subplot(1,3,ptx+1)
    plt.plot(df["Reward"], 'b', label='_Hidden', alpha=0.1)
    plt.plot(smooth[ptx]["Reward"], 'b',label="Parabolic 400k")

    plt.grid(alpha=0.3)
    plt.xlabel('Timesteps')
    plt.ylabel('Rewards')
    plt.legend()

plt.show()

