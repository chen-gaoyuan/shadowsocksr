#!/bin/bash
cd `dirname $0`

nohup python3 client.py > ssr.log 2>&1 &
