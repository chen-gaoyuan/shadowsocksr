#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 breakwall
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import time
import json
import signal
import platform
import subprocess
import urllib.request
import ParseSsr #https://www.jianshu.com/p/81b1632bea7f

file_path = 'ssr-servers.json'
useful_servers = []
ssr_process = None
try:	
	f = open(file_path, 'r')
	useful_servers = json.load(f)
except:
	print('not found config', flush=True)

def new_subprocess(cmd):
	print('cmd: ' + cmd)
	if(platform.system()=='Windows'):
		return subprocess.Popen(cmd, shell=True, close_fds=True)
	else:
		return subprocess.Popen(cmd, shell=True, close_fds=True, preexec_fn = os.setsid)
	
def kill_pid(pid):
	if(platform.system()=='Windows'):
		kill_proc = subprocess.Popen(
			"TASKKILL /F /PID {pid} /T".format(pid=pid),
			stdin=subprocess.PIPE,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
	else:
		os.killpg(p.pid, signal.SIGUSR1)

def check_connect(port):
	try:
		p=new_subprocess('curl.exe -s --socks5-hostname 127.0.0.1:' + port + ' www.google.com')
		p.wait(5)
		print('returncode=======>', p.returncode)
		return p.returncode == 0
	except Exception as e:
		print(e, flush=True)
		kill_pid(p.pid)
		return False

def ssr_connect_test(ssr, test_port):
	cmd="python2 shadowsocks/local.py -qq -s %s -p %s -k %s -m %s -O %s -o %s -b %s " %(ssr['server'],ssr['port'],ssr['password'],ssr['method'],ssr['protocol'],ssr['obfs'],"0.0.0.0")
	if(len(ssr.get('protoparam',""))>1):
		cmd+="-G %s " % ssr['protoparam']
	if(len(ssr.get('obfsparam',""))>1):
		cmd+="-g %s " % ssr['obfsparam']
	# print(cmd)

	p=new_subprocess(cmd + " -l " + test_port)
	time.sleep(3)
	start=time.time()
	ok=check_connect(test_port)
	end=time.time()
	kill_pid(p.pid)
	if ok:
		print('found! use time', end - start, flush=True)
		return cmd
	return None

def choose_one_connect(ssr_config,port,test_port):
	cmd = None
	choose_ssr = None
	# 先找以前连过的
	print('test useful server', flush=True)
	for s in useful_servers:
		for ssr in ssr_config:
			ss = ssr['server']+":"+ssr['port']
			if ss == s:
				cmd = ssr_connect_test(ssr,test_port)
				if cmd:
					choose_ssr = ssr
					break
		if cmd:
			break
	# 全部找一遍
	if not cmd:
		print('test all server', flush=True)
		for ssr in ssr_config:
			cmd = ssr_connect_test(ssr,test_port)
			if cmd:
				choose_ssr = ssr
				break
	# 找到了
	if cmd:
		s = choose_ssr['server']+":"+choose_ssr['port']
		# 提高优先级， 下次先试试这个可不可以用
		try:
			useful_servers.index(s)
			useful_servers.remove(s)
			useful_servers.insert(0, s)
		except:
			useful_servers.insert(0, s)
		f = open(file_path, 'w')
		json.dump(useful_servers, f)

		global ssr_process
		if ssr_process:
			kill_pid(ssr_process.pid)
		ssr_process=new_subprocess(cmd + " -l " + port)
		return True
	
	return False


def main():
	time.sleep(3)
	
	ssr_subscribe = ""
	ssr_config = []
	while True:
		try:
			f = open('client_config.json', 'r')
			config = json.load(f)
			port=config['port']
			test_port=config['test_port']
			url=config['url']
			headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}

			f = urllib.request.Request(url,headers=headers) 
			ssr_subscribe = urllib.request.urlopen(f).read().decode('utf-8') #获取ssr订阅链接中数据
			ssr_config = ParseSsr.parse_data(ssr_subscribe)

			if choose_one_connect(ssr_config, port, test_port):
				break
			
		except Exception as e:
			print(e, flush=True)
		time.sleep(30)

	err_count = 0
	while True:
		if err_count > 0:
			print("wait 3", flush=True)
			time.sleep(3)
		else:
			print("wait 60", flush=True)
			time.sleep(60)
		ok=check_connect(port)
		if ok:
			err_count = 0
		else:
			err_count = err_count + 1
		if err_count > 3:
			choose_one_connect(ssr_config, port, test_port)
			err_count = 0
try:
	main()
except Exception as e:
	print(e, flush=True)

if ssr_process:
	kill_pid(ssr_process.pid)