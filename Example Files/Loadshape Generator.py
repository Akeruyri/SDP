import math
import numpy as np

FilePath = r"C:\Users\louis\Desktop\SeniorDesignProject\OpenDSS\13Bus"

#Graph Visual: https://www.desmos.com/calculator/ugwcwpmtgh
def load_function(x):
    A1 = 6.18
    A2 = -0.085
    c = 0.35
    return -A1*(math.sin(x-c)+A2*math.sin(50*x*x)) #Load Function, if a sin or cos is used, values can be smoothly interpolated between days
def func_map(x):
    y_int = 0.355
    return x*(x-1)*load_function(x)+y_int #Load Function Mapped to range 0,1

# Create loadshape.dss variables
ls_name = 'LOADSHAPE_FUNCTION_TEST'
ls_pts = 96
ls_interval = 0.25  # 0.25 = 15min, 0.5 = 30min, 1 = 1hr
ls_type = 1 #0 = mult, 1 = PQmult
if ls_type == 0:
    ls_mult = np.ones(ls_pts, dtype=np.complex_)
else:
    ls_mult = np.full(ls_pts, 1+1*1j, dtype=np.complex_)

# Load Function
def r_multiplier(index):
    return func_map(float(index) / ls_pts)
def i_multiplier(index):
    return func_map(float(index) / ls_pts)
if ls_type == 0:
    for i in range(ls_pts):
        ls_mult.real[i] = ls_mult.real[i] * r_multiplier(i)
else:
    for i in range(ls_pts):
        ls_mult.real[i] = ls_mult.real[i] * r_multiplier(i)
        ls_mult.imag[i] = ls_mult.imag[i] * i_multiplier(i)

#Create Loadshape.DSS File
with open(FilePath + '\loadshapes.dss', 'w') as LS_main_file:
    if ls_type == 0:
        load_string = "New loadshape.{} npts={} interval={} Pmult=(file=loadshapes.csv, col=1)".format(ls_name,ls_pts,ls_interval)
    else:
        load_string = "New loadshape.{} npts={} interval={} Pmult=(file=loadshapes.csv, col=1) Qmult=(file=loadshapes.csv, col=2)".format(ls_name,ls_pts,ls_interval)
    LS_main_file.write(load_string)
LS_main_file.close()

#Create Loadshape Multiplier CSV
with open(FilePath + '\loadshapes.csv', 'w') as LS_mult_file:
    if ls_type == 0:
        for i in range(ls_pts):
            LS_mult_file.write("{},\n".format(ls_mult.real[i]))
    else:
        for i in range(ls_pts):
            LS_mult_file.write("{},".format(ls_mult.real[i]))
            LS_mult_file.write("{},\n".format(ls_mult.imag[i]))
LS_mult_file.close()