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
import time
from shutil import copyfile
#from concat_files_from_subdirs import *

def str2bool(s):
    if s in ['True', 'true', '1']:
        return True
    elif s in ['False', 'false', '0']:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected')

def modify_config(path, signal_power, locust_egg, locust_root, fake_track_random_seed):
    #print(path)
    with open(path, 'r') as infile:
        config = json.load(infile)
    config['fake-track']['signal-power'] = signal_power
    config['fake-track']['root-filename'] = locust_root
    config['simulation']['egg-filename'] = locust_egg
    config['fake-track']['random-seed'] = fake_track_random_seed

    with open(path, 'w') as outfile:
        json.dump(config, outfile)

def RunKatydidSimulation(n_sims, working_dir, katydid_config_path, locust_config_path, snr, min_snr, remove_egg, fixed_snr, snr_file_path=None):
    """
    Draw random exponential snr, convert to power, produce egg file and analyze with katydid.
    The simulated snr and signal power is saved in a json file.
    This is done in every iteration, so that the execution of the script can be interrupted without loosing the simulation input of all performed iterations.
    parameters:
    n_sims                  - number of simulations started
    working_dir             -   location where everything is saved
    katydid_config_path     -   path to katydid config file
    locust_config_path      -   path to locust config
    snr                     -   beta parameter for exponential snr distribution or simulated snr
    min_snr                 -   if snr is not greater than min_snr, the simulation is skipped
    remove_egg              -   if true, locust egg files will be deleted after katydid processing
    fixed_snr               -   if true, snr is not random exponential distirbution but fixed
    """

    locust_binary_path = 'LocustSim'
    katydid_binary_path = 'Katydid'


    # lists collecting simulation parameters
    signal_snr = []
    signal_power = []
    n_start = 0


    if snr_file_path is not None:
        with open(snr_file_path) as infile:
            read_snr = json.load(infile)['snr']
        print('Read SNR from json. Going to do {} simulations'.format(n_sims))



    # Run Simulations

    for ii_sim in range(n_sims):

        # draw snr and calculate power
        rand_seed = random.randint(540559518,1325542009) # choose random seed

        if snr_file_path is not None:
            i_snr = int(round(np.random.uniform(0, len(read_snr))))
            signal_snr.append(read_snr[i_snr])
        elif fixed_snr:
            signal_snr.append(snr)
        else:
            print('SNR from uniform dist: {} - {}'.format(min_snr, snr))
            signal_snr.append(np.random.uniform(min_snr, snr))

        print('\nSimulated SNR: {}\n'.format(signal_snr[-1]))

        signal_power.append(3e-14 * 200e6/8192 * signal_snr[-1])


        # save simulation input
        simulation_input = {'snr': signal_snr, 'power': signal_power}
        simulation_tracking_file = os.path.join(working_dir, 'snr_and_power.json')
        with open(simulation_tracking_file, 'w') as outfile:
            json.dump(simulation_input, outfile)

        # Egg and Root files names
        locust_egg_wnoise = os.path.join(working_dir, 'locust_wnoise' + '_{}'.format(ii_sim+n_start) + '.egg')
        reconstruction_output = os.path.join(working_dir, 'reconstructed_event' + '_{}'.format(ii_sim+n_start) + '.root')
        gain_variation_output = os.path.join(working_dir, 'GainVariation_{}.root'.format(ii_sim+n_start))
        raw_spec_output = os.path.join(working_dir, 'RawSpectrogram_{}.root'.format(ii_sim+n_start))
        locust_root_filename = os.path.join(working_dir, 'simulated_event_{}.root'.format(ii_sim+n_start))



        if signal_snr[-1] >= min_snr:
            modify_config(locust_config_path, signal_power[-1], locust_egg_wnoise, locust_root_filename, rand_seed)

            # Run simulation, process with Katydid - with noise
            print('\tRunning simulation with noise: {}/{}'.format(ii_sim+1, n_sims))
            start_time = time.time()
            try: # Locust
                cmd_str = "{} config={}".format(locust_binary_path,locust_config_path)
                print(cmd_str)
                output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)
                print('\tCreated: {}'.format(locust_egg_wnoise))
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(e.output))
                break
            try: # Katydid
                print('\tRunning Katydid...')
                cmd_str = "{} -c {} -e {} --rtw-file {} --brw.output-file={} --writer.output-file={}".format(katydid_binary_path,katydid_config_path,locust_egg_wnoise,reconstruction_output, gain_variation_output, raw_spec_output)
                print(cmd_str)
                output = subprocess.check_output(cmd_str,shell=True,stderr=subprocess.STDOUT)
                #print('\t\tCreated: {}'.format(waterfall_wnoise))
                #print(locust_egg_wnoise, gain_variation_output)
            except subprocess.CalledProcessError as e:
                print("Error: {}".format(e.output))
                break

            end_time = time.time()
            print('\tTotal event processing time was {}s'.format(end_time-start_time))


            # remove egg file if event was not found by katydid
            if remove_egg == True:
                print('\tRemove egg?')
                if not os.path.exists(reconstruction_output):
                    print('\tyes')
                    os.remove(os.path.join(locust_egg_wnoise))



    return signal_snr, signal_power

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
    parser.add_argument('-snr', '--snr',
                        help='simulated snr',
                        type=float)
    parser.add_argument('-fixed_snr', '--fixed_snr',
                        help='fix snr for every simulation',
                        type=str2bool, nargs='?', const=True,
                        default = 'False')
    parser.add_argument('-remove_egg', '--remove_egg',
                        help='remove or keep simulated egg files',
                        type=str2bool, nargs='?', const=True,
                        default = 'True')
    parser.add_argument('-scan', '--scan',
                        help='scan snr',
                        type=str2bool, nargs='?', const=True,
                        default = 'False')
    parser.add_argument('-snr_min', '--snr_min',
                        help='minimum snr in snr scan',
                        type=float,
                        default = 2)
    parser.add_argument('-snr_max', '--snr_max',
                        help='maximum snr in snr scan',
                        type=float,
                        default = 4)
    parser.add_argument('-snr_step', '--snr_step',
                        help='step size in snr scan',
                        type=float,
                        default = 1)
    parser.add_argument('-min_event_snr', '--min_event_snr',
                        help='only events with snr higher than this will be simulated',
                        type=float,
                        default = 0.)

    args = parser.parse_args()

    if not args.working_dir.endswith(os.path.sep): # make sure working dir path is correctly formatted
        args.working_dir += os.path.sep

    # path where all the output goes
    simulation_path = os.path.join(args.working_dir, args.sim_name)

    # remove and create directors
    if not os.path.exists(simulation_path):
        #os.rmdir(simulation_path)
        os.mkdir(simulation_path)

    print("\nCopy locust and katydid config to sim path")
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


    # snr scan
    if args.scan == True:
        snrs = np.arange(args.snr_min, args.snr_max, args.snr_step)
        for i in range(len(snrs)):

            working_dir = os.path.join(simulation_path, str(snrs[i]))
            if not os.path.exists(working_dir):
                os.mkdir(working_dir)

            simulation_tracking_file = os.path.join(working_dir, 'snr_and_power.json')

            print('--------RUNNING {} FAKE EVENT SIMULATIONS!--------\n'.format(args.n_sims))
            signal_snr, signal_power = RunKatydidSimulation(args.n_sims, working_dir, new_katydid_config_path, new_locust_config_path, snrs[i], args.min_event_snr, args.remove_egg, args.fixed_snr, args.snr_file_path)
            print('--------SIMULATION DONE--------')

            #cmd_str = "hadd -f {}/concat.root {}/*.root".format(working_dir, working_dir)
            #print(cmd_str)
            #output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)


    # single snr distribution
    else:
        simulation_tracking_file = os.path.join(simulation_path, 'snr_and_power.json')

        print('--------RUNNING {} FAKE EVENT SIMULATIONS!--------\n'.format(args.n_sims))
        signal_snr, signal_power = RunKatydidSimulation(args.n_sims, simulation_path, new_katydid_config_path, new_locust_config_path, args.snr, args.min_event_snr, args.remove_egg, args.fixed_snr, args.snr_file_path)
        print('--------SIMULATION DONE--------')

        #cmd_str = "hadd -f {}/concat.root {}/*.root".format(simulation_path, simulation_path)
        #print(cmd_str)
        #output = subprocess.check_output(cmd_str, shell=True, stderr=subprocess.STDOUT)


    sys.exit(0)
