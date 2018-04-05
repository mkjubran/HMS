#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');

import numpy as np
import cv2, os, sys, subprocess, pdb

with open(sys.argv[-1]) as f:
    FNums = f.readlines()
f.close()
ref_pics_active_Max=5
ref_pics_active_Stitching=3

iFNums=map(int, FNums)
GOB=len(iFNums)
NumFrames=len(iFNums)

if GOB%2==0:
	GOB=GOB-2
else:
	GOB=int(GOB/2)*2

fid = open('encoder_HMS_GOB.cfg','w')
print >> fid, '#======== Coding Structure ============='
print >> fid, 'IntraPeriod                   : -1           # Period of I-Frame ( -1 = only first)'
print >> fid, 'DecodingRefreshType           : 2           # Random Accesss 0:none, 1:CRA, 2:IDR, 3:Recovery Point SEI'
print >> fid, 'GOPSize                       : '+str(GOB)+'           # GOP Size (number of B slice = GOPSize-1)'
print >> fid, 'ReWriteParamSetsFlag          : 1           # Write parameter sets with every IRAP'
'#        Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS' '#ref_idcs reference idcs'
print >> fid,''


iFNums_array = np.array(iFNums)
ref_pics_Stitching_array=iFNums_array[0:ref_pics_active_Stitching]
ref_pics_RemovedStitching_array=iFNums_array[ref_pics_active_Stitching:NumFrames]
ref_pics_RemovedStitching_array.sort()

iFNums_array=np.concatenate((ref_pics_Stitching_array,ref_pics_RemovedStitching_array), axis=0) #Stitching Frames + Ordered remaining Frames


for cnt in range(1,ref_pics_active_Stitching+1):
	GOBLine=''
	GOBLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(cnt) + ' ' + str(cnt)
	for cnt1 in range(cnt):
		GOBLine=GOBLine+' '+str(iFNums_array[cnt1]-iFNums_array[cnt])
	GOBLine=GOBLine+' 0'
	print >> fid, GOBLine

for cnt in range(ref_pics_active_Stitching+1,NumFrames-1):
	GOBLine=''
	cnt3=-1
	if cnt < ref_pics_active_Max+1:
		NumRefTemp=cnt
		GOBLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(cnt) + ' ' + str(cnt)
	else:
		NumRefTemp=ref_pics_active_Max
		GOBLine='Frame' + str(cnt) + ': P '+ str(iFNums_array[cnt]) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(ref_pics_active_Max) + ' ' + str(ref_pics_active_Max)

	if False: #select order of stitching and non-stitching ref pics
		for cnt1 in range(NumRefTemp):
			if cnt1<ref_pics_active_Stitching:
				GOBLine=GOBLine+' '+str(ref_pics_Stitching_array[cnt1]-iFNums_array[cnt])
			else:
				GOBLine=GOBLine+' '+str(cnt3)
				cnt3=cnt3-1
	else:
		for cnt1 in range(NumRefTemp):
			if cnt1>(NumRefTemp-ref_pics_active_Stitching-1):
				GOBLine=GOBLine+' '+str(ref_pics_Stitching_array[cnt1-(NumRefTemp-ref_pics_active_Stitching)]-iFNums_array[cnt])
			else:
				GOBLine=GOBLine+' '+str(cnt3)
				cnt3=cnt3-1	

	GOBLine=GOBLine+' 0'
	print >> fid, GOBLine

f.close()    	


