#!/bin/bash
#SBATCH -o complex_out.out
#SBATCH -e complex_error.out
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=jarredk@uidaho.edu
#SBATCH --mem=200G
#SBATCH -p gpu-8 --gres=gpu:1

cd /mnt/ceph/jarredk/HGRN_repo/Reports/Report_2_13_2025/jobs/Run_special
echo 'Submitting Simulation job'
date
echo '----------------------------------------'

source ~/miniconda3/bin/activate

conda activate HGRNpacks

which python


echo 'running job'


python3 run_complex.py



