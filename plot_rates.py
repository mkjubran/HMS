import os, sys, subprocess
import pdb
import re
import argparse
import numpy as np
from matplotlib import pyplot as plt

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

gop_length = 4;
nrps = 1;
crf = 40;
in_dir = './mp4s_HD';
out_dir = './train_frames';
override = 'y'

# Optional argument
parser.add_argument('--fn', type=str,
                    help='filename')

parser.add_argument('--h', type=int,
                    help='Plot actual rate VS predicated rate using CNN')

args = parser.parse_args()

filename=args.fn;

with open(filename) as f:
    content = f.readlines()
line = [s.rstrip() for s in content]
rate_actual = [s.split('_')[0] for s in line]
rate_predicted = [s.split(' ')[-1] for s in line]
print(line)

rate_actual=np.asarray(rate_actual).astype(np.float)
rate_predicted=np.asarray(rate_predicted).astype(np.float)
print('{} {}'.format(rate_actual,rate_predicted))

plt.plot(rate_actual,rate_predicted)
plt.show()
