import numpy as np
import matplotlib.pyplot as plt
import cv2, os, sys, subprocess, pdb
import scenedetect, re
import datetime, math, time
import argparse
from numpy import *

FRMPERWIN = 1 ; INF = 999

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--f', type=str,
                    help='file name')

parser.add_argument('--fsr', type=int,
                    help='frame sample rate (ffmpeg -r ?)')

parser.add_argument('--fps', type=int,
                    help='frame rate (ffmpeg -r ?)')

args = parser.parse_args()

fn=args.f;
fsr=args.fsr;
fps=args.fps;

def call(cmd):
    # proc = subprocess.Popen(["cat", "/etc/services"], stdout=subprocess.PIPE, shell=True)
    proc = subprocess.Popen(cmd, \
                   stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return (out, err)

def export_frames(fn):
    osout = call('rm -rf pngall')
    osout = call('mkdir pngall')
    osout = call('ffmpeg -r 1 -i {} -r 1 -qp 0 pngall/%d.png'.format(fn)) ##no downsampling 1:1

    osout = call('ls -v pngall/*.png') ; lfrmall = osout[0]
    lfrmall = lfrmall.split('\n')[0:-1]
    
    osout = call('rm -rf pngDS')
    osout = call('mkdir pngDS')
    for cnt in range(len(lfrmall)):
        if ((cnt) % (fps/fsr)) == 0:
             osout = call('cp -rf pngall/{}.png pngDS/{}.png'.format((cnt+1),int((cnt/(fps/fsr))+1)))
 
    osout = call('ls -v pngDS/*.png') ; lfrm = osout[0]
    lfrm = lfrm.split('\n')[0:-1]
    osout = call('rm -rf ../vid/out.mp4')
    osout = call('ffmpeg -start_number 0 -i "pngDS/%d.png" -c:v libx264 -vf "fps={},format=yuv420p" ../vid/out.mp4'.format(fps))
    return lfrm

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
    #print(img_0);print(img_1);print(img1);print(img2)
    #print(des1)
    #print(des2)
    #pdb.set_trace()
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

    	# Match descriptors.
    	#matches = bf.match(des2,des1)
    	# pdb.set_trace()

    	# Sort them in the order of their distance.
    	#matches   = sorted(matches, key = lambda x:x.distance)
        #print("simind_2 matches={}").format(matches)

    	#distances = [ _.distance for _ in matches]
    	#simind_2    =  np.mean(distances)
        
        if math.isnan(simind_1):
          simind_1=1000

        simind_2=simind_1
    	simind = (simind_1 + simind_2)/float(2)
        #print("simind={}").format(simind)
	#print("dis1={}\n dis2={}...{}\n").format(des1,des2,simind)
    else:
        simind=1000
	#print("dis1={}\n dis2={}...{}\n").format(des1,des2,simind)

    # Draw first 10 matches.
    #img3 = cv2.drawMatches(img1,kp1,img2,kp2,matches[:10], flags=2)
    #plt.imshow(img3),plt.show()
    #pdb.set_trace()
    return simind

def make_windows(lfrm, numfrmwin):
    numfrm = len(lfrm) ; numwin = numfrm/numfrmwin
    lwin = []
    for i in range(0, numfrm, numfrmwin ): lwin.append(lfrm[i:i+numfrmwin])
    return lwin

def find_scene_cuts(fn):

    scene_list = []		# Modified by detect_scenes(...) below.
    
    cap = cv2.VideoCapture(fn)	
    # Make sure to check cap.isOpened() before continuing!

    # Usually use one detector, but multiple can be used.
    detector_list = [scenedetect.ContentDetector()]
    #detector_list = [scenedetect.ContentDetector(threshold = 30,min_scene_len = 1)]
    #detector_list = [scenedetect.ThresholdDetector(threshold = 1, min_percent = 0.95, min_scene_len = 1)]


    frames_read = scenedetect.detect_scenes(cap, scene_list, detector_list)

    # scene_list now contains the frame numbers of scene boundaries.
    #print(scene_list)

    # Ensure we release the VideoCapture object.
    cap.release()
    
    scene_list=np.array(scene_list) ;
    scene_list=scene_list+1;
    #print(scene_list)

    win_sc=[];
    for i in range(0, len(scene_list)): 
            win_sc.append('png/'+str(scene_list[i])+'.png')
    #print(win_sc)
    return win_sc

def comp_similarity(lwin_,lwin_sc_,lwinsim):
    #print(type(lwin_))
    for win in lwin_:
        #lwinsim_ = []
        now = datetime.datetime.now()
        print('{} ... {}').format(win,now.strftime("%Y-%m-%d %H:%M:%S"))
        for win_sc in lwin_sc_:
          s=re.search('(?<=/)\w+', str(win))
          iwin=int(s.group(0))
          s=re.search('(?<=/)\w+', str(win_sc))
          iwin_sc=int(s.group(0))
          #lwinsim[iwin-1][iwin_sc-1]=sliding_window_similarity(win, win_sc)[0]
	  #if iwin >= iwin_sc:
          lwinsim[iwin-1][iwin_sc-1]=window_similarity(win, win_sc)
	  #print('{}..&..{}=..{}').format(win,win_sc,lwinsim[iwin-1][iwin_sc-1])
          #lwinsim[iwin_sc-1][iwin-1]=lwinsim[iwin-1][iwin_sc-1]
    return lwinsim

def map_to_downsampled(lwin,fname):
    lwindownSampled = []
    lwindownSampledint = []
    lwinBeforedownSampledint = []
    for win in lwin:    
        s=re.search('(?<=/)\w+', str(win))
        iwin=int(s.group(0))
        lwinBeforedownSampledint.append(int(math.ceil(iwin)))   ##before downsampling
        lwindownSampledint.append(int(math.ceil((iwin-1)/(fps/fsr))+1)) ##downsampling to 8:1

    lwindownSampledint=np.unique(np.array(lwindownSampledint))
    lwinBeforedownSampledint=np.array(lwinBeforedownSampledint)

    np.save(('../savenpy/'+fname+'_SceneCutFramesBeforeDownSampling'),(lwinBeforedownSampledint-1))
    np.save(('../savenpy/'+fname+'_SceneCutFrames'),(lwindownSampledint-1))
    for iwin in lwindownSampledint:    
        lwindownSampled.append('pngDS/'+str(iwin)+'.png')
    return lwindownSampled


def comp_dissimilarity(lwin_r,lwin_c,lwinsim):
    for win_r in lwin_r:
        now = datetime.datetime.now()
        print('{} ... {}').format(win_r,now.strftime("%Y-%m-%d %H:%M:%S"))
        for win_c in lwin_c:
          s=re.search('(?<=/)\w+', str(win_r))
          iwin_r=int(s.group(0))
          s=re.search('(?<=/)\w+', str(win_c))
          iwin_c=int(s.group(0))
          if window_similarity(win_r, win_c)==1000:
              lwinsim[iwin_r-1][iwin_c-1]=0
          else:
              lwinsim[iwin_r-1][iwin_c-1]=window_similarity(win_r, win_c)
    return lwinsim

if __name__ == '__main__':
    np.set_printoptions(threshold=np.nan)
    #fn=sys.argv[-1]
    fname=fn.split('/')[2]
    fname=fname[0:(len(fname)-4)]
    
    lfrm = export_frames(fn);
    lfrmdel=lfrm[1];
    lwin = make_windows(lfrm, FRMPERWIN)
    lwinsim = []
    #print(lwin)
    lwin1 = find_scene_cuts(fn);
    #lwin1 = find_scene_cuts('../vid/out.mp4') ;
    #print(lwin1)
    lwin1=map_to_downsampled(lwin1,fname)
    print(lwin1)
    print("Number of SC frames is {}").format(len(lwin1))
    
    #lwin1.append('png/1.png') ##it is no neccessary to have first frame part of the stitching frames
    lwin_sc = make_windows(lwin1, FRMPERWIN)
    lwinsim=np.full((len(lwin),len(lwin)), INF)
    lwindissim=np.full((len(lwin),len(lwin)), INF)
   
    LambdaPoP=0.000000001
    WeightPicPos=LambdaPoP*(np.transpose(np.full((len(lwin),1),1)*np.array(range(1,len(lwin)+1))))
    #lwinsimNorm=lwinsim/np.matrix.max(lwinsim)
    np.set_printoptions(threshold=np.nan)
    #print(lwinsim.shape)
    #print(np.amax(np.amax(lwinsim)))

    if os.path.isfile('../savenpy/'+fname+'_lwinsim.npy'):
       #pdb.set_trace()
       print("Loading similarity score between SC and all frames")
       lwinsim=np.load(('../savenpy/'+fname+'_lwinsim.npy'))
    else:
       # Get global window similarity matrix
       print("Computing similarity between SC and all frames")
       #pdb.set_trace()
       lwinsim=comp_similarity(lwin,lwin_sc,lwinsim)
       np.save(('../savenpy/'+fname+'_lwinsim'),lwinsim)

    lwinsim=((lwinsim.astype(float))/np.amax(np.amax(lwinsim)))
    np.save(('../savenpy/'+fname+'_lwinsimNormalized'),lwinsim)
    print(np.unique(lwinsim))
    print(np.mean(np.mean(lwinsim,0),0))
    lwinsim=lwinsim+WeightPicPos
    np.save(('../savenpy/'+fname+'_lwinsimNormalizedWeighted'),lwinsim)
    #print(np.mean(lwinsim,0))
    

    #pdb.set_trace()
    #print('\nWindow similarity matrix:') ; print(np.matrix(lwinsim))
    lwin_popularity_index = [ np.mean(_) for _ in lwinsim ]
    #print(lwin_popularity_index)
    #lwin_popularity_index = np.mean(lwinsim,1)
    #print(lwin_popularity_index)
    #pdb.set_trace()
    lwin_opt_sorting = [] ; lwin_opt_sorting.append(np.argmin(lwin_popularity_index))
    current_top_win_index = np.argmin(lwin_popularity_index) 
    current_top_win = lwin[current_top_win_index]
    #print('{}....{}').format(current_top_win_index,current_top_win)
    print('Producing Popularity-Dissimilarity List')
    for i in range(0, len(lwin_sc)):
	#print('i={}....{}').format(i,current_top_win_index)
        # lwinsim_ = []
        # for win_ in lwin: lwinsim_.append(sliding_window_similarity(current_top_win, win_)[0])
        # lwin_popularity_index = [np.mean(_) for _ in lwinsim_]

        # for i in range(0, len(lwinsim)):
        # Find next candidates with maximum dissimilarity


        # next_candidates = lwin[np.argmax(lwinsim[current_top_win_index])]
        # next_candidates_indices = lwin[np.argmax(lwinsim[current_top_win_index])]

        # Make choice criterion list
        #pdb.set_trace()
        lwindissim=comp_dissimilarity(lwin[current_top_win_index],lwin,lwindissim)
        lwindissimNorm=((lwindissim.astype(float))/np.amax(np.amax(lwindissim)))
        #print(np.mean(lwindissimNorm,axis=1))
        #print(np.mean(lwindissimNorm,axis=0))
        #print('\nWindow dissimilarity matrix:') ; print(np.matrix(lwindissim))
        next_candidate_criterion = [((4*dissimilarity)+(1/float(popularity))) for dissimilarity, popularity \
                                        in zip(np.mean(lwindissimNorm,axis=0), lwin_popularity_index)]  ##consider dissimilarity with all previously selected current_top_win_indexs
        np.save(('../savenpy/'+fname+'next_candidate_criterion'+str(i)),next_candidate_criterion)
	#next_candidate_criterion = [dissimilarity/float(popularity) for dissimilarity, popularity \
        #                                in zip(lwindissim[current_top_win_index], lwin_popularity_index)] ##consider dissimilarity with only the current_top_win_index

        #print(next_candidate_criterion)
        # Sorted list indices
        sorted_candidate_criterion = [ _[0] for _ in sorted(enumerate(next_candidate_criterion), key=lambda x:x[1], reverse=True) ]
        sorted_candidate_criterion_Index_Value = [ _ for _ in sorted(enumerate(next_candidate_criterion), key=lambda x:x[1], reverse=True) ]
        #print(sorted_candidate_criterion_Index_Value)
        # next_candidate = lwin[np.argmax(lwinsim[current_top_win_index])]
        #for next_candidate in sorted_candidate_criterion:

        #    if next_candidate not in lwin_opt_sorting:
        #       lwin_opt_sorting.append(next_candidate)
        #       current_top_win_index = next_candidate
        for next_candidate in sorted_candidate_criterion:
            if next_candidate not in lwin_opt_sorting:
               lwin_opt_sorting.append(next_candidate)
               current_top_win_index = next_candidate
               break
        print(lwin_opt_sorting)
 
    #reprint the SC frames
    print("Number of SC frames is {}").format(len(lwin1))    
    print(lwin1)

    np.save(('../savenpy/'+fname+'_lwindissim'),lwindissim)
    np.save(('../savenpy/'+fname+'_lwindissimNormalized'),lwindissimNorm)
    print('\nOPTIMAL Stitching frames at Downsampled space:') ; print(lwin_opt_sorting)
    lwin_opt_sorting=np.array(lwin_opt_sorting)*fps/fsr
    print('\nOPTIMAL Stitching frames:') ; print(lwin_opt_sorting)
    for i in range(0, len(lwin)*fps/fsr):
      if i not in lwin_opt_sorting:
               lwin_opt_sorting=np.append(lwin_opt_sorting,i)
  
    #print('\nOPTIMAL HEVC GOP ORDER at Downsampled space:') ; print(lwin_opt_sorting)
    fid = open('OrderedFrames_'+fname+'_fps'+str(fps)+'_fsr'+str(fsr)+'.txt','w')
    for FNum in lwin_opt_sorting:
    	print >> fid, FNum
    #pdb.set_trace()
