import opendssdirect as dss
import numpy as np
import pandas as pd
import random

nt = 24 #hours in a day
random.seed()

#Get our DSS Object running.
dss.run_command(r'compile "C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\13Bus\MasterIEEE13.dss"')

#Preliminary Commands
dss.run_command('')

dss.run_command('batchedit load..* Vmin=0.8')
dss.run_command('batchedit load..* daily=PQmult')
dss.run_command('New EnergyMeter.Main Line.650632 1')
dss.run_command('set mode=daily stepsize=1h number=1')
dss.run_command('set hour=0')

Regulator_List = dss.RegControls.AllNames() #Get All Voltage Regulators in System

print(Regulator_List)

# Xtap_Reg = [[15,7,6,6,6,7,8,9,11,12,13,14,14,14,14,14,14,14,14,14,14,14,13,12],
#             [10,5,4,4,4,4,5,6,7,8,8,9,9,9,9,9,9,9,9,9,9,9,9,9],
#             [15,6,5,5,5,6,7,9,10,12,13,13,14,14,14,14,14,14,14,14,14,14,13,12]]

#Create a 2D array of taps for the Regulators (#Reg as row, #taps per Reg as col)
Reg_Taps = np.zeros((len(Regulator_List), nt), dtype=int)
for i in range(len(Regulator_List)):
    for j in range(nt):
        tap_val = random.randrange(-16,17,1) #Get a random int tap value from -16 to 16
        #tap_val = 1 #Constant Tap
        #tap_val = Xtap_Reg[i][j]
        Reg_Taps[i][j] = tap_val

#Node Voltage Array
Num_Bus_Nodes = len(dss.Circuit.AllNodeNames())
Bus_Voltages = np.zeros((nt,Num_Bus_Nodes),dtype=float)

#Daily Load Flow Power Loss
System_losses = np.zeros((nt,),dtype=complex)
Line_losses = np.zeros((nt,),dtype=complex)
Transformer_losses = np.zeros((nt,),dtype=complex)

for hour in range(nt):
    for reg in range(len(Regulator_List)):
        dss.RegControls.Name(Regulator_List[reg]) #Set Active Regulator
        dss.RegControls.TapNumber(Reg_Taps[reg][hour]) #Set Tap to repsective value
    dss.run_command('solve') #Run current state

    #Get Bus Voltages
    Bus_Voltages[hour] = dss.Circuit.AllBusMagPu()
    #Get Losses
    System_losses[hour] = dss.Circuit.Losses()[0] + dss.Circuit.Losses()[1] * 1j
    Line_losses[hour] = dss.Circuit.LineLosses()[0] + dss.Circuit.LineLosses()[1] * 1j


Transformer_losses = System_losses - Line_losses

#Convert to a Pandas Series
System_loss_series = pd.Series(System_losses)
Line_loss_series = pd.Series(Line_losses)
Transformer_loss_series = pd.Series(Transformer_losses)

#Convert Bus Voltage Data Frame
Node_Names = dss.Circuit.AllNodeNames()
Bus_Voltage_Transpose = Bus_Voltages.transpose()
Bus_Voltage_dFrame = pd.DataFrame(Bus_Voltage_Transpose, index=Node_Names)
Bus_Voltage_dFrame = Bus_Voltage_dFrame.transpose()

print('\nSystem_Losses\n\n', System_loss_series)
print('\nLine_Losses\n\n', Line_loss_series)
print('\nTransformer_Losses\n\n', Transformer_loss_series)
print('\nNode Voltages\n\n', Bus_Voltage_dFrame)