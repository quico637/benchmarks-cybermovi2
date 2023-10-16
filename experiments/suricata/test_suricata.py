#!/usr/bin/python3

import os
import signal
import sys
import re
import csv

from testbase import *


class TestSuricataBase:

	MACVTAP_NAME = 'macvtap0'
	ETHTOOL_ARGS = ('tso', 'gro', 'lro', 'gso', 'rx', 'tx', 'sg')
	STATUS_INIT = 0
	STATUS_START = 1
	STATUS_DONE = 2
	STATUS_ABORT = 3

	def __init__(self):
		self.status = self.STATUS_INIT
		#reboot_remote_host(host=RUNNER_HOST, user=RUNNER_USER)
		self.shell = get_remote_shell(host=RUNNER_HOST, user=RUNNER_USER)

	def simple_call(self, cmd):
		return self.shell.run(cmd, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer, allow_error=True).return_code
	
	def parse_monitor_proc(self, output_file):

		with open("nload_output.txt", "rb") as input_file:
			line2 = input_file.read()
		line = str(line2)


		# Parse the data to find HMax and HAvg values for "Device enp1s0"
		pattern = r"\d+;\d+HMax: \d+.\d+ .Bit/s"
		match = re.findall(pattern, line)

		print(f"line: {line}")

		if match:
			HMax = match[-1]

			pattern = r"\d+.\d+"
			HMax = re.findall(pattern, HMax)[-1]


				# Write the HMax and HAvg values to a CSV file
			with open(f"{self.local_tmpdir}/nload_data.csv", "w", newline="") as csv_file:
				writer = csv.writer(csv_file)
				writer.writerow(["HMax"])
				writer.writerow([HMax])

			print(f"HMax: {HMax}")
			


	def init_test_session(self, session_id, local_tmpdir, session_tmpdir, args):
		log('Adjusting swappiness of remote host...')
		self.simple_call(['sudo', 'sysctl', '-w', 'vm.swappiness=' + str(args.swappiness)])
		self.simple_call(['sysctl', 'vm.swappiness'])
		log('Creating local temp dir...')
		subprocess.call(['mkdir', '-p', local_tmpdir])
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		log('Initializing remote temp dir...')
		self.simple_call(['mkdir', '-p', session_tmpdir])
		subprocess.call(['rsync', '-zvrpE', './tester_script', '%s@%s:%s/' % (RUNNER_USER, RUNNER_HOST, RUNNER_TMPDIR)])
		log('Making sure remote system is clean...')

	def upload_test_session(self, session_id, local_tmpdir, session_tmpdir):
		log('Upload session data to data server...')
		data_store = '%s@%s:%s/' % (DATA_USER, DATA_HOST, DATA_DIR)
		subprocess.call(['sudo', 'rsync', '-zvrpE', local_tmpdir, data_store])
		self.simple_call(['sudo', 'rsync', '-zvrpE', session_tmpdir, data_store])

	def destroy_session(self, session_id, local_tmpdir, session_tmpdir, args):
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		if args.macvtap:
			self.simple_call(['sudo', 'ip', 'link', 'del', 'macvtap0'])
		# subprocess.call(['rm', '-rfv', local_tmpdir])
		# self.simple_call(['rm', '-rfv', session_tmpdir])

	def close(self):
		del self.shell

	def wait_for_suricata(self, session_tmpdir, prepend=[]):
		while True:
			ret = self.shell.run(prepend + ['test', '-f', session_tmpdir + '/eve.json'], allow_error=True)
			if ret.return_code != 0:
				log('Waiting for 8sec for Suricata to stabilize...')
				time.sleep(8)
				
			else:
				log('Suricata is ready.')
				return

	def replay_trace(self, local_tmpdir, trace_file, nworker, src_nic, poll_interval_sec, replay_speed_X):
		
		os.remove("nload_output.txt")

		with open("nload_output.txt", "w") as output_file:
			monitor_proc = subprocess.Popen(["nload", 'device', src_nic], stdout=output_file, stderr=subprocess.PIPE, text=True)


		workers = []
		with open(local_tmpdir + '/tcpreplay.out', 'wb') as f:
			try:
				
				if replay_speed_X != 1:
					cmd = ['sudo', 'tcpreplay', '-i', src_nic, '--multiplier', str(replay_speed_X), LOCAL_TRACE_REPO_DIR + '/' + trace_file]
				else:
					cmd = ['sudo', 'tcpreplay', '-i', src_nic, LOCAL_TRACE_REPO_DIR + '/' + trace_file]
				for i in range(nworker):
					workers.append(subprocess.Popen(cmd, stdout=f, stderr=f))
				log('Waiting for all %d tcpreplay processes to complete...' % nworker)
				for w in workers:
					w.wait()
				# log('All tcpreplay FIRST ROUND')


				# # sencond time
				# workers = []
				# for i in range(nworker):
				# 	workers.append(subprocess.Popen(cmd, stdout=f, stderr=f))
				# log('Waiting for all %d tcpreplay processes to complete...' % nworker)
				# for w in workers:
				# 	w.wait()
				# log('All tcpreplay processes are complete. Wait for 20sec before proceeding.')



				time.sleep(20)
			except KeyboardInterrupt as e:
				log('Interrupted. Stopping tcpreplay processes...')
				for w in workers:
					w.terminate()
				self.status = self.STATUS_ABORT
				log('Aborted.')
			finally:
				monitor_proc.send_signal(signal.SIGINT)
				monitor_proc.wait()
				self.parse_monitor_proc(output_file)


	
	def start(self):
		raise NotImplementedError()
