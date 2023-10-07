#!/usr/bin/python3

import os
import signal
import sys

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
		# reboot_remote_host(host=RUNNER_HOST, user=RUNNER_USER)
		self.shell = get_remote_shell(host=RUNNER_HOST, user=RUNNER_USER)
		self.zombie_shell = get_remote_shell(host=ZOMBIE_HOST, user=ZOMBIE_USER)

	def simple_call(self, cmd, shell):
		return shell.run(cmd, stdout=sys.stdout.buffer, stderr=sys.stdout.buffer, allow_error=True).return_code
	
	def init_test_session(self, session_id, local_tmpdir, session_tmpdir, args, shell):
		log('Adjusting swappiness of remote host...')
		self.simple_call(['sudo', 'sysctl', '-w', 'vm.swappiness=' + str(args.swappiness)], shell)
		self.simple_call(['sysctl', 'vm.swappiness'], shell)
		log('Creating local temp dir...')
		subprocess.call(['mkdir', '-p', local_tmpdir])
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		log('Initializing remote temp dir...')
		self.simple_call(['mkdir', '-p', session_tmpdir], shell)
		subprocess.call(['rsync', '-zvrpE', './tester_script', '%s@%s:%s/' % (RUNNER_USER, RUNNER_HOST, RUNNER_TMPDIR)])
		log('Making sure remote system is clean...')
		self.simple_call(['sudo', 'ip', 'link', 'del', 'macvtap0'], shell)
		self.simple_call(['sudo', 'pkill', '-9', 'Suricata-Main'], shell)
		# self.simple_call(['sudo', 'pkill', '-9', 'top'])
		# self.simple_call(['sudo', 'pkill', '-9', 'atop'])
		# Configure NIC to fit Suricata's need.
		log('Configuring src and dest NICs...')
		self.simple_call(['sudo', 'ifconfig', args.dest_nic, 'promisc'], shell)
		for optarg in self.ETHTOOL_ARGS:
			subprocess.call(['sudo', 'ethtool', '-K', args.src_nic, optarg, 'off'])
			self.simple_call(['sudo', 'ethtool', '-K', args.dest_nic, optarg, 'off'], shell)
		# Setup macvtap
		if args.macvtap is True:
			log('Creating macvtap device for NIC "%s"...' % args.dest_nic)
			tap_name = self.MACVTAP_NAME
			mac_addr = gen_random_mac_addr()
			self.simple_call(['sudo', 'ip', 'link', 'add', 'link', args.dest_nic, 'name', tap_name, 'type', 'macvtap', 'mode', 'passthru'], shell)
			self.simple_call(['sudo', 'ip', 'link', 'set', tap_name, 'address', mac_addr, 'up'], shell)
			self.simple_call(['sudo', 'ip', 'link', 'show', tap_name], shell)

	def upload_test_session(self, session_id, local_tmpdir, session_tmpdir):
		log('Upload session data to data server...')
		data_store = '%s@%s:%s/' % (DATA_USER, DATA_HOST, DATA_DIR)
		self.simple_call(['mkdir', '-p', DATA_DIR], shell)
		subprocess.call(['sudo', 'rsync', '-zvrpE', local_tmpdir, data_store])
		self.simple_call(['sudo', 'rsync', '-zvrpE', session_tmpdir, data_store], shell)

	def destroy_session(self, shell, session_id, local_tmpdir, session_tmpdir, args):
		subprocess.call(['sudo', 'pkill', '-9', 'tcpreplay'])
		if args.macvtap:
			self.simple_call(['sudo', 'ip', 'link', 'del', 'macvtap0'], shell)
		subprocess.call(['rm', '-rfv', local_tmpdir])
		self.simple_call(['rm', '-rfv', session_tmpdir], shell)

	def close(self):
		del self.shell
		del self.zombie_shell

	def wait_for_suricata(self, session_tmpdir, prepend=[], shell):
		while True:
			if self.simple_cal(prepend + ['test', '-f', session_tmpdir + '/eve.json'], shell) != 0:
				log('Waiting for 1sec for Suricata to stabilize...')
				time.sleep(1)
			else:
				log('Suricata is ready.')
				return

	def replay_trace(self, local_tmpdir, trace_file, nworker, src_nic, poll_interval_sec, replay_speed_X):
		monitor_proc = subprocess.Popen([os.getcwd() + '/tester_script/sysmon.py',
			'--delay', str(poll_interval_sec), '--outfile', 'sysstat.sender.csv',
			'--nic', src_nic, '--nic-outfile', 'netstat.tcpreplay.{nic}.csv'],
			stdout=sys.stdout, stderr=sys.stderr, cwd=local_tmpdir)
		workers = []
		with open(local_tmpdir + '/tcpreplay.out', 'wb') as f:
			try:
				cmd = ['sudo', 'tcpreplay', '-i', src_nic, LOCAL_TRACE_REPO_DIR + '/' + trace_file]
				if replay_speed_X != 1:
					cmd += ['--multiplier', str(replay_speed_X)]
				for i in range(nworker):
					workers.append(subprocess.Popen(cmd, stdout=f, stderr=f))
				log('Waiting for all %d tcpreplay processes to complete...' % nworker)
				for w in workers:
					w.wait()
				log('All tcpreplay processes are complete. Wait for 10sec before proceeding.')
				time.sleep(10)
			except KeyboardInterrupt as e:
				log('Interrupted. Stopping tcpreplay processes...')
				for w in workers:
					w.terminate()
				self.status = self.STATUS_ABORT
				log('Aborted.')
			finally:
				monitor_proc.send_signal(signal.SIGINT)
				monitor_proc.wait()

	def start(self):
		raise NotImplementedError()
