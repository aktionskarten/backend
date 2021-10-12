#!/usr/bin/env bash

echo "Init postgres for aktionskarten"
python postgres.py createuser --user maps --password maps
python postgres.py initdb --owner maps maps
