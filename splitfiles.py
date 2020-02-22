import os, subprocess
import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')


# Optional argument
parser.add_argument('--in_dir', type=str,
                    help='Input Directory')

parser.add_argument('--out_dir', type=str,
                    help='Output Directory')

args = parser.parse_args()

in_dir=args.in_dir
out_dir=args.out_dir

def call(cmd):
#   print(cmd)
   return subprocess.check_output(cmd, shell=True)


FileCountMax=150000
FileCount=0
DirCount=0
for filename in os.listdir(in_dir):
    f = os.path.basename(filename)
#    print(f)
    if (FileCount > FileCountMax) or (DirCount == 0):
        DirCount+=1
        call('rm -rf  {}_P{}'.format(out_dir,DirCount))
        call('mkdir {}_P{}'.format(out_dir,DirCount))
        FileCount=0
        call('cp -rf {}/{} {}_P{}/.'.format(in_dir,f,out_dir,DirCount))
        print('cp -rf {}/{} {}_P{}/.'.format(in_dir,f,out_dir,DirCount))
        FileCount+=1
    else:
        call('cp -rf {}/{} {}_P{}/.'.format(in_dir,f,out_dir,DirCount))
        FileCount+=1
