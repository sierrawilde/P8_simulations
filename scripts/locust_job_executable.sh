#!/bin/bash
echo "hostname:" `/bin/hostname`
echo " "; echo " "


# source the p8 software environment
source $P8COMPUTE_BUILD_PREFIX/setup.sh


# This is the one additional line you need to use your own libraries (which are
# assumed to have been uploaded in the output sandbox) instead.
# uncomment the following lines if submitting a loust custom branch job

#echo ${PWD}
#export LD_LIBRARY_PATH=${PWD}/lib:${LD_LIBRARY_PATH}
#export PATH=${PWD}:${PATH}
#export ROOT_INCLUDE_PATH=/usr/local/p8/locust/current/include/locust_mc/:${ROOT_INCLUDE_PATH}

# print which libraries are used
ldd $(which LocustSim) | grep -i locust
# print which locust executable is used
ldd $(which LocustSim) | grep LocustSim
echo " "; echo " "

# the "collect_locust_psyllid_output.py" script uses root_numpy which is not part of the p8 software environment
# I installed it in the python_packages folder
# This folder is added to the python path here, so it will be found by python scripts
# comment if no python_packages directory is uploaded
#echo " "; echo " "
#PWDOUTPUT=$(pwd)
#PYTHONDIR='/python_packages/'
#FULLADDPATH=$PWDOUTPUT$PYTHONDIR
#echo $FULLADDPATH
#export PYTHONPATH=$PYTHONPATH:$FULLADDPATH
#echo $PYTHONPATH
# ls $PYTHONPATH
mkdir python_packages
pip install --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org numpy -t ./python_packages/
pip install --trusted-host=pypi.python.org --trusted-host=pypi.org --trusted-host=files.pythonhosted.org root_numpy -t ./python_packages/
# confirm the environment for debugging
env

echo " "; echo " "
# and the files that exist before execution
ls -l
echo " "
echo $1 $2 $3 $4


python scripts/LocustFakeEvent.py $1 -sim_name=$2 -lc=$3 -kc=$4 -min_event_snr=0 -snr=25 #-snr_file_path=$5
# uncomment the snr-file-path if reading snrs from a file

echo " "
cd $2

# collect the information from all generated root files
python ../scripts/collect_locust_psyllid_job_output.py

# merge root files
hadd -f all_reconstructed_events_merged.root reconstructed*.root
hadd -f all_simulated_events_merged.root simulated*.root


cd ..

# copy all content from simulation working dir to job level
cp $2/* .

# list output files
ls
