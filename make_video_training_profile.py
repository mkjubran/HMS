import os, sys, subprocess
import pdb


gop_length = 4
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



input_dir = sys.argv[-1]

# Prepare output dir ..
cmd = 'rm -rf train_frames' ; output = call(cmd)
cmd = 'mkdir  train_frames' ; output = call(cmd)
for filename in os.listdir(input_dir):
    if filename.endswith(".mp4"): 

         # Clean dir ..
         cmd = 'rm -rf tmp' ; output = call(cmd)
         cmd = 'mkdir  tmp' ; output = call(cmd)
         cmd = 'rm -rf tmp_e' ; output = call(cmd)
         cmd = 'mkdir  tmp_e' ; output = call(cmd)
         cmd = 'rm -f tmp_e.mp4' ; output = call(cmd)



         # Make x and x_e; modify encoding as necessary ..  (e.g., adjust CRF/B-frames/etc)
         cmd = 'ffmpeg -i {}/{} -crf 25 tmp_e.mp4'.format(input_dir, filename)
         output = call(cmd)

         cmd = 'ffmpeg -i {}/{}  tmp/%5d.png'.format(input_dir, filename)
         output = call(cmd)

         cmd = 'ffmpeg -i tmp_e.mp4 tmp_e/%5d.png'
         output = call(cmd)

         cmd = 'ffprobe -show_entries frame=pkt_size,pict_type tmp_e.mp4'
         output = call(cmd)


         # Parse necessary info ..
         frame_string = [_.replace('[/FRAME]','') for _ in output.split(b'[FRAME]')]
         frame_size = [int(_.split('\n')[1].split('=')[1]) for _ in frame_string[1:]]
         frame_type = [_.split('\n')[2].split('=')[1] for _ in frame_string[1:]]
         frame_predictors = predictors_ip_gop(frame_type,gop_length)
         # [_.split('\n')[2].split('=')[1] for _ in frame_strings[1:]]

         # Output preprocessed model inputs
         print('Output for {}'.format(filename))
         # for i in range(len(frame_type)):
         frame_skip = 10
         for i in range(0, len(frame_type), frame_skip):
             if frame_type[i] != 'I':
                # Note: i+1 because ffmpeg frame indices START FROM 1
                fo = '{}_{}_{}.png'.format(format(frame_size[i], '05d'), format(i+1,'05d'), filename[:-4])
                cmd = 'montage tmp/{}.png tmp_e/{}.png -tile 2x1 -font DejaVu-Sans -geometry +0+0 PNG24:train_frames/{}'.format(format(i+1,'05d'), format(i+1,'05d'), fo)
                output = call(cmd)

    else:
        continue

