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
parser.add_argument('--fcodec', type=str,
                    help='file name of HM Rate_PSNR log file')

parser.add_argument('--fsift', type=str,
                    help='file name to be used to read saved np arrays, must be the mp4 file used to get the np arrays')

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
             FRate=int(L[11])/1000+0
             FPSNR=float(L[14])+0
	     FNum_Rate_PSNR=np.append(FNum_Rate_PSNR,np.array([[FNum,FRate,FPSNR]]),0)
   FNum_Rate_PSNR=FNum_Rate_PSNR[1:np.size(FNum_Rate_PSNR,0)]
   return FNum_Rate_PSNR

def Get_TotalRate(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get rate and PSNR
   for cnt in range(len(fl)):
      L=fl[cnt].split()
      if len(L)>0:
         if ((L[0]=='Bit') and (L[1]=='Rate')):
             TotalRate=float(L[3])+0
   return TotalRate

def Get_TotalPSNR(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get rate and PSNR
   for cnt in range(len(fl)):
      L=fl[cnt].split()
      if (len(L)>19):
         if ((L[0][0:5]=='Frame')):# and (L[1]=='[Y')):
             TotalPSNR=float(L[19].split('d')[0])+0
   return TotalPSNR


if __name__ == '__main__':
   ##Inputs
   fcodec=args.fcodec;
   fsift=args.fsift;
   #np.set_printoptions(threshold=np.nan)

######### Procesing Codec info
   fcodec_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fcodec)
   #print(fcodec_FNum_Rate_PSNR)

# read the over all: Number of Frames, Rate, PSNR
   TotalRatefn1=Get_TotalRate(fcodec)
   TotalPSNRfn1=Get_TotalPSNR(fcodec)
   print("fcodec: Rate={}kbps, PSNR={}dB").format(TotalRatefn1,TotalPSNRfn1)

######### Processing SIFT info
   fname=fsift.split('/')[2]
   fname=fname[0:(len(fname)-4)]
   lwinBeforedownSampledint=np.load((fname+'_SceneCutFramesBeforeDownSampling.npy'))
   lwindownSampledint=np.load((fname+'_SceneCutFrames.npy'))
   lwinsim=np.load((fname+'_lwinsim.npy'))
   lwinsimNormalizedWeighted=np.load((fname+'_lwinsimNormalizedWeighted.npy'))
   lwindissim=np.load((fname+'_lwindissim.npy'))
   lwindissimNorm=np.load((fname+'_lwindissimNormalized.npy'))
    
   lwinBeforedownSampledintplot=[1 if _ in lwinBeforedownSampledint else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
   lwindownSampledintplot=[1 if _ in lwindownSampledint else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
   lwinsimplot=[1 if _ in lwinsim else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
   lwinsimNormalizedWeightedplot=[1 if _ in lwinsimNormalizedWeighted else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
   lwindissimplot=[1 if _ in lwindissim else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
   lwindissimNormplot=[1 if _ in lwindissimNorm else 0 for _ in fcodec_FNum_Rate_PSNR[:,0]]
######### Plotting   
   plt.figure()
   plt.subplot(2, 1, 1)
   plt.plot(range(len(fcodec_FNum_Rate_PSNR[:,0])),lwindownSampledintplot,"-r*")
   plt.xlabel('Frame Number')
   plt.subplot(2, 1, 2)
   plt.plot(range(len(fcodec_FNum_Rate_PSNR[:,0])),lwinBeforedownSampledintplot,"-b*")
   plt.xlabel('Frame Number')

   plt.figure()
   plt.subplot(2, 1, 1)
   plt.plot(fcodec_FNum_Rate_PSNR[:,0],fcodec_FNum_Rate_PSNR[:,1],"ro")
   plt.legend(['fcodec'])
   plt.xlabel('Frame Number')
   plt.ylabel('Frame Size (kbits)')


   plt.subplot(2, 1, 2)
   plt.plot(fcodec_FNum_Rate_PSNR[:,0],fcodec_FNum_Rate_PSNR[:,2],"ro")
   plt.legend(['fcodec'])
   plt.xlabel('Frame Number')
   plt.ylabel('PSNR (dB)')

   plt.show()
   #plt.show()
