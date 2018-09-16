#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict deltaRPS #ref_idcs reference idcs
#print >> fid, 'Frame1:  P    1   5       -6.5                      0.2590         0          0          1.0   0            0               0           1                1         -1      0');
from __future__ import division
from numpy import *
import numpy as np
import cv2, os, sys, subprocess, pdb
import argparse
import ConfigParser
import time, re, datetime
import math
import matplotlib.pyplot as plt




FRMPERWIN = 1 ; INF = 999

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
def prepare_video(fn):
    osout = call('rm -rf ../CodecSIFT')
    osout = call('mkdir ../CodecSIFT')
    osout = call('mkdir ../CodecSIFT/pngall')
    osout = call('ffmpeg -r 1 -i {} -r 1 -qp 0 ../CodecSIFT/pngall/%d.png'.format(fn))
    osout = call('ffmpeg -start_number 0 -i ../CodecSIFT/pngall/%d.png -c:v libx264 -vf "fps=25,format=yuv420p" -qp 0 ../CodecSIFT/{}_CodecSIFT.mp4'.format(fnname))
    osout = call('ffmpeg -y -i ../CodecSIFT/{}_CodecSIFT.mp4 -vcodec rawvideo -pix_fmt yuv420p -qp 0 ../CodecSIFT/{}_CodecSIFT.yuv'.format(fnname,fnname))
    return

###--------------------------------------------------------------
## Building Configuration File
def Build_encoding_struct_stitch():
    
   iFNums=map(int, range(GOP+1))
   ## get total number of frames
   NumFrames=round(len(iFNums))
   NumFrames=int(NumFrames)

   ##write config files header
   fid = open('../CodecSIFT/encoder_HMS_GOP.cfg','w')
   print >> fid, '#======== Coding Structure ============='
   print >> fid, 'IntraPeriod                   : -1           # Period of I-Frame ( -1 = only first)'
   print >> fid, 'DecodingRefreshType           : 2           # Random Accesss 0:none, 1:CRA, 2:IDR, 3:Recovery Point SEI'
   print >> fid, 'GOPSize                       : '+str(GOP)+'           # GOP Size (number of B slice = GOPSize-1)'
   print >> fid, 'ReWriteParamSetsFlag          : 1           # Write parameter sets with every IRAP'
   '#        Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference pictures     predict     deltaRPS' '#ref_idcs reference idcs'
   print >> fid,''
   
   ## Produce iFNums_array2 [StitchFrame; other frames ordered]
   iFNums_array = np.array(iFNums)
   #iFNums_array=iFNums_array.clip(0, 999999999)
   #indexes = np.unique(iFNums_array, return_index=True)[1]
   #iFNums_array=[iFNums_array[index] for index in sorted(indexes)]
   #iFNums_array=np.array(iFNums_array)

   ref_pics_Stitching_array=np.array([StitchFrame])

   ref_pics_RemovedStitching_array=np.array(range(0,NumFrames))
   index=np.where(np.isin(ref_pics_RemovedStitching_array,ref_pics_Stitching_array))
   ref_pics_RemovedStitching_array=np.delete(ref_pics_RemovedStitching_array,index)

   ref_pics_RemovedStitching_array.sort()
   iFNums_array2=np.concatenate((ref_pics_Stitching_array,ref_pics_RemovedStitching_array), axis=0) #Stitching Frames + Ordered remaining Frames
   #print(iFNums_array2)

   ref_pics_active_Stitching=1
   ref_pics_active_Max=1
   ## Buidling encoding structure for Stitching mode
   ref_pics_stitch_to_use=[]
   if 0 in ref_pics_Stitching_array:
	if ref_pics_active_Stitching>0:
		ref_pics_stitch_to_use=np.append(ref_pics_stitch_to_use,0)

   ref_pics=np.array([StitchFrame])
   GOPLine='Frame' + str(1) + ': I '+ str(StitchFrame) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(0) + ' ' + str(0)+' '+str(int(0))
   print >> fid, GOPLine

   cntin=1
   for cnt in range(1,NumFrames):
      if cnt != StitchFrame:
         GOPLine='Frame' + str(cnt+cntin) + ': P '+ str(cnt) +' 0 -6.5 0.2590 0 0 1.0 0 0 0 '+ str(len(ref_pics)) + ' ' + str(len(ref_pics))
	 for cnt1 in range(len(ref_pics)):
	    GOPLine=GOPLine+' '+str(int(ref_pics[cnt1]-cnt))
	    GOPLine=GOPLine+' 2 0'
	 print >> fid, GOPLine
      else:
         cntin=0

###--------------------------------------------------------------
def Encode_decode_video():
    print('Encoding Video')
    InputYUV='../CodecSIFT/{}_CodecSIFT.yuv'.format(fnname)
    BitstreamFile='../CodecSIFT/{}_CodecSIFT.bin'.format(fnname)
    ReconFile='../CodecSIFT/{}_CodecSIFT_Recon.yuv'.format(fnname)

    osout = call('rm -rf {}'.format(BitstreamFile))
    osout = call('cp -f ./encoder_HMS.cfg ../CodecSIFT/encoder_HMS.cfg')
    if RateControl==0:
        osout=call_bg('./HMS/bin/TAppEncoderStatic -c ../CodecSIFT/encoder_HMS.cfg -c ../CodecSIFT/encoder_HMS_GOP.cfg --InputFile={} --SourceWidth={} --SourceHeight={} --SAO=0 --QP={} --FrameRate={} --FramesToBeEncoded={} --MaxCUSize={} --MaxPartitionDepth={} --QuadtreeTULog2MaxSize=4 --BitstreamFile="{}" --RateControl={} --TargetBitrate={} &'.format(InputYUV,Width,Height,QP,fps,GOP,MaxCUSize,MaxPartitionDepth,BitstreamFile,RateControl,rate))
    else:
        osout=call_bg('./HMS/bin/TAppEncoderStatic -c ../CodecSIFT/encoder_HMS.cfg -c ../CodecSIFT/encoder_HMS_GOP.cfg --InputFile={} --SourceWidth={} --SourceHeight={} --SAO=0 --QP={} --FrameRate={} --FramesToBeEncoded={} --MaxCUSize={} --MaxPartitionDepth={} --QuadtreeTULog2MaxSize=4 --BitstreamFile="{}" --RateControl={} --TargetBitrate={} &'.format(InputYUV,Width,Height,QP,fps,GOP*alpha,MaxCUSize,MaxPartitionDepth,BitstreamFile,RateControl,rate))
    encoderlogfile='../CodecSIFT/encoderlog.dat'
    fid = open(encoderlogfile,'w')
    fid.write(osout.stdout.read())
    fid.close
    osout.stdout.read()
    
    print('Decoding Video')
    osout = call('rm -rf {}'.format(ReconFile))
    osout=call_bg('./HMS/bin/TAppDecoderStatic --BitstreamFile="{}" --ReconFile="{}" &'.format(BitstreamFile,ReconFile))
    decoderlogfile='../CodecSIFT/decoderlog.dat'
    fid = open(decoderlogfile,'w')
    fid.write(osout.stdout.read())
    fid.close
    return

###--------------------------------------------------------------
def Measure_Rate_PSNR():
    InputYUV='../CodecSIFT/{}_CodecSIFT.yuv'.format(fnname)
    ReconFile='../CodecSIFT/{}_CodecSIFT_Recon.yuv'.format(fnname)

    (osout,err)=call('python ./Quality/measure.py {} {} {} {} &'.format(InputYUV,ReconFile,Width,Height))
    encoderlogfile='../CodecSIFT/encoderlog.dat'
    fid = open(encoderlogfile,'a')
    fid.write(osout)
    fid.close
    return

###--------------------------------------------------------------
def Edit_encoder_log():

    PIXEL_MAX = 255.0
    mseY=0
    mseU=0
    mseV=0
    mseYUV=0
    NumFramesPSNR=0

    NumFramesRate=0
    TotalBits=0
    
    CombinedLinesRateAll=[]
    CombinedLinesPSNRAll=[]
    CombinedLinesRate=[]
    CombinedLinesPSNR=[]
    encoderlogfile='../CodecSIFT/encoderlog.dat'
    with open(encoderlogfile) as f:
       Lines = f.readlines()
    f.close()
   
    cnt_col_Rate=0
    cnt_col_PSNR=0
    for cnt in range(len(Lines)):
       templine=(Lines[cnt][:]).rstrip()
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")
       templine=templine.replace("  "," ")

       if templine.split(' ')[0] == 'POC':
           #print('{}   ...  {}'.format(cnt_row,cnt_col_Rate)) 
           CombinedLinesRateAll.append(Lines[cnt][:])
           CombinedLinesRate.append(Lines[cnt][:])
           cnt_col_Rate=cnt_col_Rate+1
           TotalBits=TotalBits+int(templine.split(' ')[11])
           NumFramesRate=NumFramesRate+1
           if (NumFramesRate>0):
               AverageRate=(TotalBits/NumFramesRate)*fps
            


       if (((re.split(' |:',templine)[0]) == 'Frame') and ((re.split(' |:',templine)[3]) == '[Y')):   
           CombinedLinesPSNRAll.append(Lines[cnt][:])
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
           CombinedLinesPSNR.append(templineNew)
           cnt_col_PSNR=cnt_col_PSNR+1
       
## write to edited log file
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


###################################################################3
## check similarity using SIFT
def call_err(cmd):
    # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
    proc = subprocess.Popen(cmd, \
                   stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return (out, err)

def get_frames_list(fn):
    osout = call_err('ls -v ../CodecSIFT/pngall/*.png') ; lfrmall = osout[0]
    lfrmall = lfrmall.split('\n')[0:-1]
    
    osout = call_err('rm -rf ../CodecSIFT/pngDS')
    osout = call_err('mkdir ../CodecSIFT/pngDS')
    for cnt in range(len(lfrmall)):
        if ((cnt) % (fps/fsr)) == 0:
             osout = call_err('cp -rf ../CodecSIFT/pngall/{}.png ../CodecSIFT/pngDS/{}.png'.format((cnt+1),int((cnt/(fps/fsr))+1)))
 
    osout = call_err('ls -v ../CodecSIFT/pngDS/*.png') ; lfrm = osout[0]
    lfrm = lfrm.split('\n')[0:-1]
    return lfrm

def make_windows(lfrm, numfrmwin):
    numfrm = len(lfrm) ; numwin = numfrm/numfrmwin
    lwin = []
    for i in range(0, numfrm, numfrmwin ): lwin.append(lfrm[i:i+numfrmwin])
    return lwin

def comp_similarity(lwin_,lwin_sc_,lwinsim):
    for win in lwin_:
        now = datetime.datetime.now()
        #print('{} ... {}').format(win,now.strftime("%Y-%m-%d %H:%M:%S"))
        for win_sc in lwin_sc_:
          s=re.split('/',str(win))[-1]
          iwin=int(s[0:(len(s)-6)])

          s=re.split('/',win_sc)[-1]
          iwin_sc=int(s[0:(len(s)-4)])
          lwinsim[iwin-1][iwin_sc-1]=window_similarity(win, win_sc)
	  #print('{}..&..{}=..{}').format(win,win_sc,lwinsim[iwin-1][iwin_sc-1])
    return lwinsim

def window_similarity(win_0, win_1):
    lfrmsim = []
    if (type(win_0) == str and type(win_1) == str):
       lfrmsim.append(content_similarity(win_0, win_1))
    elif (type(win_0) == str and type(win_1) <> str):
       lfrmsim.append(content_similarity(win_0, win_1[0]))
    elif (type(win_0) <> str and type(win_1) == str):
       lfrmsim.append(content_similarity(win_0[0], win_1))
    else:
       lfrmsim.append(content_similarity(win_0[0], win_1[0]))
        
    return np.mean(lfrmsim)

def content_similarity(img_0, img_1):
    
    img1 = cv2.imread(img_0, 0)
    img2 = cv2.imread(img_1, 0)

    # Initiate SIFT detector
    orb = cv2.ORB_create()
    #orb = cv2.ORB()
    #print("{} ...... {}\n").format(img_0,img_1)

    # find the keypoints and descriptors with SIFT
    kp1, des1 = orb.detectAndCompute(img1,None)
    kp2, des2 = orb.detectAndCompute(img2,None)

    if (type(des1)==type(des2)):
    	# create BFMatcher object
    	bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    	# Match descriptors.
    	matches = bf.match(des1,des2)
    	#pdb.set_trace()
        #print("simind_1 matches={}").format(matches)

    	# Sort them in the order of their distance.
    	matches   = sorted(matches, key = lambda x:x.distance)
    	distances = [ _.distance for _ in matches]
    	simind_1    =  np.mean(distances)
    	#print("simind_1={}\n").format(simind_1)
     
        if math.isnan(simind_1):
          simind_1=1000

        simind_2=simind_1
    	simind = (simind_1 + simind_2)/float(2)
    else:
        simind=1000
    return simind

##################################################################
## Main Body
if __name__ == "__main__":
    np.set_printoptions(threshold='nan')
    args=main()

    ##Inputs
    StitchFrame=int(args.stitchframe);
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
    alpha=float(args.alpha)  ##rate control factor to avoid degradation of rate/PSNR at the end of the GOP.
    
    fsr=fps
    fnname=vid.split('/')[-1]
    fnname=fnname[0:(len(fnname)-4)]

    if GOP%2!=0:
        GOP=int(GOP/2) * 2

    if num_ref_pics_active_Stitching>num_ref_pics_active_Max:
        num_ref_pics_active_Stitching=num_ref_pics_active_Max
    
    if GOP<(2*num_ref_pics_active_Max):
        GOP=2*num_ref_pics_active_Max

    #prepare_video(vid)
    #Build_encoding_struct_stitch()
    #Encode_decode_video()
    #Measure_Rate_PSNR()
    #Edit_encoder_log()    


    fname=fnname
    
    lfrm = get_frames_list(vid);
    lwin = make_windows(lfrm, FRMPERWIN)
    lwinsim=np.full((len(lwin),len(lwin)), INF)
    lwin_stitch=lwin[StitchFrame-1]
    lwinsim=comp_similarity(lwin,lwin_stitch,lwinsim)


    s=re.split('/',str(lwin_stitch))[-1]
    lwinsim=np.array(lwinsim)
    SIFT_score=lwinsim[:,int(s[0:(len(s)-6)])-1]
    SIFT_score_Norm=SIFT_score/np.max(SIFT_score)
   
    plt.plot(range(len(SIFT_score_Norm)),SIFT_score_Norm)
    plt.title('average SIFT Score')
    plt.xlabel('Frame Number')
    plt.ylabel('Average SIFT Score')
    plt.legend(['SIFT'])
    plt.show()


