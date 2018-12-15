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
             FRate=int(L[11])/1000+0
             FPSNR=float(L[14])+0
	     FNum_Rate_PSNR=np.append(FNum_Rate_PSNR,np.array([[FNum,FRate,FPSNR]]),0)
   FNum_Rate_PSNR=FNum_Rate_PSNR[1:np.size(FNum_Rate_PSNR,0)]
   return FNum_Rate_PSNR

def Comp_TotalRate(f_FNum_Rate_PSNR):
   TotalSize=0
   for cnt in range(np.shape(f1_FNum_Rate_PSNR)[0]):
	TotalSize=TotalSize+f_FNum_Rate_PSNR[cnt,1]
   TotalRate=TotalSize/fps
   return TotalRate
   

def Comp_TotalPSNR(f_FNum_Rate_PSNR):
   TotalMSE=0
   for cnt in range(np.shape(f_FNum_Rate_PSNR)[0]):
	TotalMSE=TotalMSE+( (255**2) / (10**(f_FNum_Rate_PSNR[cnt,2]/10)) )
   
   TotalMSE=TotalMSE/int(np.shape(f_FNum_Rate_PSNR)[0])
   TotalPSNR=10*np.log10(((255**2)/(TotalMSE)))
   return TotalPSNR




if __name__ == '__main__':
   ##Inputs
   fname1=args.fn1;
   fname2=args.fn2;
   Lfname1=args.Lfn1;
   Lfname2=args.Lfn2;
   fps=args.fps;
   #np.set_printoptions(threshold=np.nan)
   
   f1_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname1)
   f2_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname2)

   f1_numFrames=np.shape(f1_FNum_Rate_PSNR)[0]
   f2_numFrames=np.shape(f2_FNum_Rate_PSNR)[0]

   ## to consider same number of frames of both files
   if f1_numFrames > f2_numFrames:
      f1_FNum_Rate_PSNR=f1_FNum_Rate_PSNR[0:f2_numFrames,:]
   else:
      f2_FNum_Rate_PSNR=f2_FNum_Rate_PSNR[0:f1_numFrames,:]

  # plt.subplot(2, 1, 1)
  # plt.plot(f1_FNum_Rate_PSNR[:,0],f1_FNum_Rate_PSNR[:,1],"r--")
  # plt.plot(f2_FNum_Rate_PSNR[:,0],f2_FNum_Rate_PSNR[:,1],"b--")
  # plt.legend([Lfname1,Lfname2])
   #plt.title('Comparing 2 videos')
  # plt.xlabel('Frame Number')
  # plt.ylabel('Frame Size (kbits)')


  # plt.subplot(2, 1, 2)
   #f1_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname1)
  # plt.plot(f1_FNum_Rate_PSNR[:,0],f1_FNum_Rate_PSNR[:,2],"r--")
   #f2_FNum_Rate_PSNR=Get_FNum_Rate_PSNR(fname2)
  # plt.plot(f2_FNum_Rate_PSNR[:,0],f2_FNum_Rate_PSNR[:,2],"b--")
  # plt.legend([Lfname1,Lfname2])
   #plt.title('Comparing 2 videos')
  # plt.xlabel('Frame Number')
  # plt.ylabel('PSNR (dB)')
   #plt.show()
   

## compute the over all: Number of Frames, Rate, PSNR
   TotalRatefn1=Comp_TotalRate(f1_FNum_Rate_PSNR)
   TotalRatefn2=Comp_TotalRate(f2_FNum_Rate_PSNR)

   TotalPSNRfn1=Comp_TotalPSNR(f1_FNum_Rate_PSNR)
   TotalPSNRfn2=Comp_TotalPSNR(f2_FNum_Rate_PSNR)

   print("Fn1 ({}): #Frames= {}, Rate={} kbps, PSNR={} dB").format(Lfname1,f1_numFrames,TotalRatefn1,TotalPSNRfn1)
   print("Fn2 ({}): #Frames= {}, Rate={} kbps, PSNR={} dB").format(Lfname2,f2_numFrames,TotalRatefn2,TotalPSNRfn2)

   #plt.show()

