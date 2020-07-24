import subprocess
import os


N_jobs = 3
MAX_FILES_PER_JOB = 10 # this number of files will be combined in one job
slope_stepsize = 0.1

locust_config='configs/LocustFakeEvent_wnoise_100MHz_narrow_slopes.json'
katydid_config='configs/Katydid_ROACH_Config_06_2019.yaml'
working_dir_name = 'uniform_snr_slope_scan'

jobname = 'locust_job'
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
	jdl_file.write('Executable = "scripts/locust_job_executable_slope_scan.sh";\n\n')

	arg_string = '"{} {} {} {} {}"'.format(MAX_FILES_PER_JOB, job_work_dir_name, locust_config, katydid_config, slope_stepsize)

	jdl_file.write('Arguments = {};\n\n'.format(arg_string))
	jdl_file.write('StdOutput = "std.out";\n')
	jdl_file.write('StdError = "std.err";\n\n')
	jdl_file.write('InputSandbox = {scripts, configs, snr_files};\n\n')

	input_data_str = '{'

	#jdl_file.write('InputData = ;\n\n'.format(input_data_str))

	jdl_file.write('OutputSandbox = {"std.out","std.err"};\n')
	jdl_file.write('OutputData = {"*.json", "*.root", "*.yaml"};\n')
	jdl_file.write('OutputSE = "PNNL-PIC-SRM-SE";\n')

	jdl_file.close()

	cmd_str = 'dirac-wms-job-submit {}'.format(jdl_file_name)
	print(cmd_str)
	out_str = subprocess.check_output(cmd_str, shell=True) # comment this (and the next line) if you dont actually want to submit the jobs
	print(out_str)
