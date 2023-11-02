#!/usr/bin/python3

import os
os.chdir('/home/quico/benchmarks/experiments/suricata')
import subprocess
import sys
from helpers import *
import re


def do_command(line):
	line = line.split(maxsplit=2)
	nround = int(line[0])
	script = line[1]
	args = line[2].split() if len(line) == 3 else []
	command = ['sudo', script] + args
	for i in range(0, nround):
		log('Round %d / %d: ' % (i+1, nround) + str(command))
		subprocess.call(command)


def do_all_commands(test_path):
	with open(test_path, 'r') as f:
		for line in f:
			line = line.strip()
			if len(line) == 0 or line.startswith('#'):
				continue
			else:
				do_command(line)
	log('All commands are done.')


def main():
	
	# Define the file path and the pattern to search for

	file_path = './test_suricata_bare.py'
	pattern_to_search = r'FILE = .*'
	replacement_text = f'FILE = \'{sys.argv[1]}\''

	# Read the file's content
	with open(file_path, 'r') as file:
		file_content = file.read()

	# Use regular expressions to search and replace the pattern
	modified_content = re.sub(pattern_to_search, replacement_text, file_content)

	# Write the modified content back to the file
	with open(file_path, 'w') as file:
		file.write(modified_content)

	do_all_commands('./config/tests.%s.txt' % HOSTNAME)


if __name__ == '__main__':
	main()
