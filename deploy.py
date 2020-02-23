#!venv/bin/python

import argparse
import subprocess
import os
import sys

os.environ['ANSIBLE_STDOUT_CALLBACK'] = 'debug'

def run_playbook(
    playbook_filename,
    hosts,
    playbook_command='venv/bin/ansible-playbook',
    private_key=None,
    extra_options=None,
    extra_vars=None):

    command = construct_playbook_command(
        playbook_filename,
        hosts,
        playbook_command=playbook_command,
        private_key=private_key,
        extra_options=extra_options,
        extra_vars=extra_vars)

    print(command)

    process = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    output = process.stdout.readline()
    while not (output == '' and process.poll() is not None):
        print(output.strip())
        output = process.stdout.readline()

    print(process.stderr.read(), file=sys.stderr)

    exit_code = process.poll()

    if exit_code > 0:
        print('Stack execution failed, exit code: '+str(exit_code))
        exit(exit_code)


def get_hosts_str(hosts):
    if isinstance(hosts, list):
        hosts = ",".join(hosts) + ","

    if not isinstance(hosts, str):
        raise TypeError('hosts must be a str or list object')

    return hosts


def construct_playbook_command(playbook_filename, hosts, playbook_command='ansible-playbook', private_key=None, extra_options=None, extra_vars=None):

    hosts = get_hosts_str(hosts)

    command = [
        playbook_command,
        playbook_filename,
        '-i',
        hosts,
    ]

    if private_key:
        command.append('--private-key={}'.format(private_key))

    if extra_vars:
        vars = '"' + ' '.join("{}={}".format(key, value) for (key, value) in sorted(extra_vars.items())) + '"'
        command += ['--extra-vars', vars]

    if not extra_options:
        return ' '.join(command)

    if isinstance(extra_options, str):
        command.append(extra_options)
    elif isinstance(extra_options, list):
        command += extra_options
    else:
        raise TypeError("extra_options must be str or list.")

    return ' '.join(command)


def deploy(base_bucket_name, tmp_path):
    run_playbook(
        'tools/deploy.ansible.yaml',
        ['local'],
        extra_vars={
            'base_bucket_name': base_bucket_name,
            'tmp_path': tmp_path
        }
    )


parser = argparse.ArgumentParser()
parser.add_argument("-b", "--base_bucket_name")
parser.add_argument("-t", "--tmp_path")
args = parser.parse_args()

deploy(args.base_bucket_name, args.tmp_path)#