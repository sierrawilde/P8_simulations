# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 13:09:12 2020
@author: chrischtel
"""
import json
import numpy as np
import ROOT as r
from root_numpy import tree2array
import os

def LoadFilelist(mypath, search_str = '.'):
    '''
    Get list of all files fullfilling a few naming conditions
    '''
    filelist = []
    #print('Searching files in {} from run {} with "{}" in filename'.format(mypath, job_id, search_str))
    for (dirpath, dirnames, filenames) in os.walk(mypath, topdown=False):
        for name in filenames:
            if search_str in name and 'zero' not in name and dirpath=='.':
                filelist.append(name)
    return filelist




def AssignIDs(job_id, file):
    splitted_name = file.replace('.', '_')
    splitted_name=splitted_name.split('_')
    #print(splitted_name)
    event_id = str(job_id)+splitted_name[-2]
    return int(event_id), int(splitted_name[-2])

def MatchFile(event_id, filelist):
    for f in filelist:
        f_splitted = f.replace('.','_')
        f_splitted=f_splitted.split('_')
        #print(f_splitted)
        for sub_f in f_splitted:
            if sub_f.isdigit():
                if int(event_id) == int(sub_f):
                    #print(event_id, sub_f, f)
                    return f
    return None

def collect_and_sort_job_output_file(path):
    mega_dict = {}

    acq_prop_paths = LoadFilelist(path, 'acquisition')
    simulated_root_paths = LoadFilelist(path, 'simulated')
    reconstructed_root_paths = LoadFilelist(path, 'reconstructed')
    simulated_snr_jsons = LoadFilelist(path, 'snr_and_power')

    print(reconstructed_root_paths)

    if len(simulated_snr_jsons)>1:
        print(simulated_snr_jsons)
        raise Exception('too many snr files')
    elif len(simulated_snr_jsons)==0:
        print('no content for job')


    with open(os.path.join(path, simulated_snr_jsons[0]), 'r') as infile:
        snrs = json.load(infile)
        #print(len(snrs['snr']))
    for i in range(len(simulated_root_paths)):
        try:
            global_id, local_id = AssignIDs(0, simulated_root_paths[i])
            #print(global_id, local_id)
        except Exception as e:
            print(e)
            print(simulated_root_paths[i])
            continue
        #print('\n',global_id, local_id)
        matching_root_file = MatchFile(local_id, sorted(reconstructed_root_paths))
        #print(local_id, matching_root_file)
        matching_acq_prop_file = MatchFile(local_id, acq_prop_paths)

        #print(local_id, matching_acq_prop_file, matching_root_file)



        mega_dict[local_id] = {'simulated_event_file': simulated_root_paths[i], 'simulated_snr': snrs['snr'][local_id],
                     'reconstructed_event_file': matching_root_file, 'acquisition_props_file':matching_acq_prop_file}

    return mega_dict

def read_root(path_to_simulated_event):
    start_times, end_times, start_frequencies, signal_powers, pitch_angles, n_tracks, slopes = [], [], [], [], [], [], []
    random_seed = 0.
    try:
        f = r.TFile.Open(path_to_simulated_event, 'read')
        tree = f.Get("Event_0")
        #print(tree2array(tree, branches=["ntracks"])[0][0])
        start_frequencies = list(tree2array(tree, branches=["StartFrequencies"])[0][0])
        start_times = list(tree2array(tree, branches=["StartTimes"])[0][0])
        end_times = list(tree2array(tree, branches=["EndTimes"])[0][0])
        signal_powers = list(tree2array(tree, branches=["TrackPower"])[0][0])
        pitch_angles = list(tree2array(tree, branches=["PitchAngles"])[0][0])
        n_tracks = int(tree2array(tree, branches=["ntracks"])[0][0])
        slopes = list(tree2array(tree, branches=["Slopes"])[0][0])
        random_seed = float(tree2array(tree, branches=["RandomSeed"])[0][0])
    except Exception as e:
        print(e)

    f.Close()

    return start_times, end_times, start_frequencies, signal_powers, pitch_angles, n_tracks, slopes, random_seed


def read_event_root(path_to_reconstructed_event):
    event_total_nups, event_bins, max_nup, length, event_start, event_end, n_tracks, event_start_freq, event_slopes = [], [], [], [], [], [], [], [], []
    track_total_nups, track_bins, max_track_nup, track_start, track_start_freqs, track_end, track_slopes = [], [], [], [], [], [], []

    try:

        f = r.TFile.Open(path_to_reconstructed_event, 'read')
        tree = f.Get("multiTrackEvents")


        a = tree2array(tree, branches=["fFirstTrackTotalNUP", "fFirstTrackNTrackBins", "fFirstTrackMaxNUP", "fFirstTrackTimeLength",  "fEndTimeInRunC", "fStartTimeInRunC",  "fTotalEventSequences", "fStartFrequency", "fFirstTrackSlope"])
        b = tree2array(tree, branches=["fTracks.fTotalTrackNUP", "fTracks.fNTrackBins", "fTracks.fMaxTrackNUP", "fTracks.fStartFrequency", "fTracks.fEndTimeInRunC", "fTracks.fStartTimeInRunC", "fTracks.fSlope"])
        f.Close()

        # events

        for i in range(len(a)):
            event_total_nups.append(float(a[i][0]))
            event_bins.append(float(a[i][1]))
            max_nup.append(float(a[i][2]))
            length.append(float(a[i][3]))
            event_end.append(float(a[i][4]))
            event_start.append(float(a[i][5]))
            n_tracks.append(float(a[i][6]))
            event_start_freq.append(float(a[i][7]))
            event_slopes.append(float(a[i][8]))


        # tracks

        for i in range(len(b)):
            track_total_nups.extend(b[i][0].astype(float))
            track_bins.extend(b[i][1].astype(float))
            max_track_nup.extend(b[i][2].astype(float))
            track_start_freqs.extend(b[i][3].astype(float))
            track_end.extend(b[i][4].astype(float))
            track_start.extend(b[i][5].astype(float))
            track_slopes.extend(b[i][6].astype(float))
    except Exception as e:
        print('Couldnt read reconstructed event. Path is {}'.format(path_to_reconstructed_event))
        if path_to_reconstructed_event is not None:
            print(e)


    event_props = [event_total_nups, event_bins, max_nup, length, event_start, event_end, n_tracks, event_start_freq, event_slopes]
    track_props = [track_total_nups, track_bins, max_track_nup, track_start, track_start_freqs, track_end, track_slopes]

    print(event_props)
    return event_props, track_props



def GetSimulationtruthAndReconstruction(mega_dict, read_trigger_props=True):
    for event_id in mega_dict.keys():
        print('\nEvent id:', event_id)

        print('Read simulated truth')
        simulation_truth = read_root(mega_dict[event_id]['simulated_event_file'])

        mega_dict[event_id]['start_times_true'] = simulation_truth[0]
        mega_dict[event_id]['end_times_true'] = simulation_truth[1]
        mega_dict[event_id]['start_frequencies_true'] = simulation_truth[2]
        mega_dict[event_id]['signal_powers_true'] = simulation_truth[3]
        mega_dict[event_id]['pitch_angles_true'] = simulation_truth[4]
        mega_dict[event_id]['n_tracks_true'] = simulation_truth[5]
        mega_dict[event_id]['slopes_true'] = simulation_truth[6]
        mega_dict[event_id]['random_seeds_true'] = simulation_truth[7]

        print('Read reconstruction')
        reconstructed_events, reconstructed_tracks = read_event_root(mega_dict[event_id]['reconstructed_event_file'])

        mega_dict[event_id]['event_start_times_recon'] = reconstructed_events[4]
        mega_dict[event_id]['event_end_times_recon'] = reconstructed_events[5]
        mega_dict[event_id]['event_start_frequencies_recon'] = reconstructed_events[7]
        mega_dict[event_id]['event_total_nup_recon'] = reconstructed_events[0]
        mega_dict[event_id]['event_total_n_bins_recon'] = reconstructed_events[1]
        mega_dict[event_id]['event_max_nup_recon'] = reconstructed_events[2]
        mega_dict[event_id]['event_n_tracks_recon'] = reconstructed_events[6]
        mega_dict[event_id]['event_slopes_recon'] = reconstructed_events[8]

        mega_dict[event_id]['track_start_times_recon'] = reconstructed_tracks[3]
        mega_dict[event_id]['track_end_times_recon'] = reconstructed_tracks[5]
        mega_dict[event_id]['track_start_frequencies_recon'] = reconstructed_tracks[4]
        mega_dict[event_id]['track_total_nup_recon'] = reconstructed_tracks[0]
        mega_dict[event_id]['track_total_n_bins_recon'] = reconstructed_tracks[1]
        mega_dict[event_id]['track_max_nup_recon'] = reconstructed_tracks[2]
        mega_dict[event_id]['track_slopes_recon'] = reconstructed_tracks[6]

        if read_trigger_props:
            print('Read trigger')
            acquisition_starts = []
            acquisition_ends = []
            acquisition_lengths = []
            try:
                with open(mega_dict[event_id]['acquisition_props_file'], 'r') as infile:
                    a = json.load(infile)

                for k in a.keys():
                    acquisition_starts.append(a[k]['start_time_in_run_in_s'])
                    acquisition_ends.append(a[k]['end_time_in_run_in_s'])
                    acquisition_lengths.append(a[k]['n_records'])

            except Exception as e:
                print('Acquisition file: {}'.format(mega_dict[event_id]['acquisition_props_file']))
                print(e)
            mega_dict[event_id]['acquisition_starts'] = acquisition_starts
            mega_dict[event_id]['acquisition_ends'] = acquisition_ends
            mega_dict[event_id]['acquisition_lengths'] = acquisition_lengths


    return mega_dict

path = '.'
mega_dict = collect_and_sort_job_output_file(path)
print(mega_dict)
mega_dict = GetSimulationtruthAndReconstruction(mega_dict, read_trigger_props=False)

with open('mega_dict.json', 'w') as outfile:
    json.dump(mega_dict, outfile)
