## --nrps=1 --gop=4 --crf=40 --override='yes' --in_dir= --out_dir=
import os, sys, subprocess
import pdb
import re
import argparse
import numpy as np
import multiprocessing

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

procs = 16   # Number of processes to create

gop_length = 4;
nrps = 1;
crf = 40;
in_dir = './mp4s_HD';
out_dir = './train_frames';
override = 'y'

# Optional argument
parser.add_argument('--nrps', type=int,
                    help='size of nrps, nrps=0 means all I frames')

parser.add_argument('--gop', type=int,
                    help='Size of GOP')

parser.add_argument('--crf', type=int,
                    help='CRF')

parser.add_argument('--out_dir', type=str,
                    help='Output Directory')

parser.add_argument('--in_dir', type=str,
                    help='Input Directory')

parser.add_argument('--override', type=str,
                    help='Override training data [y/Y or n/N]')

#parser.add_argument('--hms', type=int,
#                    help='Stitch Frame')

args = parser.parse_args()




f= open("task_completed.txt","w+")
f.write("task started\n")
f.close()


gop_length=args.gop;
nrps=args.nrps;
crf=args.crf;
input_dir=args.in_dir;
out_dir=args.out_dir;
override=args.override;
#FrameStitching=args.hms;

# load size of frames from stitching
#x=np.load('./tmp_HMS/toptr2s6r_640480_Rate_PSNR_ORB_{}.npy'.format(FrameStitching));
#size=np.true_divide(x[:,1], 8)

# Code for pre processing:
# ffmpeg -i sintel.mp4  -crf 16 -bf 0 sintel_2.mp4

def call(cmd):
   print(cmd)
   return subprocess.check_output(cmd, shell=True)


# Returns gop per P frame .. will probably not be used
def predictors_ip_gop(frame_type, gop_length):
   last_i_frame = 0
   frame_predictors = []
   for i in range(len(frame_type)):
      if frame_type[i] == 'I':
         frame_predictors.append([])
         last_i_frame = i

      if frame_type[i] == 'P':
         frame_predictors.append(range(last_i_frame, last_i_frame + gop_length))
       
   return frame_predictors

# to speed up generation of montage pngs for stitchframes
def produceStitch_Framei(f_count,pr_count):
   ii=f_count+pr_count
   for FrameStitching in range(1,len(frame_size),12):
      fo = '{}_{}_SF{}_{}.png'.format(format(int(frame_size[ii]), '010d'), format(int(Frame[ii]),'05d'), FrameStitching,filename[:-4])
      if frame_type[ii] != 'G':
          # Note: ii+1 because ffmpeg frame indices START FROM 1
          if ( nrps == 1):
             #-- nrps=1
             cmd = 'montage tmp/{}.png tmp_e/{}.png tmp_e/{}.png  -tile 3x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(int(Frame[ii]),'05d'), format(int(FrameStitching),'05d'), format(int(Frame[ii]),'05d'),out_dir,fo)
             output = call(cmd)
          else:
             print('No montage command for nrps={}'.format(nrps))

###--------------------------------------------------------------
#To extract the encoding data from coding log file ()
def produce_training_data(finfo):
    with open(finfo) as fi:
       lines = fi.readlines()
    for cnt in range(len(lines)):
       line = re.sub(' +', ' ', lines[cnt]).lstrip().split(' ')
       POC.append(line[0])
       POCtype.append(line[1])
       Frame.append(str(int(line[0])+1)) ## Frame=POC+1
       Bits.append(int(line[2])/8)
       L0 = re.sub(' +', ' ', lines[cnt]).split('L0')[1].split(' ')[1:-1]
       L1 = re.sub(' +', ' ', lines[cnt]).split('L1')[1].split(' ')[1:-1]

       L0 = list(set(L0));
       L1 = list(set(L1));

       #L0 = [ elem for elem in L0 if elem != '-1' ]
       #L1 = [ elem for elem in L1 if elem != '-1' ]
      
       L0 = [ str(int(elem)+1) for elem in L0 if elem != '-1' ]
       L1 = [ str(int(elem)+1) for elem in L1 if elem != '-1' ]

       while len(L0)<nrps:
         L0.append(L0[-1])

       while len(L1)<nrps:
         L1.append(L1[-1])

       L0_predictors.append(L0)
       L1_predictors.append(L1)
    return

# Prepare output dir ..
if (( override == 'Y') or (override == 'y')):
    cmd = 'rm -rf {}'.format(out_dir) ; output = call(cmd)

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

#if not os.path.exists('{}_tmp'.format(input_dir)):
#    os.makedirs('{}_tmp'.format(input_dir))

#if not os.path.exists('{}_corrupted'.format(input_dir)):
#    os.makedirs('{}_corrupted'.format(input_dir))

#cmd = 'mkdir  {}'.format(out_dir) ; output = call(cmd)

for filename in os.listdir(input_dir):
    if filename.endswith(".mp4"): 

         # define global variable
         Bits=[]
         POC=[]
         POCtype=[]
         Frame=[]
         L0_predictors=[]
         L1_predictors=[]

         # Clean dir ..
         cmd = 'rm -rf tmp' ; output = call(cmd)
         cmd = 'mkdir  tmp' ; output = call(cmd)
         cmd = 'rm -rf tmp_e' ; output = call(cmd)
         cmd = 'mkdir  tmp_e' ; output = call(cmd)
         cmd = 'rm -f tmp_e.mp4' ; output = call(cmd)

         cmd = 'rm -rf x265LC_InfoPerFrame.txt'; output = call(cmd)

         #try:
         if ( 1 == 1 ):
           # Make x and x_e; modify encoding as necessary ..  (e.g., adjust CRF/B-frames/etc)
           #cmd = 'ffmpeg -i {}/{} -crf 25 tmp_e.mp4'.format(input_dir, filename)
           if ( nrps == 0 ):
              cmd = '../../ffmpeg/ffmpeg -i {}/{} -c:v libx265 -x265-params "preset=superfast:crf={}:bframes=0:ref=1:keyint=1:no-open-gop=1" tmp_e.mp4'.format(input_dir, filename,crf, nrps)
              output = call(cmd)
           else:
              cmd = '../../ffmpeg/ffmpeg -i {}/{} -c:v libx265 -x265-params "preset=superfast:crf={}:bframes=0:ref={}" tmp_e.mp4'.format(input_dir, filename,crf, nrps)
              output = call(cmd)

           cmd = 'ffmpeg -i {}/{}  tmp/%5d.png'.format(input_dir, filename)
           output = call(cmd)

           cmd = 'ffmpeg -i tmp_e.mp4 tmp_e/%5d.png'
           output = call(cmd)

           #cmd = 'ffprobe -show_entries frame=pkt_size,pict_type tmp_e.mp4'
           #output = call(cmd)

           # Parse necessary info ..
           #frame_string = [_.replace('[/FRAME]','') for _ in output.split(b'[FRAME]')]
           #frame_size = [int(_.split('\n')[1].split('=')[1]) for _ in frame_string[1:]]
           #frame_type = [_.split('\n')[2].split('=')[1] for _ in frame_string[1:]]
           #frame_predictors = predictors_ip_gop(frame_type,gop_length)
           # [_.split('\n')[2].split('=')[1] for _ in frame_strings[1:]]

           produce_training_data('x265LC_InfoPerFrame.txt')
           frame_size=Bits;
           frame_type=POCtype;
           frame_predictors=L0_predictors;

           #pdb.set_trace()
           #Output preprocessed model inputs
           print('Output for {}'.format(filename))
           for i in range(0,len(frame_size),48*procs):
              jobs = []
              for k in range(0,48*procs,12):
                out_list = list()
                process = multiprocessing.Process(target=produceStitch_Framei,args=(i,k))
                jobs.append(process)

              # Start the processes (i.e. calculate the random number lists)      
              for j in jobs:
                j.start()

              # Ensure all of the processes have finished
              for j in jobs:
                j.join()

#            for FrameStitching in range(1,len(frame_size)):
#             #print('{}   {}\n'.format(i,frame_type));
#             fo = '{}_{}_SF{}_{}.png'.format(format(int(frame_size[i]), '010d'), format(int(Frame[i]),'05d'), FrameStitching,filename[:-4])
#             if frame_type[i] != 'G':
#                # Note: i+1 because ffmpeg frame indices START FROM 1
#                #fo = '{}_{}_{}.png'.format(format(frame_size[i], '05d'), format(int(Frame[i]),'05d'), filename[:-4])
#                if ( nrps == 1):
#                  #-- nrps=1
#                  cmd = 'montage tmp/{}.png tmp_e/{}.png tmp_e/{}.png  -tile 3x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(int(Frame[i]),'05d'), format(int(FrameStitching),'05d'), format(int(Frame[i]),'05d'),out_dir,fo)
#                  output = call(cmd)
#                else:
#                  print('No montage command for nrps={}'.format(nrps))
#             elif ( nrps == 0):
#               cmd = 'montage tmp/{}.png tmp_e/{}.png -tile 2x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(i+1,'05d'), format(i+1,'05d'),out_dir,fo)
#               output = call(cmd)
#             else:
#               print('Frame type is {} and no montage command for nrps={}'.format(frame_type[i],nrps))

    else:
        continue


f= open("task_completed.txt","w+")
f.write(args)
f.close()
