import pandas as pd
import matplotlib.pyplot as plt
#Desktop
path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output\Training Results\Parabolic Load\Output_Parabola_40k.csv"

df = pd.read_csv(path)
print(df)

TSBOARD_SMOOTHING = [0.99]

smooth = []
for ts_factor in TSBOARD_SMOOTHING:
    smooth.append(df.ewm(alpha=(1 - ts_factor)).mean())

for ptx in range(1):
    # plt.subplot(1,3,ptx+1)
    plt.plot(df["Solar"], 'r', label='_Hidden', alpha=0.1)
    plt.plot(smooth[ptx]["Solar"], 'r',label="L 0.01,G 0.99")

    # plt.title("IEEE 123 Bus Training")
    plt.grid(alpha=0.3)
    plt.xlabel('Timesteps')
    plt.ylabel('Rewards')
    plt.legend()

plt.show()