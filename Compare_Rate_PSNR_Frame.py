#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');
from __future__ import division
import numpy as np
import os, sys, subprocess, pdb
import argparse, re
import matplotlib.pyplot as plt


# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--fn1', type=str,
                    help='file name of first Rate_PSNR file')

parser.add_argument('--fn2', type=str,
                    help='file name of second Rate_PSNR file')

args = parser.parse_args()

def Get_FNum_Rate_PSNR(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get rate and PSNR
   FNum_Rate_PSNR=np.empty((1,3), float)
   for cnt in range(len(fl)):
      L=fl[cnt].split()
      if len(L)>0:
         if L[0]=='POC':
             FNum=int(L[1])+0
             FRate=int(L[11])+0
             FPSNR=float(L[14])+0
	     FNum_Rate_PSNR=np.append(FNum_Rate_PSNR,np.array([[FNum,FRate,FPSNR]]),0)
   FNum_Rate_PSNR=FNum_Rate_PSNR[1:np.size(FNum_Rate_PSNR,0)]
   return FNum_Rate_PSNR


if __name__ == '__main__':
   ##Inputs
   fname1=args.fn1;
   fname2=args.fn2;
   #np.set_printoptions(threshold=np.nan)

   f1_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname1)
   plt.plot(f1_FNum_Rate_PSNR[:,0],f1_FNum_Rate_PSNR[:,1],"r-")

   f2_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname2)
   plt.plot(f2_FNum_Rate_PSNR[:,0],f2_FNum_Rate_PSNR[:,1],"b-")
   plt.show()

