from reg_controller import reg_controller
import opendssdirect as dss
import numpy as np


#Load in the model
dss.run_command(r'compile "C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\13Bus\MasterIEEE13.dss"')
dss.run_command('')
dss.run_command('batchedit load..* Vmin=0.8')
dss.run_command('batchedit load..* daily=PQmult')
dss.run_command('set mode=daily stepsize=1h number=1')
dss.run_command('set hour=0')

#Get list of Regulators

regulator_list = dss.RegControls.AllNames()
regulators = []
for name in regulator_list:
    regulators.append(reg_controller(name))

#Run Daily Load Flow
for hrs in range(regulators[0].total_timesteps):
    for reg in regulators:
        regulators[reg].switch_taps(hrs) #Change the taps
    dss.run_command('solve')
    for reg in regulators:
        regulators[reg].get_losses(hrs) # Get the Loss

#Print Loss
print('System Losses/n' + regulators[0].system_losses)
print('Line Losses/n' + regulators[0].line_losses)
print('Transformer Losses/n' + regulators[0].transformer_losses)
