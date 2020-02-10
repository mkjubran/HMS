#python ./Compare_Rate_PSNR_Frame.py --fn1=../HMSsync/HMSResu --fn2=../HMSsync/HMSRe

from __future__ import division
import numpy as np
import os, sys, subprocess, pdb
import argparse, re
import matplotlib.pyplot as plt


# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--fn', type=str,
                    help='file name of first Rate_PSNR file')

parser.add_argument('--fps', type=int,
                    help='frame per second')

parser.add_argument('--nf', type=int,
                    help='number of frames')


args = parser.parse_args()

def Get_FNum_Rate_PSNR(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get rate and PSNR
   FNum_Rate_PSNR=np.empty((1,3), float)
   for cnt in range(len(fl)):
      L=fl[cnt].replace("..."," ")
      L=L.replace("'","")
      L=L.replace(",","").split()
      if len(L)>0:
         if L[0]=='POC':
             #print(L)
             FNum=int(L[1])+0
             FRate=int(L[11])+0
             FPSNR=float(L[14])+0
	     FNum_Rate_PSNR=np.append(FNum_Rate_PSNR,np.array([[FNum,FRate,FPSNR]]),0)
   FNum_Rate_PSNR=FNum_Rate_PSNR[1:np.size(FNum_Rate_PSNR,0)]
   return FNum_Rate_PSNR

def Comp_TotalRate(f_FNum_Rate_PSNR):
   TotalSize=0
   for cnt in range(np.shape(f_FNum_Rate_PSNR)[0]):
	TotalSize=TotalSize+f_FNum_Rate_PSNR[cnt,1]
   TotalRate=((TotalSize/np.shape(f_FNum_Rate_PSNR)[0])*fps)/1000
   return TotalRate
   

def Comp_TotalPSNR(f_FNum_Rate_PSNR):
   TotalMSE=0
   for cnt in range(np.shape(f_FNum_Rate_PSNR)[0]):
	TotalMSE=TotalMSE+( (255**2) / (10**(f_FNum_Rate_PSNR[cnt,2]/10)) )
   
   TotalMSE=TotalMSE/int(np.shape(f_FNum_Rate_PSNR)[0])
   TotalPSNR=10*np.log10(((255**2)/(TotalMSE)))
   return TotalPSNR


def Get_FNum_VMAF(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get VMAF Score
   FNum_VMAF=np.empty((1,2), float)
   for cnt in range(len(fl)):
      L=fl[cnt].replace("..."," ")
      L=L.replace("'","")
      L=L.replace("\\n","")
      L=L.replace("]","")
      L=L.replace(":"," ")
      L=L.replace(",","").split()
      if len(L)>0:
         if L[0]=='VMAF_Frame':
             #print(L)
             #print('{}...{}'.format(L[1],L[15]))
             FNum=int(L[1])+0
             FVMAF=float(L[15])+0
	     FNum_VMAF=np.append(FNum_VMAF,np.array([[FNum,FVMAF]]),0)
   FNum_VMAF=FNum_VMAF[1:np.size(FNum_VMAF,0)]
   return FNum_VMAF

def Comp_TotalVMAF(f_FNum_VMAF):
   TotalVMAF=0
   for cnt in range(np.shape(f_FNum_VMAF)[0]):
	TotalVMAF=TotalVMAF+f_FNum_VMAF[cnt,1]
   TotalVMAF=(TotalVMAF/np.shape(f_FNum_VMAF)[0])
   return TotalVMAF

if __name__ == '__main__':
   ##Inputs
   nf=0;
   fname1=args.fn;
   fps=args.fps;
   nf=args.nf;

   f1_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname1)
   f1_FNum_VMAF=Get_FNum_VMAF(fname1)
   f1_numFrames=np.shape(f1_FNum_Rate_PSNR)[0]
   nfc=f1_numFrames

   if (nf != 0) and (nf <= f1_numFrames):
	f1_FNum_Rate_PSNR=f1_FNum_Rate_PSNR[0:nf,:]
	f1_FNum_VMAF=f1_FNum_VMAF[0:nf,:]
	nfc=nf

## compute the over all: Number of Frames, Rate, PSNR
   TotalRatefn1=Comp_TotalRate(f1_FNum_Rate_PSNR)
   TotalPSNRfn1=Comp_TotalPSNR(f1_FNum_Rate_PSNR)
   TotalVMAFfn1=Comp_TotalVMAF(f1_FNum_VMAF)

#   print("Number of frames used to compute Rate, PSNR and VMAR is {}").format(nfc)
#   print("Fn1 ({}): #Frames= {}, Rate={} kbps, PSNR={} dB, VMAF={}").format(Lfname1,f1_numFrames,TotalRatefn1,TotalPSNRfn1,TotalVMAFfn1)

   T1=fname1.split('.da')[0];
   T2=T1.split('_')[-1];
   T3=T1.split('Rate')[-1];
   if T2.isdigit():
      R1=int(T2)/1000
   else:
      R1=int(T3)/1000

   print("{}	{}	{}	{}	{}").format(f1_numFrames,int(R1),TotalRatefn1,TotalPSNRfn1,TotalVMAFfn1)

