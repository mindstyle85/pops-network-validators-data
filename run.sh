#!/bin/bash

python3 update.py & pids=$!
python3 -m flask run --host=0.0.0.0 & pids+=" $!"

trap "kill $pids" SIGTERM SIGINT
wait $pids