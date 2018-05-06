import numpy as np
import matplotlib.pyplot as plt
import cv2, os, sys, subprocess, pdb

FRMPERWIN = 1 ;

def call(cmd):
    # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
    proc = subprocess.Popen(cmd, \
                   stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return (out, err)

def export_frames(fn):
    osout = call('rm -rf png'.format(fn))
    osout = call('mkdir png'.format(fn))
    osout = call('ffmpeg -i {} -qp 0 png/%d.png'.format(fn))
    osout = call('ls -v png/*.png') ; lfrm = osout[0] 
    lfrm = lfrm.split('\n')[0:-1]

    return lfrm

if __name__ == '__main__':
    # matches = content_similarity(sys.argv[-1], sys.argv[-2])
    # sim = sliding_window_similarity(['A.jpg','B.jpg'], ['B.jpg','C.jpg'])
    lfrm = export_frames(sys.argv[-1]);
    lwinsim = []
    fid = open('OrderedFrames.txt','w')

    # Get global window similarity matrix
    for fcnt in range(len(lfrm)):
	print('Frame{}').format(fcnt)
    	print >> fid, fcnt
    
