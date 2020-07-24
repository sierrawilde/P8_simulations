#!/bin/bash
echo "hostname:" `/bin/hostname`
echo " "; echo " "


# source the SAME environment setup script as in the .bash_profile
# on the project8-vm.
#source /cvmfs/hep.pnnl.gov/project8/katydid/current/setup.sh
source $P8COMPUTE_BUILD_PREFIX/setup.sh
echo " "

# confirm the environment for debugging
env
# and the files that exist before execution
ls -l
echo " "
#mkdir python_packages
#pip install --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org h5py -t ./python_packages/
#PWDOUTPUT=$(pwd)
#PYTHONDIR='/python_packages/'
#FULLADDPATH=$PWDOUTPUT$PYTHONDIR
#echo $FULLADDPATH
#export PYTHONPATH=$PYTHONPATH:$FULLADDPATH
#echo $PYTHONPATH

echo $1 $2 $3 $4


ls snr_files
python scripts/LocustFakeEvent_slope_scan.py $1 -sim_name=$2 -min_snr=0 -max_snr=30 -lc=$3 -kc=$4 -from_slope=0.1 -to_slope=1.1 -slope_stepsize=$5

cp -r $2/* .
ls
