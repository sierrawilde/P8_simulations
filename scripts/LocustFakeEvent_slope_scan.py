#!/usr/bin/env python

'''
Script to run Locust fake event simulation many times. Each time it generates two waterfall root files: A fake track with and without noise
Run: python LocustFakeEvent.py n_sims [-h] [-w WORKING_DIR] [-l LOCUST_BIN] [-k KATYDID_BIN] [-c CONFIG]

Author: C. Claessens (with a lot of copy from L. Saldana)
Date: 10/30/2018
'''

import argparse
import json
import random
import numpy as np
import subprocess
import os
import sys
from shutil import copyfile
#from concat_files_from_subdirs import *

def str2bool(s):
    if s in ['True', 'true', '1']:
        return True
    elif s in ['False', 'false', '0']:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected')

def modify_config(path, signal_power, locust_egg, locust_root, fake_track_random_seed, mean_slope):
    with open(path, 'r') as infile:
        config = json.load(infile)
    config['fake-track']['signal-power'] = signal_power
    config['fake-track']['root-filename'] = locust_root
    config['simulation']['egg-filename'] = locust_egg
    config['fake-track']['random-seed'] = fake_track_random_seed
    config['fake-track']['slope-mean'] = mean_slope
    with open(path, 'w') as outfile:
        json.dump(config, outfile)

def RunKatydidSimulation(n_sims, working_dir, katydid_config_path, locust_config_path, mean_slope, max_snr, min_snr, remove_egg, snr_file_path=None, min_slope=0, max_slope=1, simulation_input=None):
    """
    Draw random exponential snr, convert to power, produce egg file and analyze with katydid.
    The simulated snr and signal power is saved in a json file.
    This is done in every iteration, so that the execution of the script can be interrupted without loosing the simulation input of all performed iterations.
    parameters:
    n_sims - number of simulations started
    working_dir             -   location where everything is saved
    katydid_config_path     -   path to katydid config file
    locust_config_path      -   path to locust config
    snr                     -   beta parameter for exponential snr distribution or simulated snr
    min_snr                 -   if snr is not greater than min_snr, the simulation is skipped
    remove_egg              -   if true, locust egg files will be deleted after katydid processing
    """

    locust_binary_path = 'LocustSim'
    katydid_binary_path = 'Katydid'



    # if old_sim_input is not None:
    #    signal_snr = old_sim_input['snr']
    #    signal_power = old_sim_input['power']
    #    n_start = len(signal_snr)
    # else:

    # lists collecting simulation parameters
    signal_snr = []
    signal_power = []
    signal_slope = []
    snr_power_slope_list = []
    n_start = 0

    if snr_file_path is not None:
        with open(snr_file_path) as infile:
            read_snr = json.load(infile)['snr'][0:n_sims]
        n_sims = len(read_snr)
        print('Read SNR from json. Going to do {} simulations'.format(n_sims))


    # Run Simulations
    simulation_tracking_file = os.path.join(working_dir, 'snr_and_power_and_slope.json')
    simulation_input_file = os.path.join(working_dir, 'snr_and_power_and_slope_{}.json'.format(np.round(mean_slope, 2)))
    for ii_sim in range(n_sims):

        # draw snr, calculate power, and obtain slope
        rand_seed = random.randint(540559518,1325542009) # choose random seed

        if snr_file_path is not None:
            signal_snr.append(read_snr[ii_sim])
        else:
            signal_snr.append(np.random.uniform(min_snr, max_snr))


        signal_power.append(3e-14 * 200e6/8192 * signal_snr[-1])
        signal_slope.append(mean_slope)


        simulation_input = {'snr': signal_snr, 'power': signal_power, 'slope': signal_slope}
        # save simulation input for subdirectory output
        #print(ii_sim, simulation_input)
        #simulation_tracking_file = os.path.join(working_dir, 'snr_and_power_and_slope.json')
        # with open(simulation_tracking_file, 'w') as outfile:
        #     json.dump(simulation_input, outfile)

        # save simulation input for 1 directory output
        with open(simulation_input_file, 'w') as outfile:
            json.dump(simulation_input, outfile)

        # Egg and Root files names
        locust_egg_wnoise = os.path.join(working_dir, 'locust_wnoise_{}_{}'.format(np.round(mean_slope, 2), ii_sim+n_start) + '.egg')
        reconstruction_output = os.path.join(working_dir, 'reconstructed_event_{}_{}'.format(np.round(mean_slope, 2), ii_sim+n_start) + '.root')
        gain_variation_output = os.path.join(working_dir, 'GainVariation_{}_{}.root'.format(np.round(mean_slope, 2), ii_sim+n_start))
        raw_spec_output = os.path.join(working_dir, 'RawSpectrogram_{}_{}.root'.format(np.round(mean_slope, 2), ii_sim+n_start))
        locust_root_filename = os.path.join(working_dir, 'simulated_event_{}_{}.root'.format(np.round(mean_slope, 2), ii_sim+n_start))

        modify_config(locust_config_path, signal_power[-1], locust_egg_wnoise, locust_root_filename, rand_seed, signal_slope[-1])

        if signal_snr[-1] >= min_snr:

            # Run simulation, process with Katydid - with noise
            print('\tRunning simulation with noise')
            print(os.getcwd())
            try: # Locust
                cmd_str = "{} config={}".format(locust_binary_path,locust_config_path)
                #print(cmd_str)
                output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)
                print('\t\tCreated: {}'.format(locust_egg_wnoise))
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(e.output))
                break
            try: # Katydid
                print('\tRunning Katydid...')
                output = subprocess.check_output("{} -c {} -e {} --rtw-file {} --brw.output-file={} --writer.output-file={}".format(katydid_binary_path,katydid_config_path,locust_egg_wnoise,reconstruction_output, gain_variation_output, raw_spec_output),shell=True,stderr=subprocess.STDOUT)
                #print('\t\tCreated: {}'.format(waterfall_wnoise))
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(e.output))
                break


            # remove egg file
            if remove_egg == True:
                for root, dirs, files in os.walk(working_dir):
                    for name in files:
                        if '.egg' in name:
                            os.remove(os.path.join(working_dir, name))
    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="generate fake tracks in Locust and obtain Katydid waterfall spectrograms")

    parser.add_argument('n_sims',
                        help='Number of simulations',
                        type=int)
    parser.add_argument('-w','--working_dir',
                        help="Path to working directory to save egg and root files",
                        type=str,
                        default='./')
    parser.add_argument('-kc','--katydid_config',
                        help="Path to Katydid config file",
                        type=str,
                        default='./Katydid_fake_events_no_spsp_config.yaml')
    parser.add_argument('-lc','--locust_config',
                        help="Path to Locust config file",
                        type=str,
                        default='./LocustFakeEvent_wnoise.json')
    parser.add_argument('-snr_file_path','--snr_file_path',
                        help="Path to snr json",
                        type=str,
                        default=None)
    parser.add_argument('-sim_name', '--sim_name',
                        help='filename for saving simulation output',
                        type=str,
                        default='TestSimulation')
    parser.add_argument('-max_snr', '--max_snr',
                        help='maximum simulated snr',
                        type=float)
    parser.add_argument('-remove_egg', '--remove_egg',
                        help='remove or keep simulated egg files',
                        type=str2bool, nargs='?', const=True,
                        default = 'True')
    parser.add_argument('-from_slope', '--from_slope',
                        help='lowest mean slope in scan',
                        type=float,
                        default = 2)
    parser.add_argument('-to_slope', '--to_slope',
                        help='highest mean sope in scan',
                        type=float,
                        default = 4)
    parser.add_argument('-slope_stepsize', '--slope_stepsize',
                        help='step size in slope scan',
                        type=float,
                        default = 1)
    parser.add_argument('-min_snr', '--min_snr',
                        help='only events with snr higher than this will be simulated',
                        type=float,
                        default = 0.)

    args = parser.parse_args()

    if not args.working_dir.endswith(os.path.sep): # make sure working dir path is correctly formatted
        args.working_dir += os.path.sep

    # path where all the output goes
    simulation_path = os.path.join(args.working_dir, args.sim_name)

    # remove and create directors
    if os.path.exists(simulation_path):
        os.rmdir(simulation_path)
    os.mkdir(simulation_path)

    # copy locust and katydid config to sim path
    locust_config_p, locust_config_f = os.path.split(args.locust_config)
    new_locust_config_path = os.path.join(simulation_path, locust_config_f)
    copyfile(args.locust_config, new_locust_config_path)

    katydid_config_p, katydid_config_f = os.path.split(args.katydid_config)
    new_katydid_config_path = os.path.join(simulation_path, katydid_config_f)
    copyfile(args.katydid_config, new_katydid_config_path)

    # save args to sim path
    simulation_args = {'args': vars(args)}
    simulation_args_file = os.path.join(simulation_path, 'args.json')
    with open(simulation_args_file, 'w') as outfile:
        json.dump(simulation_args, outfile)


    # slope scan
    slopes = np.arange(args.from_slope, args.to_slope+0.5*args.slope_stepsize, args.slope_stepsize)
    for i in range(len(slopes)):

        working_dir = simulation_path
        # working_dir = os.path.join(simulation_path, str(slopes[i]))
        # if not os.path.exists(working_dir):
        #     os.mkdir(working_dir)

        print('--------RUNNING {} FAKE EVENT SIMULATIONS with mean slope {}!--------\n'.format(args.n_sims, slopes[i]))
        RunKatydidSimulation(args.n_sims, working_dir, new_katydid_config_path, new_locust_config_path, slopes[i], args.max_snr, args.min_snr, args.remove_egg, args.snr_file_path, args.from_slope, args.to_slope)
        print('--------SIMULATION DONE--------')



    sys.exit(0)
