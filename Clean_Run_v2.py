import os, subprocess
import argparse


# Search parameter ..
LABEL="logs_A_256_Train_Kinetics_640_480_CRF40_RPS1_x_xp_Test_640_480_stitching_x_xp_10d"
RPS="1"
lr=0.00002
EPOCH_STEP="1"

#input_dir="BrinkShort_640480_train_frames_640_480_x_xp_10d_skip12_P6"



# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')


# Optional argument
parser.add_argument('--in_dir', type=str,
                    help='Input Directory')

parser.add_argument('--gpu', type=int,
                    help='Input Directory')

args = parser.parse_args()

in_dir=args.in_dir
GPU=args.gpu

def call(cmd):
   print(cmd)
   return subprocess.check_output(cmd, shell=True)




if os.path.exists(in_dir) and os.path.isdir(in_dir):
    if not os.listdir(in_dir):
        print("Directory is empty")
    else:
        print("Directory is not empty")
else:
    print("Given Directory don't exists")

in_dir = in_dir.rstrip()
in_path = in_dir[:]
path, file = os.path.split(in_dir)
if file=='':
   in_dir=path.split('/')[-1]
else:
   in_dir=file

print(in_dir)

cnt=0
while os.listdir(in_path) and (cnt < 3):
   cnt=cnt+1
   if os.path.exists('./rate_{}.txt'.format(in_dir)):
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


   ## Run the rate predict model
   if GPU == 0:
      if os.path.exists('./rate_{}.txt'.format(in_dir)):
         call('mv -f rate_{}.txt rate.txt'.format(in_dir));
      try:
         call('python3 run_with_predicted_rates_256.py --gpu 0 --lr 0 --rps_size 1 --mode test --l1_weight 10 --output_dir {} --max_epochs 1 --checkpoint {} --input_dir ./preproc/{} --which_direction AtoB'.format(LABEL,LABEL,in_dir));
      finally:
         call('mv -f rate.txt rate_{}.txt'.format(in_dir))
   elif GPU == 1:
      if os.path.exists('./rate_{}.txt'.format(in_dir)):
         call('mv -f rate_{}.txt rate_2.txt'.format(in_dir));
      try:
         call('python3 run_with_predicted_rates_256_2.py --gpu 1 --lr 0 --rps_size 1 --mode test --l1_weight 10 --output_dir {} --max_epochs 1 --checkpoint {} --input_dir ./preproc/{} --which_direction AtoB'.format(LABEL,LABEL,in_dir));
      finally:
         call('mv -f rate_2.txt rate_{}.txt'.format(in_dir))
   else:
      print('GPU must be 0 or 1')

