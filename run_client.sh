#!/bin/bash
cd `dirname $0`

nohup python client.py > ssr.log 2>&1 &
