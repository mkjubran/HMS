import numpy as np
import os,sys, subprocess, pdb
import datetime, math
import argparse
import random
import ntpath

from os import listdir
from os.path import isfile, join   
from random import randint

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--input_dir', type=str,
                    help='videos input dir')

parser.add_argument('--output_dir', type=str,
                    help='videos output dir')

parser.add_argument('--output_filename', type=str,
                    help='videos output filename')

parser.add_argument('--infps', type=int,
                    help='input frames per second')

parser.add_argument('--outfps', type=int,
                    help='output frames per second')

parser.add_argument('--fsr', type=int,
                    help='frames sampling rate')

parser.add_argument('--W', type=int,
                    help='video width')

parser.add_argument('--H', type=int,
                    help='video hight')

parser.add_argument('--vidd', type=int,
                    help='video duration in minutes')

parser.add_argument('--ctmin', type=int,
                    help='minimum duration of video clip in seconds')

parser.add_argument('--ctmax', type=int,
                    help='maximum duration of video clip in seconds')


args = parser.parse_args()

##Inputs
input_dir=args.input_dir;
output_dir=args.output_dir;
output_filename=args.output_filename;
infps=args.infps;
outfps=args.outfps;
fsr=args.fsr;
width=args.W;
hight=args.H;
vidd=args.vidd;
ctmin=args.ctmin
ctmax=args.ctmax

def call(cmd):
    # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
    proc = subprocess.Popen(cmd, \
                   stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return (out, err)

if __name__ == '__main__':
    
    inputvideofilesOrig = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
    randIdx=random.sample(range(0, len(inputvideofilesOrig)), len(inputvideofilesOrig))
   
    inputvideofiles=[]
    for Idx in randIdx:
        inputvideofiles.append(inputvideofilesOrig[Idx])
  
    cnt=0
    clipslen=np.random.randint(ctmin, ctmax,len(inputvideofiles))
    while (clipslen.sum()/60 < vidd):
        clipslen=np.random.randint(ctmin, ctmax+1,len(inputvideofiles))
        cnt=cnt+1
        if (cnt > 9999):
            print('requested video duration can not be achieved, increase ctmax or add more video clips')
            break
    
    #print(clipslen)
   
    osout = call('rm -rf {}/cropped/'.format(output_dir))
    osout = call('mkdir {}/cropped/'.format(output_dir))
    input_dir_cropped=output_dir+'/cropped/'
    for cnt in range(len(clipslen)):
        clipname=inputvideofiles[cnt]
        osout = call('ffmpeg -y -i {}/{} -ss 00:00:00  -t {} {}/{}'.format(input_dir,clipname,str(datetime.timedelta(seconds=clipslen[cnt])),input_dir_cropped,clipname))

    thefile = open('concat_clips_temp.txt', 'w')
    for videofile in inputvideofiles:
        thefile.write("file '{}/{}'\n".format(input_dir_cropped,videofile))
    thefile.close() 

    osout = call('rm {}/output_temp.mp4'.format(output_dir))
    osout = call('ffmpeg -f concat  -safe 0 -i concat_clips_temp.txt -c copy {}/output_temp.mp4'.format(output_dir))

    osout = call('rm {}/{}.mp4'.format(output_dir,output_filename))
    osout = call('ffmpeg -y -r {} -i {}/output_temp.mp4 -strict -2 -vf scale={}:{} -c:v libx264 -preset ultrafast -r {} -qp 0 {}/{}.mp4 -hide_banner'.format(infps,output_dir,width,hight,outfps,output_dir,output_filename))
   
    osout = call('rm {}/{}.yuv'.format(output_dir,output_filename))
    osout = call('ffmpeg -y -i {}/{}.mp4 -vcodec rawvideo -pix_fmt yuv420p {}/{}.yuv'.format(output_dir,output_filename,output_dir,output_filename))
    print('{}/{}.mp4 is generated'.format(output_dir,output_filename))
    print('{}/{}.yuv is generated'.format(output_dir,output_filename))

