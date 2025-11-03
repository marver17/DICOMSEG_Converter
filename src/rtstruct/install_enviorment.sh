#! /bin/sh 

conda create -n rtstruct python=3.12 -y
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"
conda run -n rtstruct pip install --upgrade pip
conda run -n rtstruct pip install -r requirements.txt


