import opendssdirect as dss
import random as rand
import numpy as np

rand.seed()

# Desktop Path
path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\123Bus\IEEE123Master.dss"
output_path = r"C:\Users\louis\Desktop\SeniorDesignProject\repository\Example Files\Output\Output_Tap_Test.csv"

# Solve initial state
dss.Basic.ClearAll()
dss.Text.Command('Compile "' + path + '"')
dss.Text.Command("set mode=snapshot")
dss.Text.Command("batchedit regcontrol..* enabled=false")  # Disable regulator control, taps are set manually
dss.Text.Command("Solve")

# System Variables
reg_names = dss.RegControls.AllNames()

reg_tap_list = []
reg_size = len(reg_names)
for reg in range(reg_size):
    dss.RegControls.Name(reg_names[reg])  # Set Active Reg to pull tap information
    reg_tap_list.append(dss.RegControls.TapNumber())  # Append Tap

volt_list = dss.Circuit.AllBusMagPu()

total_test_points = 10

output_file = open(output_path,'w+')

def tap_change():
    # Choose Random Regulator
    reg = reg_names[rand.randint(0,reg_size-1)]
    dss.RegControls.Name(reg) # 0 <= reg_selected <= reg_size -1 : [0,1,2,...,reg_size-1]
    dss.Transformers.Name(dss.RegControls.Transformer()) # Select its corresponding transformer
    # Change its tap to a random tap
    tap = rand.randint(-16,16)
    dss.Transformers.Tap(np.interp(tap, [-16,16], [0.9,1.1]))
    return reg, tap

def solve ():
    dss.Text.Command("Solve")

def update_reg_state ():  # Update Current Regulator Tap positions
    for reg in range(reg_size):
        dss.RegControls.Name(reg_names[reg])  # Set Active Regulator
        reg_tap_list[reg] = dss.RegControls.TapNumber()  # Update its Tap Number

def update_volt_state(): # Update Current Bus Voltage Magnitudes
    volt_list = dss.Circuit.AllBusMagPu()

def output_state(i, reg, tap):
    if i == -1:
        line = 'Step,Reg,Tap,,'
        for r in reg_names:
            line += r + ','
        line += 'Volt (pu),'
        for i in range(len(dss.Circuit.AllNodeNames())):
            line += dss.Circuit.AllNodeNames()[i] + ','
        line += '\n'
        # Initial State
        line += 'Initial,System,State,>,'
        for t in reg_tap_list:
            line += str(t) + ','
        for volt in volt_list:
            line += str(volt) + ','
        line += '\n'
    else:
        line = str(i) + ',' + reg + ',' + str(tap) + ',>,'
        for t in reg_tap_list:
            line += str(t) + ','
        line += ','
        for volt in volt_list:
            line += str(volt) + ','
        line += '\n'
    output_file.write(line)

# Tap changing loop
output_state(-1, "initial", -1)
for i in range(total_test_points):
    reg, tap = tap_change()
    solve()
    update_reg_state()
    update_volt_state()
    output_state(i, reg, tap)

output_file.close()



