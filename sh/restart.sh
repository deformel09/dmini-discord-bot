#!/bin/bash

cd "$(dirname "$0")/.."
./sh/stop.sh && sleep 1 && ./sh/run.sh