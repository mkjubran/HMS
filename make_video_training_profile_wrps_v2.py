import os, sys, subprocess
import pdb
import re
import argparse


# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

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

args = parser.parse_args()

gop_length=args.gop;
nrps=args.nrps;
crf=args.crf;
input_dir=args.in_dir;
out_dir=args.out_dir;
override=args.override;

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

if not os.path.exists('{}_tmp'.format(input_dir)):
    os.makedirs('{}_tmp'.format(input_dir))

if not os.path.exists('{}_corrupted'.format(input_dir)):
    os.makedirs('{}_corrupted'.format(input_dir))

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

         try:
         #if (1 == 1):
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
           # for i in range(len(frame_type)):
           frame_skip = 10
           for i in range(0, len(frame_type), frame_skip):
             #print('{}   {}\n'.format(i,frame_type));
             fo = '{}_{}_{}.png'.format(format(frame_size[i], '010d'), format(int(Frame[i]),'05d'), filename[:-4])
             if frame_type[i] != 'I':
                # Note: i+1 because ffmpeg frame indices START FROM 1
                #fo = '{}_{}_{}.png'.format(format(frame_size[i], '05d'), format(int(Frame[i]),'05d'), filename[:-4])
                if ( nrps == 4):
                  #-- nrps=4
                  cmd = 'montage tmp/{}.png tmp_e/{}.png tmp_e/{}.png tmp_e/{}.png tmp_e/{}.png tmp_e/{}.png -tile 6x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(int(Frame[i]),'05d'), format(int(Frame[i]),'05d'), format(int(frame_predictors[i][0]),'05d'),format(int(frame_predictors[i][1]),'05d'),format(int(frame_predictors[i][2]),'05d'), format(int(frame_predictors[i][3]),'05d'),out_dir,fo)
                  output = call(cmd)
                elif ( nrps == 2 ):
                  #-- nrps=2
                  cmd = 'montage tmp/{}.png tmp_e/{}.png tmp_e/{}.png tmp_e/{}.png -tile 4x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(int(Frame[i]),'05d'), format(int(Frame[i]),'05d'), format(int(frame_predictors[i][0]),'05d'),format(int(frame_predictors[i][1]),'05d'),out_dir,fo)
                  output = call(cmd)
                elif ( nrps == 1 ):
                  #-- nrps=1
                  cmd = 'montage tmp/{}.png tmp_e/{}.png tmp_e/{}.png  -tile 3x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(int(Frame[i]),'05d'), format(int(Frame[i]),'05d'), format(int(frame_predictors[i][0]),'05d'),out_dir,fo)
                  output = call(cmd)
                else:
                  print('No montage command for nrps={}'.format(nrps))
             elif ( nrps == 0):
               cmd = 'montage tmp/{}.png tmp_e/{}.png -tile 2x1 -font DejaVu-Sans -geometry +0+0 PNG24:{}/{}'.format(format(i+1,'05d'), format(i+1,'05d'),out_dir,fo)
               output = call(cmd)
             else:
               print('Frame type is {} and no montage command for nrps={}'.format(frame_type[i],nrps))

           cmd = 'mv {}/{} {}_tmp/{}'.format(input_dir,filename,input_dir,filename)
           out = call(cmd)
         #else:
         except:
           cmd = 'mv {}/{} {}_corrupted/{}'.format(input_dir,filename,input_dir,filename)
           out = call(cmd)
    else:
        continue

