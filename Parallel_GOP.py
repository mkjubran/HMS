#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');
from __future__ import division
import numpy as np
import os, sys, subprocess, pdb
import argparse
import ConfigParser

## Parse configuration Parameters from the configuration file
def main(argv=None):
    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.
    if argv is None:
        argv = sys.argv

    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.
    conf_parser = argparse.ArgumentParser(
        description=__doc__, # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
        )
    conf_parser.add_argument("-c", "--conf_file",
                        help="Specify config file", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = { "option":"default"}

    if args.conf_file:
        config = ConfigParser.SafeConfigParser()
        config.read([args.conf_file])
        defaults.update(dict(config.items("Parametters")))
        #print(dict(config.items("Parametters")))

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[conf_parser]
        )
    parser.set_defaults(**defaults)   
    args = parser.parse_args(remaining_argv)
    return(args)

if __name__ == "__main__":
    args=main()

    ##Inputs
    RankListFile=args.ranklistfile;
    ref_pics_active_Max=args.ref_pics_active_max;
    ref_pics_active_Stitching=args.ref_pics_active_stitching;
    mode=args.mode;
    fps=args.fps;
    
    print('ref_pics_active_Max={}, ref_pics_active_Stitching={}').format(ref_pics_active_Max,ref_pics_active_Stitching) 
    fsr=fps
  
'''
if ref_pics_active_Stitching>ref_pics_active_Max:
   ref_pics_active_Stitching=ref_pics_active_Max

def Build_encoding_struct_GOP_1():
## Building encoding structure for GOP=-1
	cnt=0
	GOPLine=''
	cnt3=-1
	NumRefTemp=ref_pics_active_Max
	GOPLine='Frame1: P 1 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(ref_pics_active_Max) + ' ' + str(ref_pics_active_Max)
	for cnt1 in range(NumRefTemp):
		if cnt1>(NumRefTemp-ref_pics_active_Stitching-1):
                        print((ref_pics_Stitching_array[cnt1-(NumRefTemp-ref_pics_active_Stitching)]-iFNums_array[cnt]))
			GOPLine=GOPLine+' '+str(ref_pics_Stitching_array[cnt1-(NumRefTemp-ref_pics_active_Stitching)]-iFNums_array[cnt])
		else:
			GOPLine=GOPLine+' '+str(cnt3)
			cnt3=cnt3-1	

	GOPLine=GOPLine+' 0'
	print >> fid, GOPLine
	f.close()

def Build_encoding_struct_stitch():
	## Buidling encoding structure for Stitching mode
	ref_pics_stitch_to_use=[]
	if 0 in ref_pics_Stitching_array:
		if ref_pics_active_Stitching>0:
			ref_pics_stitch_to_use=np.append(ref_pics_stitch_to_use,0)

	ref_pics=[]
	for cnt in range(1,NumFrames):
		ref_pics_notstitch_to_use=[]
		ref_pics_old=ref_pics
		ref_pics=[]
		reference_idcs=[]
		cnt2=cnt-1
		ref_pics=np.append(ref_pics_notstitch_to_use,ref_pics_stitch_to_use)
		while len(ref_pics_notstitch_to_use)<ref_pics_active_Max-ref_pics_active_Stitching:
			ref_pics_notstitch_to_use=np.append(ref_pics_notstitch_to_use,cnt2)
			ref_pics=np.append(ref_pics_notstitch_to_use,ref_pics_stitch_to_use)
			ref_pics=np.unique(ref_pics)
			cnt2=cnt2-1
		ref_pics=np.sort(ref_pics)
		ref_pics=ref_pics[ref_pics>=0]
		ref_pics=ref_pics[::-1]

		if cnt in ref_pics_Stitching_array:
			if len(ref_pics_stitch_to_use) < ref_pics_active_Stitching: 
				ref_pics_stitch_to_use=np.append(ref_pics_stitch_to_use,cnt)
	
		GOPLine='Frame' + str(cnt) + ': P '+ str(cnt) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(len(ref_pics)) + ' ' + str(len(ref_pics))
		for cnt1 in range(len(ref_pics)):
			GOPLine=GOPLine+' '+str(int(ref_pics[cnt1]-cnt))
	
		if cnt == 1:
			GOPLine=GOPLine+' 0'
		else:	
			GOPLine=GOPLine+' 2 0'
			
		print >> fid, GOPLine
	
	f.close()

if __name__ == '__main__':

   ## read priority list
   with open(args.ranklist) as f:
       FNums = f.readlines()
   f.close()
   iFNums=map(int, FNums)

   ## get total number of frames
   NumFrames=round(len(iFNums))
   NumFrames=int(NumFrames)

   ## set GOP value based on mode type
   if (mode == "stitching") or (mode == "Stitching") or (mode == "stitch") or (mode == "Stitch"):
   	GOP=NumFrames
   	if GOP%2==0:
   		GOP=GOP-2
	else:
		GOP=int(GOP/2) * 2
   else:
	GOP=1
        ref_pics_active_Stitching=0

   ##write config files header
   fid = open('encoder_HMS_GOP.cfg','w')
   print >> fid, '#======== Coding Structure ============='
   print >> fid, 'IntraPeriod                   : -1           # Period of I-Frame ( -1 = only first)'
   print >> fid, 'DecodingRefreshType           : 2           # Random Accesss 0:none, 1:CRA, 2:IDR, 3:Recovery Point SEI'
   print >> fid, 'GOPSize                       : '+str(GOP)+'           # GOP Size (number of B slice = GOPSize-1)'
   print >> fid, 'ReWriteParamSetsFlag          : 1           # Write parameter sets with every IRAP'
   '#        Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict     deltaRPS' '#ref_idcs reference idcs'
   print >> fid,''

   ## Produce iFNums_array2 [stitching frames ordered; other frames ordered]
   iFNums_array = np.array(iFNums)
   iFNums_array=iFNums_array.clip(0, 999999999)
   indexes = np.unique(iFNums_array, return_index=True)[1]
   iFNums_array=[iFNums_array[index] for index in sorted(indexes)]
   iFNums_array=np.array(iFNums_array)

   ref_pics_Stitching_array=iFNums_array[0:ref_pics_active_Stitching]
   ref_pics_RemovedStitching_array=iFNums_array[ref_pics_active_Stitching:NumFrames]

   ref_pics_RemovedStitching_array=np.array(range(0,NumFrames))
   index=np.where(np.isin(ref_pics_RemovedStitching_array,ref_pics_Stitching_array))
   ref_pics_RemovedStitching_array=np.delete(ref_pics_RemovedStitching_array,index)

   ref_pics_RemovedStitching_array.sort()
   iFNums_array2=np.concatenate((ref_pics_Stitching_array,ref_pics_RemovedStitching_array), axis=0) #Stitching Frames + Ordered remaining Frames
   #print(iFNums_array2)

   ## Write GOP structure to config file

   if GOP == 1:
      Build_encoding_struct_GOP_1()
   else:
      Build_encoding_struct_stitch()
'''

