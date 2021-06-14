
import reg_controller
import opendssdirect as dss
from opendssdirect.utils import run_command

#Load in the model
dss.run_command(r'compile "C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\13Bus\MasterIEEE13.dss"')
dss.run_command('')
dss.run_command('batchedit load..* Vmin=0.8')
dss.run_command('batchedit load..* daily=PQmult')
dss.run_command('set mode=daily stepsize=1h number=1')
dss.run_command('set hour=0')


#Get list of Regulators


#Run Daily Load Flow


#Summarize Loss