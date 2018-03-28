#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');

import numpy as np

with open('OrderedFrames.txt') as f:
    FNums = f.readlines()
f.close()

cnt=0
ref_pics_active=0
ref_pics=0
ref_pics_active_Max=4
ref_pics_Max=6
ref_pics_active_Stitching=1
ref_pics_array=[]
iFNum=[]

fid = open('encoder_HMS_GOB.cfg','w')

for FNum in FNums:
	cnt=cnt+1
	i=0
	j=0
	FNum=FNum.rstrip()
	iFNum.append(int(FNum))
	ref_pics_array[:]=[]
	if ref_pics_active < ref_pics_active_Max:
		ref_pics_active=ref_pics_active+1
	else:
		ref_pics_active=ref_pics_active_Max

        if ref_pics < ref_pics_Max:
		ref_pics=ref_pics+1
	else:
		ref_pics=ref_pics_Max

	for i in range(min(cnt,ref_pics_active_Stitching)):
 		ref_pics_array.append(iFNum[i])
		print('--->',cnt,i)

	for j in range((min(cnt,ref_pics_active_Stitching)+1),min(cnt,ref_pics_active)):
 		ref_pics_array.append(j)
		print('+++++>',cnt,i)
	
	print(iFNum)
	print(ref_pics_array[:])

	GOBLine='Frame' + str(cnt) + ': P '+ str(FNum) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(ref_pics_active) + ' ' + str(ref_pics) + ' -1 0'

	print >> fid, GOBLine
	
	
f.close()    	


