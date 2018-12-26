#python ./Compare_Rate_PSNR_Frame.py --fn1=../HMSsync/HMSResu --fn2=../HMSsync/HMSRe

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

parser.add_argument('--Lfn1', type=str,
                    help='Label of legend in plots related to first Rate_PSNR file')

parser.add_argument('--fn2', type=str,
                    help='file name of second Rate_PSNR file')

parser.add_argument('--Lfn2', type=str,
                    help='Label of legend in plots related to second Rate_PSNR file')

parser.add_argument('--fps', type=int,
                    help='frame per second')

args = parser.parse_args()

def Get_FNum_PSNR(fname):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get rate and PSNR
   FNum_PSNR=np.empty((1,2), float)
   for cnt in range(len(fl)):
      L=fl[cnt].replace("..."," ")
      L=L.replace("'","")
      L=L.replace(":","")
      L=L.replace("dB","")
      L=L.replace(",","").split()
      if len(L)>0:
         if L[0]=='Frame':
             #print(L)
             FNum=int(L[1])+0
             FPSNR=float(L[3])+0
	     FNum_PSNR=np.append(FNum_PSNR,np.array([[FNum,FPSNR]]),0)
   FNum_PSNR=FNum_PSNR[1:np.size(FNum_PSNR,0)]
   return FNum_PSNR
   
def Comp_TotalRate(fname,f_FNum_PSNR):
   #read file
   with open(fname) as f:
      fl = f.readlines()
      f.close()

   ## get file size
   FNum_PSNR=np.empty((1,3), float)
   for cnt in range(len(fl)):
      L=fl[cnt].replace("..."," ")
      L=L.replace("'","")
      L=L.replace(",","").split()
      if len(L)>0:
         if ((L[0]=='File') and (L[1]=='Size')):
             #print(L)
             FSize=(int(L[4])+0)*8
   TotalRate=((FSize/np.shape(f_FNum_PSNR)[0])*fps)/1000
   return TotalRate

def Comp_TotalPSNR(f_FNum_PSNR):
   TotalMSE=0
   for cnt in range(np.shape(f_FNum_PSNR)[0]):
	TotalMSE=TotalMSE+( (255**2) / (10**(f_FNum_PSNR[cnt,1]/10)) )
   
   TotalMSE=TotalMSE/int(np.shape(f_FNum_PSNR)[0])
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
   fname1=args.fn1;
   Lfname1=args.Lfn1;
   fps=args.fps;
   
   f1_FNum_PSNR=Get_FNum_PSNR(fname1) 

   f1_FNum_VMAF=Get_FNum_VMAF(fname1)

   f1_numFrames=np.shape(f1_FNum_PSNR)[0]  

## compute the over all: Number of Frames, Rate, PSNR
   TotalRatefn1=Comp_TotalRate(fname1,f1_FNum_PSNR)

   TotalPSNRfn1=Comp_TotalPSNR(f1_FNum_PSNR)

   TotalVMAFfn1=Comp_TotalVMAF(f1_FNum_VMAF)

   print("Fn1 ({}): #Frames= {}, Rate={} kbps, PSNR={} dB, VMAF={}").format(Lfname1,f1_numFrames,TotalRatefn1,TotalPSNRfn1,TotalVMAFfn1)

   plt.show()

