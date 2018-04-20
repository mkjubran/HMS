#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');

import numpy as np
import os, sys, subprocess, pdb
#import cv2
import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--ranklist', type=str,
                    help='A text file with with frames rank list')

parser.add_argument('--ref_stitch', type=int,
                    help='number of stitching reference frames')

parser.add_argument('--ref_active', type=int,
                    help='Number of frames within the active reference picture set including stitching reference frames')

parser.add_argument('--mode', type=str,
                    help='Use stitching or not')

args = parser.parse_args()

##Inputs
RankListFile=args.ranklist;
ref_pics_active_Stitching=args.ref_stitch;
ref_pics_active_Max=args.ref_active;
mode=args.mode;

#with open(sys.argv[-1]) as f:
with open(args.ranklist) as f:
    FNums = f.readlines()
f.close()
#ref_pics_active_Max=5
#ref_pics_active_Stitching=3

iFNums=map(int, FNums)
if (mode == "stitching") or (mode == "Stitching"):
	GOP=len(iFNums)
	if GOP%2==0:
		GOP=GOP-2
	else:
		GOP=int(GOP/2)*2
else:
	GOP=1

NumFrames=len(iFNums)



fid = open('encoder_HMS_GOP.cfg','w')
print >> fid, '#======== Coding Structure ============='
print >> fid, 'IntraPeriod                   : -1           # Period of I-Frame ( -1 = only first)'
print >> fid, 'DecodingRefreshType           : 2           # Random Accesss 0:none, 1:CRA, 2:IDR, 3:Recovery Point SEI'
print >> fid, 'GOPSize                       : '+str(GOP)+'           # GOP Size (number of B slice = GOPSize-1)'
print >> fid, 'ReWriteParamSetsFlag          : 1           # Write parameter sets with every IRAP'
'#        Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS' '#ref_idcs reference idcs'
print >> fid,''

iFNums_array = np.array(iFNums)
ref_pics_Stitching_array=iFNums_array[0:ref_pics_active_Stitching]
ref_pics_RemovedStitching_array=iFNums_array[ref_pics_active_Stitching:NumFrames]
ref_pics_RemovedStitching_array.sort()

iFNums_array=np.concatenate((ref_pics_Stitching_array,ref_pics_RemovedStitching_array), axis=0) #Stitching Frames + Ordered remaining Frames

for cnt in range(1,ref_pics_active_Stitching+1):
	GOPLine=''
	GOPLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(cnt) + ' ' + str(cnt)
	for cnt1 in range(cnt):
		GOPLine=GOPLine+' '+str(iFNums_array[cnt1]-iFNums_array[cnt])
	GOPLine=GOPLine+' 0'
	print >> fid, GOPLine

## Building encoding structure for GOP=-1
##Frame1: P 1 0 -6.5 0.2590 0 0 1.0 0 0 0 12 12 -1 -2 -3 -4 -5 -6 -7 -8 -9 -10 -11 -12 0
if GOP == 1:
	cnt=0
	GOPLine=''
	cnt3=-1
	NumRefTemp=ref_pics_active_Max
	GOPLine='Frame1: P 1 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(ref_pics_active_Max) + ' ' + str(ref_pics_active_Max)
	if False: #select order of stitching and non-stitching ref pics
		for cnt1 in range(NumRefTemp):
			if cnt1<ref_pics_active_Stitching:
				GOPLine=GOPLine+' '+str(ref_pics_Stitching_array[cnt1]-iFNums_array[cnt])
			else:
				GOPLine=GOPLine+' '+str(cnt3)
				cnt3=cnt3-1
	else:
		for cnt1 in range(NumRefTemp):
			if cnt1>(NumRefTemp-ref_pics_active_Stitching-1):
				GOPLine=GOPLine+' '+str(ref_pics_Stitching_array[cnt1-(NumRefTemp-ref_pics_active_Stitching)]-iFNums_array[cnt])
			else:
				GOPLine=GOPLine+' '+str(cnt3)
				cnt3=cnt3-1	

	GOPLine=GOPLine+' 0'
	print >> fid, GOPLine
	f.close()
	quit()


## Buidling encoding structure for Stitching mode
for cnt in range(ref_pics_active_Stitching+1,NumFrames-1):
	GOPLine=''
	cnt3=-1
	if cnt < ref_pics_active_Max+1:
		NumRefTemp=cnt
		GOPLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(cnt) + ' ' + str(cnt)
	else:
		NumRefTemp=ref_pics_active_Max
		GOPLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(ref_pics_active_Max) + ' ' + str(ref_pics_active_Max)

	if False: #select order of stitching and non-stitching ref pics
		for cnt1 in range(NumRefTemp):
			if cnt1<ref_pics_active_Stitching:
				GOPLine=GOPLine+' '+str(ref_pics_Stitching_array[cnt1]-iFNums_array[cnt])
			else:
				GOPLine=GOPLine+' '+str(cnt3)
				cnt3=cnt3-1
	else:
		for cnt1 in range(NumRefTemp):
			if cnt1>(NumRefTemp-ref_pics_active_Stitching-1):
				GOPLine=GOPLine+' '+str(ref_pics_Stitching_array[cnt1-(NumRefTemp-ref_pics_active_Stitching)]-iFNums_array[cnt])
			else:
				GOPLine=GOPLine+' '+str(cnt3)
				cnt3=cnt3-1	

	GOPLine=GOPLine+' 0'
	print >> fid, GOPLine

f.close()    	


