import subprocess
import os


N_jobs = 500
MAX_FILES_PER_JOB = 200 # this number of files will be combined in one job

#snr_file = 'rad_power_scaling_15_snr_file.json'

#locust_config='configs/LocustFakeEvent_wnoise_100MHz_16e-7_300_flat_record.json'
#locust_config='configs/LocustFakeEvent_wnoise_100MHz_16e-7_min_pitch_flat_record.json'
#locust_config='configs/LocustFakeEvent_wnoise_100MHz_start_pitch_and_start_z.json'
locust_config='configs/LocustFakeTrack_distribution_choices.json'
katydid_config='configs/Katydid_LOCUST_may_2019_config.yaml'

working_dir_name = 'simulation_in_and_output'
jobname = 'locust_job_uniform_slope_snr_pitch'

jdl_file_list = []

print('Creating {} jdl files...'.format(N_jobs))

for n in xrange(N_jobs):


	jdl_file_name = '{}_{}.jdl'.format(jobname, n)
	jdl_file = open(jdl_file_name, 'w')
	jdl_file_list.append(jdl_file)

	job_work_dir_name = '{}_job_{}'.format(working_dir_name, n)

	#jdl_file.write('Site = "DIRAC.PNNL.us";\n')
	jdl_file.write('JobName = "{}_{}";\n'.format(jobname, n))
	jdl_file.write('CPUTime = 10002;\n')
	jdl_file.write('LogLevel = info;\n')
	jdl_file.write('Executable = "scripts/locust_job_executable.sh";\n\n')

	arg_string = '"{} {} {} {}"'.format(MAX_FILES_PER_JOB, job_work_dir_name, locust_config, katydid_config)

	jdl_file.write('Arguments = {};\n\n'.format(arg_string))
	jdl_file.write('StdOutput = "std.out";\n')
	jdl_file.write('StdError = "std.err";\n\n')
	# input sandbox with local locust build
	input_string = '"scripts", "configs"'#, "python_packages"'#.format(snr_file)
	# Add "lib", "data" for custom branch submission
	# Add "snr_dist_files/{}" for snr file submission
	# python packages contains root_numpy
	# snr_fist files can be removed if generated snr distribution is not read from file
	jdl_file.write('InputSandbox = {};\n\n'.format(input_string))



	jdl_file.write('OutputSandbox = {"std.out","std.err"};\n')
	jdl_file.write('OutputData = {"*.json", "*merged.root", "*.yaml"};\n') # only merged root, json and yaml files are uploaded as job output
	jdl_file.write('OutputSE = "PNNL-PIC-SRM-SE";\n')

	jdl_file.close()

	cmd_str = 'dirac-wms-job-submit {}'.format(jdl_file_name)
	print(cmd_str)
	out_str = subprocess.check_output(cmd_str, shell=True) # comment this (and the next line) if you dont actually want to submit the jobs
	print(out_str)
