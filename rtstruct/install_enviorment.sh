#! /bin/sh 

conda create -n rtstruct python=3.12 -y

conda run -n rtstruct pip install --upgrade pip
conda run -n rtstruct pip install -r requirements.txt


