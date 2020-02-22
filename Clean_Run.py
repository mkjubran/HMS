import os, subprocess
import argparse

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')


# Optional argument
parser.add_argument('--in_dir', type=str,
                    help='Input Directory')

args = parser.parse_args()

in_dir=args.in_dir

def call(cmd):
   print(cmd)
#   return
   return subprocess.check_output(cmd, shell=True)


print('rate_{}.txt'.format(in_dir))
with open('rate_{}.txt'.format(in_dir)) as f:
    content = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content = [x.strip() for x in content] 

if not os.path.isdir('./preproc/{}_Completed'.format(in_dir)):
    call('mkdir ./preproc/{}_Completed'.format(in_dir))

for filename in content:
    f = '{}.png'.format(filename.split(' ')[0])
    if os.path.exists('./preproc/{}/{}'.format(in_dir,f)):
       call('mv ./preproc/{}/{} ./preproc/{}_Completed/.'.format(in_dir,f,in_dir))
