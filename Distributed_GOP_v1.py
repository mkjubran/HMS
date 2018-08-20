#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');
from __future__ import division
import numpy as np
import os, sys, subprocess, pdb
import argparse
import ConfigParser
import time, re
import math



INF = 999

###--------------------------------------------------------------
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

###--------------------------------------------------------------
## read frame numbers from Rank List File
def read_ranklist():
   ## read priority list
   with open(RankListFile) as f:
       FNums = f.readlines()
   f.close()
   iFNums=map(int, FNums)

   ## get total number of frames
   NumFrames=round(len(iFNums))
   NumFrames=int(NumFrames)
   return(iFNums,NumFrames)

###--------------------------------------------------------------
## convert iFNums from vector to matrix such that each row is a separate GOP
def Create_Distributed_GOP_Matrix():
   NotAlloc_Frames=np.arange(0,NumFrames)
   for val in ref_pics_active_Stitching:
      idx=np.where(NotAlloc_Frames==val)
      NotAlloc_Frames=np.delete(NotAlloc_Frames,idx)
   
   Distributed_GOP_Matrix=[]
   ref_pics_in_Distributed_GOP_Matrix=np.empty(0)
   while len(NotAlloc_Frames)>0:
       Distributed_GOP_Vec=np.empty(0)
       ref_pics_active_Stitching_temp=ref_pics_active_Stitching
       if len(Distributed_GOP_Matrix) > (GOP-1):
           cnt=0
           while len(ref_pics_active_Stitching_temp)<num_ref_pics_active_Max:
              ref_pics_active_Stitching_temp=np.append(ref_pics_active_Stitching_temp,Distributed_GOP_Matrix[len(Distributed_GOP_Matrix)-cnt-1])
              ref_pics_active_Stitching_temp=np.unique(ref_pics_active_Stitching_temp)
              cnt=cnt+1
              #print('{}...{}...{}..{}'.format(cnt,len(ref_pics_active_Stitching_temp),num_ref_pics_active_Max,Distributed_GOP_Matrix[len(Distributed_GOP_Matrix)-cnt-1]))
       ref_pics_added=0;
       while len(Distributed_GOP_Vec)<GOP:
          if len(NotAlloc_Frames)==0:
              break
          elif len(ref_pics_active_Stitching_temp)==0:
              Distributed_GOP_Vec=np.append(Distributed_GOP_Vec,NotAlloc_Frames[0])
              NotAlloc_Frames=np.delete(NotAlloc_Frames,0)
          elif ref_pics_active_Stitching_temp[0]<NotAlloc_Frames[0]: 
              Distributed_GOP_Vec=np.append(Distributed_GOP_Vec,ref_pics_active_Stitching_temp[0])
              ref_pics_active_Stitching_temp=np.delete(ref_pics_active_Stitching_temp,0)
              ref_pics_added=ref_pics_added+1
          else:
              Distributed_GOP_Vec=np.append(Distributed_GOP_Vec,NotAlloc_Frames[0])
              NotAlloc_Frames=np.delete(NotAlloc_Frames,0)
       if len(Distributed_GOP_Vec)==GOP:
              Distributed_GOP_Matrix=np.append(Distributed_GOP_Matrix,Distributed_GOP_Vec)
              
       ref_pics_in_Distributed_GOP_Matrix=np.append(ref_pics_in_Distributed_GOP_Matrix,ref_pics_added)
   Distributed_GOP_Matrix=np.reshape(Distributed_GOP_Matrix,(int(len(Distributed_GOP_Matrix)/GOP),GOP))
   return(Distributed_GOP_Matrix,ref_pics_in_Distributed_GOP_Matrix)

###--------------------------------------------------------------
def call(cmd):
    # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
    #proc = subprocess.Popen(cmd, \
    #               stdout=subprocess.PIPE, shell=True)
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return (out, err)

###--------------------------------------------------------------
def call_bg(cmd):
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE, shell=True)
    return proc

###--------------------------------------------------------------
def export_frames(fn):
    osout = call('rm -rf ../Split_Video')
    osout = call('mkdir ../Split_Video')
    osout = call('mkdir ../Split_Video/pngall')
    osout = call('ffmpeg -r 1 -i {} -r 1 -qp 0 ../Split_Video/pngall/%d.png'.format(fn))
    return 

###--------------------------------------------------------------
def Split_Video_GOP(Distributed_GOP_Matrix):
    for cnt_row in range(np.shape(Distributed_GOP_Matrix)[0]):
        osout = call('rm -rf ../Split_Video/Part{}'.format(cnt_row))
        osout = call('mkdir ../Split_Video/Part{}'.format(cnt_row))
        for cnt_col in range(np.shape(Distributed_GOP_Matrix)[1]):
            osout = call('cp -rf ../Split_Video/pngall/{}.png ../Split_Video/Part{}/{}.png'.format(int(Distributed_GOP_Matrix[cnt_row,cnt_col]+1),cnt_row,int(cnt_col+1)))
        osout = call('ffmpeg -start_number 0 -i ../Split_Video/Part{}/%d.png -c:v libx264 -vf "fps=25,format=yuv420p" -qp 0 ../Split_Video/Part{}/Part{}.mp4'.format(cnt_row,cnt_row,cnt_row))
        osout = call('ffmpeg -y -i ../Split_Video/Part{}/Part{}.mp4 -vcodec rawvideo -pix_fmt yuv420p -qp 0 ../Split_Video/Part{}/Part{}.yuv'.format(cnt_row,cnt_row,cnt_row,cnt_row))
    return

###--------------------------------------------------------------
def Create_Encoder_Config(Distributed_GOP_Matrix,ref_pics_in_Distributed_GOP_Matrix):
    for Pcnt in range(np.shape(Distributed_GOP_Matrix)[0]):
        if Pcnt==0:
            print('GOP#{} [{} - {}]'.format(Pcnt,int(Distributed_GOP_Matrix[Pcnt][0]),int(Distributed_GOP_Matrix[Pcnt][np.shape(Distributed_GOP_Matrix)[1]-1])))
        else:
            print('GOP#{} [{} - {}]'.format(Pcnt,int((Distributed_GOP_Matrix[Pcnt-1][np.shape(Distributed_GOP_Matrix)[1]-1])+1),int(Distributed_GOP_Matrix[Pcnt][np.shape(Distributed_GOP_Matrix)[1]-1])))
    	Abs_ref_pics_Stitching_array_Distributed=ref_pics_active_Stitching[0:int(ref_pics_in_Distributed_GOP_Matrix[Pcnt])]
    	#num_ref_pics_active_Stitching_Distributed=len(Abs_ref_pics_Stitching_array_Distributed)
        num_ref_pics_active_Stitching_Distributed=len(ref_pics_active_Stitching)
    	NumFrames_Distributed=GOP
    	num_ref_pics_active_Max_Distributed=num_ref_pics_active_Max
        
        ref_pics_Stitching_array_Distributed=[];
        relative_ref_value=0
        if Pcnt>0:
           for Abs_ref_value in Abs_ref_pics_Stitching_array_Distributed:
              if Abs_ref_value <= Distributed_GOP_Matrix[Pcnt-1][GOP-1]:
                  ref_pics_Stitching_array_Distributed=np.append(ref_pics_Stitching_array_Distributed,relative_ref_value)
                  relative_ref_value=relative_ref_value+1
              else:
                  ref_pics_Stitching_array_Distributed=np.append(ref_pics_Stitching_array_Distributed,Abs_ref_value)
        else:
           ref_pics_Stitching_array_Distributed=Abs_ref_pics_Stitching_array_Distributed
        
        ref_pics_Stitching_array_Distributed=ref_pics_Stitching_array_Distributed.astype(int)
        print('Stitching Frames in the Ref Picture set: Absolute Frame Numbers = {}').format(Abs_ref_pics_Stitching_array_Distributed)
        print('Stitching Frames in the Ref Picture set: Frame Numbers Relative to this GOP = {}').format(ref_pics_Stitching_array_Distributed)


    	##write config files header
    	fid = open('../Split_Video/Part{}/encoder_HMS_GOP_{}.cfg'.format(Pcnt,Pcnt),'w')
    	print >> fid, '#======== Coding Structure ============='
    	print >> fid, 'IntraPeriod                   : -1           # Period of I-Frame ( -1 = only first)'
    	print >> fid, 'DecodingRefreshType           : 2           # Random Accesss 0:none, 1:CRA, 2:IDR, 3:Recovery Point SEI'
    	print >> fid, 'GOPSize                       : '+str(GOP)+'           # GOP Size (number of B slice = GOPSize-1)'
    	print >> fid, 'ReWriteParamSetsFlag          : 1           # Write parameter sets with every IRAP'
    	'#        Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict     deltaRPS' '#ref_idcs reference idcs'
    	print >> fid,''
      
        fid.write('#Stitching Frames in the Ref Picture set: Global Frame Values = %s\n' % Abs_ref_pics_Stitching_array_Distributed)
        fid.write('#Stitching Frames in the Ref Picture set: Relative to this GOP = %s\n' % ref_pics_Stitching_array_Distributed)
    	print >> fid,''

    	## Buidling encoding structure for Stitching mode
    	ref_pics_stitch_to_use_Distributed=[]
    	if 0 in ref_pics_Stitching_array_Distributed:
	    if num_ref_pics_active_Stitching_Distributed>0:
	        ref_pics_stitch_to_use_Distributed=np.append(ref_pics_stitch_to_use_Distributed,0)

    	ref_pics_Distributed=[]
    	for cnt in range(1,NumFrames_Distributed+1):
	   ref_pics_notstitch_to_use_Distributed=[]
	   ref_pics_old_Distributed=ref_pics_Distributed
	   ref_pics_Distributed=[]
	   reference_idcs_Distributed=[]
	   cnt2=cnt-1
	   ref_pics_Distributed=np.append(ref_pics_notstitch_to_use_Distributed,ref_pics_stitch_to_use_Distributed)
           #print(ref_pics_Distributed)
	   while len(ref_pics_notstitch_to_use_Distributed)<num_ref_pics_active_Max_Distributed-num_ref_pics_active_Stitching_Distributed:
	      ref_pics_notstitch_to_use_Distributed=np.append(ref_pics_notstitch_to_use_Distributed,cnt2)
	      ref_pics_Distributed=np.append(ref_pics_notstitch_to_use_Distributed,ref_pics_stitch_to_use_Distributed)
	      ref_pics_Distributed=np.unique(ref_pics_Distributed)
	      cnt2=cnt2-1
	   ref_pics_Distributed=np.sort(ref_pics_Distributed)
	   ref_pics_Distributed=ref_pics_Distributed[ref_pics_Distributed>=0]
	   ref_pics_Distributed=ref_pics_Distributed[::-1]
           #print(ref_pics_Distributed)

	   if cnt in ref_pics_Stitching_array_Distributed:
	      if len(ref_pics_stitch_to_use_Distributed) < num_ref_pics_active_Stitching_Distributed: 
	         ref_pics_stitch_to_use_Distributed=np.append(ref_pics_stitch_to_use_Distributed,cnt)
	
	   GOPLine='Frame' + str(cnt) + ': P '+ str(cnt) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(len(ref_pics_Distributed)) + ' ' + str(len(ref_pics_Distributed))
	   for cnt1 in range(len(ref_pics_Distributed)):
	      GOPLine=GOPLine+' '+str(int(ref_pics_Distributed[cnt1]-cnt))
	   if cnt == 1:
	      GOPLine=GOPLine+' 0'
	   else:	
	      GOPLine=GOPLine+' 2 0'
			
           print >> fid, GOPLine

	fid.write('\n#Note: The number of frames in the particitioned video is equal to GOP (Frame#0, Frame#1, .... Frame#(GOP-1)) and thus the line Frmae#GOP in this file will not be used to encode any frame, it is added to comply with the required format of HEVC GOP structure')
        fid.close()

###--------------------------------------------------------------
def Encode_decode_video(Distributed_GOP_Matrix):
    encoderlog=[]
    decoderlog=[]
    PcntCompleted=[]
    for Pcnt in range(np.shape(Distributed_GOP_Matrix)[0]):
    #for Pcnt in range(4):
         print('Encoding GOP#{} of {}'.format(Pcnt,(np.shape(Distributed_GOP_Matrix)[0]-1)))
         InputYUV='../Split_Video/Part{}/Part{}.yuv'.format(Pcnt,Pcnt)
         BitstreamFile='../Split_Video/Part{}/HMEncodedVideo.bin'.format(Pcnt)
         osout = call('rm -rf {}'.format(BitstreamFile))
         osout = call('cp -f ./encoder_HMS.cfg ../Split_Video/Part{}/encoder_HMS.cfg'.format(Pcnt))
    
         #print('./HMS/bin/TAppEncoderStatic -c ../Split_Video/Part{}/encoder_HMS.cfg -c ../Split_Video/Part{}/encoder_HMS_GOP_{}.cfg --InputFile={} --SourceWidth={} --SourceHeight={} --SAO=0 --QP={} --FrameRate={} --FramesToBeEncoded={} --MaxCUSize={} --MaxPartitionDepth={} --QuadtreeTULog2MaxSize=4 --BitstreamFile="{}" --RateControl={} --TargetBitrate={}'.format(Pcnt,Pcnt,Pcnt,InputYUV,Width,Height,QP,fps,GOP,MaxCUSize,MaxPartitionDepth,BitstreamFile,RateControl,Pcnt,rate))
    
         osout=call_bg('./HMS/bin/TAppEncoderStatic -c ../Split_Video/Part{}/encoder_HMS.cfg -c ../Split_Video/Part{}/encoder_HMS_GOP_{}.cfg --InputFile={} --SourceWidth={} --SourceHeight={} --SAO=0 --QP={} --FrameRate={} --FramesToBeEncoded={} --MaxCUSize={} --MaxPartitionDepth={} --QuadtreeTULog2MaxSize=4 --BitstreamFile="{}" --RateControl={} --TargetBitrate={} &'.format(Pcnt,Pcnt,Pcnt,InputYUV,Width,Height,QP,fps,GOP,MaxCUSize,MaxPartitionDepth,BitstreamFile,RateControl,Pcnt,rate))
         encoderlog.append(osout)
         PcntCompleted.append(Pcnt)
         if int(Pcnt % NProcesses) == 0 :
            for Pcnt2 in PcntCompleted:
		encoderlogfile='../Split_Video/Part{}/encoderlog.dat'.format(Pcnt2)
		fid = open(encoderlogfile,'w')
                fid.write(encoderlog[Pcnt2].stdout.read())
                fid.close
            PcntCompleted=[]

    for Pcnt2 in PcntCompleted:
         encoderlogfile='../Split_Video/Part{}/encoderlog.dat'.format(Pcnt2)
	 fid = open(encoderlogfile,'w')
         fid.write(encoderlog[Pcnt2].stdout.read())
         fid.close
    PcntCompleted=[]

    PcntCompleted=[]
    for Pcnt in range(np.shape(Distributed_GOP_Matrix)[0]):
    #for Pcnt in range(4):
         encoderlog[Pcnt].stdout.read()
         print('Decoding GOP#{} of {}'.format(Pcnt,(np.shape(Distributed_GOP_Matrix)[0]-1)))
         InputYUV='../Split_Video/Part{}/Part{}.yuv'.format(Pcnt,Pcnt)
         ReconFile='../Split_Video/Part{}/ReconPart{}.yuv'.format(Pcnt,Pcnt)
         BitstreamFile='../Split_Video/Part{}/HMEncodedVideo.bin'.format(Pcnt)
         osout = call('rm -rf {}'.format(ReconFile))
         
         #print('./HMS/bin/TAppDecoderStatic --BitstreamFile="{}" --ReconFile="{}" &'.format(BitstreamFile,ReconFile))
         osout=call_bg('./HMS/bin/TAppDecoderStatic --BitstreamFile="{}" --ReconFile="{}" &'.format(BitstreamFile,ReconFile))
         decoderlog.append(osout)
	 PcntCompleted.append(Pcnt)
         if int(Pcnt % NProcesses) == 0 :
            for Pcnt2 in PcntCompleted:
		decoderlogfile='../Split_Video/Part{}/decoderlog.dat'.format(Pcnt2)
		fid = open(decoderlogfile,'w')
                fid.write(decoderlog[Pcnt2].stdout.read())
                fid.close
            PcntCompleted=[]
   
    for Pcnt2 in PcntCompleted:
         decoderlogfile='../Split_Video/Part{}/decoderlog.dat'.format(Pcnt2)
	 fid = open(decoderlogfile,'w')
         fid.write(decoderlog[Pcnt2].stdout.read())
         fid.close
    PcntCompleted=[]
    return

###--------------------------------------------------------------
def Measure_Rate_PSNR(Distributed_GOP_Matrix):
    for Pcnt in range(np.shape(Distributed_GOP_Matrix)[0]):
    #for Pcnt in range(3):
         print('Measuring Rate and PSNR for GOP#{} of {}'.format(Pcnt,(np.shape(Distributed_GOP_Matrix)[0]-1)))
         InputYUV='../Split_Video/Part{}/Part{}.yuv'.format(Pcnt,Pcnt)
         ReconFile='../Split_Video/Part{}/ReconPart{}.yuv'.format(Pcnt,Pcnt)
         (osout,err)=call('python ./Quality/measure.py {} {} {} {} &'.format(InputYUV,ReconFile,Width,Height))
         encoderlogfile='../Split_Video/Part{}/encoderlog.dat'.format(Pcnt)
	 fid = open(encoderlogfile,'a')
         fid.write(osout)
         fid.close
    return

###--------------------------------------------------------------
def Combine_encoder_log(Distributed_GOP_Matrix):

    PIXEL_MAX = 255.0
    mseY=0
    mseU=0
    mseV=0
    mseYUV=0
    NumFramesPSNR=0

    NumFramesRate=0
    TotalBits=0

    CombinedLinesRate=[]
    CombinedLinesPSNR=[]
    CombinedLinesRateAll=[]
    CombinedLinesPSNRAll=[]
    for cnt_row in range(np.shape(Distributed_GOP_Matrix)[0]):
        cnt_col_Rate=0
        cnt_col_PSNR=0
        encoderlogfile='../Split_Video/Part{}/encoderlog.dat'.format(cnt_row)
        with open(encoderlogfile) as f:
             Lines = f.readlines()
        f.close()
        for cnt in range(len(Lines)):
            templine=(Lines[cnt][:]).rstrip()
            templine=templine.replace("  "," ")
            templine=templine.replace("  "," ")
            templine=templine.replace("  "," ")

            if templine.split(' ')[0] == 'POC':
               #print('{}   ...  {}'.format(cnt_row,cnt_col_Rate)) 
               CombinedLinesRateAll.append(Lines[cnt][:])
               if (Distributed_GOP_Matrix[cnt_row][cnt_col_Rate] > Distributed_GOP_Matrix[cnt_row-1][GOP-1]) or (cnt_row==0):   ## if new POC, not considered in previous GOPs
                    #print((templine).rstrip())
                    #print('{}'.format(templine.split(' ')[11]))
                    CombinedLinesRate.append(Lines[cnt][:])
                    cnt_col_Rate=cnt_col_Rate+1
                    TotalBits=TotalBits+int(templine.split(' ')[11])
                    NumFramesRate=NumFramesRate+1
               else:
                    cnt_col_Rate=cnt_col_Rate+1
       
            if (NumFramesRate>0):
               AverageRate=(TotalBits/NumFramesRate)*fps
            


            if (((re.split(' |:',templine)[0]) == 'Frame') and ((re.split(' |:',templine)[3]) == '[Y')):   
               CombinedLinesPSNRAll.append(Lines[cnt][:])
               if (Distributed_GOP_Matrix[cnt_row][cnt_col_PSNR] > Distributed_GOP_Matrix[cnt_row-1][GOP-1]) or (cnt_row==0):  ## if new frame, not considered in previous GOPs
                    PSNRYFrame=re.split(' |:',templine)[4]
                    PSNRUFrame=re.split(' |:',templine)[6]
                    PSNRVFrame=re.split(' |:',templine)[8]
                    PSNRYUVFrame=re.split(' |:',templine)[10]
          
                    PSNRYFrame=float(PSNRYFrame[0:(len(PSNRYFrame)-2)])
                    PSNRUFrame=float(PSNRUFrame[0:(len(PSNRUFrame)-2)])
                    PSNRVFrame=float(PSNRVFrame[0:(len(PSNRVFrame)-2)])
                    PSNRYUVFrame=float(PSNRYUVFrame[0:(len(PSNRYUVFrame)-3)])

                    mseYFrame=((PIXEL_MAX)/(10**(PSNRYFrame/20)))**2
                    mseY=mseY+mseYFrame

                    mseUFrame=((PIXEL_MAX)/(10**(PSNRUFrame/20)))**2
                    mseU=mseU+mseUFrame

                    mseVFrame=((PIXEL_MAX)/(10**(PSNRVFrame/20)))**2
                    mseV=mseV+mseVFrame

                    mseYUVFrame=((PIXEL_MAX)/(10**(PSNRYUVFrame/20)))**2
                    mseYUV=mseYUV+mseYUVFrame

                    NumFramesPSNR=NumFramesPSNR+1

                    PSNRYVideo=20 * math.log10(PIXEL_MAX / (math.sqrt(mseY/NumFramesPSNR)))
                    PSNRUVideo=20 * math.log10(PIXEL_MAX / (math.sqrt(mseU/NumFramesPSNR)))
                    PSNRVVideo=20 * math.log10(PIXEL_MAX / (math.sqrt(mseV/NumFramesPSNR)))
                    PSNRYUVVideo=20 * math.log10(PIXEL_MAX / (math.sqrt(mseYUV/NumFramesPSNR)))

                    templineNew=('Frame {0:3d}: [Y {1:1.4f}dB   U {2:1.4f}dB   V {3:1.4f}dB   YUV {4:1.4f}dB]  ..... Video: [Y {5:1.4f}dB   U {6:1.4f}dB   V {7:1.4f}dB   YUV {8:1.4f}dB]').format(NumFramesPSNR,PSNRYFrame,PSNRUFrame,PSNRVFrame,PSNRYUVFrame,PSNRYVideo,PSNRUVideo,PSNRVVideo,PSNRYUVVideo)
                    #print((Lines[cnt][:]).rstrip())
                    #print(templineNew.rstrip())
                    #print()
                    #print('{}..{}..{}..{}...Video...{}..{}..{}..{}'.format(PSNRYFrame,PSNRUFrame,PSNRVFrame,PSNRYUVFrame,PSNRYVideo,PSNRUVideo,PSNRVVideo,PSNRYUVVideo))
                    #print(re.split(' |:',templine)[1])
                    #print('{}   ...  {}'.format(cnt_row,cnt_col_PSNR)) 

                    CombinedLinesPSNR.append(templineNew)
                    cnt_col_PSNR=cnt_col_PSNR+1
               else:
                    cnt_col_PSNR=cnt_col_PSNR+1

## write to combined log file
    fid = open(Combined_encoder_log,'w')

    fid.write('Input File (MP4) = {}\n'.format(vid))
    fid.write('RankListFile = {}\n'.format(RankListFile))
    fid.write('Ref_active = {}\n'.format(num_ref_pics_active_Max))
    fid.write('Ref_stitch = {}\n'.format(num_ref_pics_active_Stitching))
    fid.write('QP = {}\n'.format(QP))
    fid.write('MaxCUSize = {}\n'.format(MaxCUSize))
    fid.write('MaxPartitionDepth = {}\n'.format(MaxPartitionDepth))
    fid.write('fps = {}\n'.format(fps))
    fid.write('RateControl = {}\n'.format(RateControl))
    fid.write('rate = {}\n'.format(rate))
    fid.write('NProcesses = {}\n\n'.format(NProcesses))


## write PSNR
    for cnt in range(len(CombinedLinesPSNR)):
       templine=CombinedLinesPSNR[cnt][:].replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.rstrip()
       templine=templine.split(' ')
       fid.write('Frame {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n'.format(cnt,str(templine[2]),str(templine[3]),str(templine[4]),str(templine[5]),str(templine[6]),str(templine[7]),str(templine[8]),str(templine[9]),str(templine[10]),str(templine[11]),str(templine[12]),str(templine[13]),str(templine[14]),str(templine[15]),str(templine[16]),str(templine[17]),str(templine[18]),str(templine[19])))

## write Rate
    fid.write('\n\n')
    for cnt in range(len(CombinedLinesRate)):
       templine=CombinedLinesRate[cnt][:].replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.split(' ')
       fid.write('POC {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n'.format(cnt,str(templine[2]),str(templine[3]),str(templine[4]),str(templine[5]),str(templine[6]),str(templine[7]),str(templine[8]),str(templine[9]),str(templine[10]),str(templine[11]),str(templine[12]),str(templine[13]),str(templine[14]),str(templine[15]),str(templine[16]),str(templine[17]),str(templine[18]),str(templine[19]),str(templine[20]),str(templine[21]),str(templine[22])))

    fid.write('\nNumber of Frames = {}\n'.format(NumFramesRate))
    fid.write('Written bites = {}\n'.format(TotalBits))
    fid.write('Bit Rate = {} kbps\n'.format(AverageRate/1000))

    fid.close


    fid = open((Combined_encoder_log[0:(len(Combined_encoder_log)-4)]+'All.dat'),'w')
    for cnt in range(len(CombinedLinesPSNRAll)):
       templine=CombinedLinesPSNRAll[cnt][:].replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.split(' ')
       #print('Frame {}...{}'.format(cnt,templine[2:10]))
       fid.write('Frame {} {} {} {} {} {} {} {} {}\n'.format(str(templine[1]),str(templine[2]),str(templine[3]),str(templine[4]),str(templine[5]),str(templine[6]),str(templine[7]),str(templine[8]),str(templine[9]),str(templine[10])))

    fid.write('\n\n')
    for cnt in range(len(CombinedLinesRateAll)):
       templine=CombinedLinesRateAll[cnt][:].replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.split(' ')
       #print('POC {}...{}'.format(cnt,templine[2:22]))
       fid.write('POC {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}\n'.format(str(templine[1]),str(templine[2]),str(templine[3]),str(templine[4]),str(templine[5]),str(templine[6]),str(templine[7]),str(templine[8]),str(templine[9]),str(templine[10]),str(templine[11]),str(templine[12]),str(templine[13]),str(templine[14]),str(templine[15]),str(templine[16]),str(templine[17]),str(templine[18]),str(templine[19]),str(templine[20]),str(templine[21]),str(templine[22])))


    fid.close

##################################################################
## Main Body
if __name__ == "__main__":
    args=main()

    ##Inputs
    RankListFile=args.ranklistfile;
    num_ref_pics_active_Max=int(args.num_ref_pics_active_max);
    num_ref_pics_active_Stitching=int(args.num_ref_pics_active_stitching);
    vid=args.vid;

    mode=args.mode;
    fps=int(args.fps);
    GOP=int(args.gop);
    Width=int(args.w);
    Height=int(args.h);
    QP=int(args.qp);
    MaxCUSize=int(args.maxcusize);
    MaxPartitionDepth=int(args.maxpartitiondepth);
    RateControl=int(args.ratecontrol);
    rate=int(args.rate);
    NProcesses=int(args.nprocesses);
    Combined_encoder_log=args.combined_encoder_log

    
    fsr=fps

    if GOP%2!=0:
        GOP=int(GOP/2) * 2

    if num_ref_pics_active_Stitching>num_ref_pics_active_Max:
        num_ref_pics_active_Stitching=num_ref_pics_active_Max
    
    if GOP<(2*num_ref_pics_active_Max):
        GOP=2*num_ref_pics_active_Max

    (iFNums,NumFrames)=read_ranklist();
    iFNums=np.array(iFNums)
    ref_pics_active_Stitching=iFNums[0:(num_ref_pics_active_Stitching)]
    ref_pics_active_Stitching=np.sort(ref_pics_active_Stitching)
    
    (Distributed_GOP_Matrix,ref_pics_in_Distributed_GOP_Matrix)=Create_Distributed_GOP_Matrix();
    export_frames(vid)
    Split_Video_GOP(Distributed_GOP_Matrix)
    Create_Encoder_Config(Distributed_GOP_Matrix,ref_pics_in_Distributed_GOP_Matrix)
    Encode_decode_video(Distributed_GOP_Matrix)
    Measure_Rate_PSNR(Distributed_GOP_Matrix)
    Combine_encoder_log(Distributed_GOP_Matrix)    

    #print(ref_pics_active_Stitching)
    #print(ref_pics_in_Distributed_GOP_Matrix)
    print(Distributed_GOP_Matrix)

