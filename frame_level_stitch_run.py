import numpy as np
import matplotlib.pyplot as plt
import cv2, os, sys, subprocess, pdb
import scenedetect, re

FRMPERWIN = 1 ; INF = 999

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
    #print("{} ...... {}\n").format(img_0,img_1)

    # find the keypoints and descriptors with SIFT
    kp1, des1 = orb.detectAndCompute(img1,None)
    kp2, des2 = orb.detectAndCompute(img2,None)
    
    if (type(des1)==type(des2)):
    	# create BFMatcher object
    	bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    	# Match descriptors.
    	matches = bf.match(des1,des2)
    	# pdb.set_trace()

    	# Sort them in the order of their distance.
    	matches   = sorted(matches, key = lambda x:x.distance)
    	distances = [ _.distance for _ in matches]
    	simind_1    =  np.mean(distances)
    	#print("simind_1={}\n").format(simind_1)

    	# Match descriptors.
    	matches = bf.match(des2,des1)
    	# pdb.set_trace()

    	# Sort them in the order of their distance.
    	matches   = sorted(matches, key = lambda x:x.distance)
    	distances = [ _.distance for _ in matches]
    	simind_2    =  np.mean(distances)

    	simind = (simind_1 + simind_2)/float(2)
	#print("dis1={}\n dis2={}\n").format(des1,des2)
    else:
	#print("dis1={}\n dis2={}\n").format(des1,des2)
     	simind=1000

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


    frames_read = scenedetect.detect_scenes(cap, scene_list, detector_list)

    # scene_list now contains the frame numbers of scene boundaries.
    print(scene_list)

    # Ensure we release the VideoCapture object.
    cap.release()
    
    scene_list=np.array(scene_list) ;
    scene_list=scene_list+2;
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
        print('{}').format(win)
        for win_sc in lwin_sc_:
          s=re.search('(?<=/)\w+', str(win))
          iwin=int(s.group(0))
          s=re.search('(?<=/)\w+', str(win_sc))
          iwin_sc=int(s.group(0))
          #lwinsim[iwin-1][iwin_sc-1]=sliding_window_similarity(win, win_sc)[0]
	  lwinsim[iwin-1][iwin_sc-1]=window_similarity(win, win_sc)
	  #print('{}..&..{}=..{}').format(win,win_sc,lwinsim[iwin-1][iwin_sc-1])
          #lwinsim[iwin_sc-1][iwin-1]=lwinsim[iwin-1][iwin_sc-1]
    return lwinsim

if __name__ == '__main__':
    # matches = content_similarity(sys.argv[-1], sys.argv[-2])
    # sim = sliding_window_similarity(['A.jpg','B.jpg'], ['B.jpg','C.jpg'])
    fn=sys.argv[-1]
    lfrm = export_frames(fn) ; 
    lwin = make_windows(lfrm, FRMPERWIN)
    lwinsim = []
    #print(lwin)
    lwin1 = find_scene_cuts(fn) ;
    print(lwin1)
    lwin1.append('png/1.png')
    lwin_sc = make_windows(lwin1, FRMPERWIN)
    lwinsim=np.full((len(lwin),len(lwin)), INF)
    lwindissim=np.full((len(lwin),len(lwin)), INF)
    # Get global window similarity matrix
    
    lwinsim=comp_similarity(lwin,lwin_sc,lwinsim)
    
    Lambda=0.001
    WeightPicPos=Lambda*(np.transpose(np.full((len(lwin),1),1)*np.array(range(1,len(lwin)+1))))
    lwinsim=lwinsim+WeightPicPos

    #print('\nWindow similarity matrix:') ; print(np.matrix(lwinsim))
    # lwinfreq = [ np.mean(_) for _ in lwinsim ]
    lwin_popularity_index = [ np.mean(_) for _ in lwinsim ]
    print(lwin_popularity_index)

    lwin_opt_sorting = [] ; lwin_opt_sorting.append(np.argmin(lwin_popularity_index))
    current_top_win_index = np.argmin(lwin_popularity_index) 
    current_top_win = lwin[current_top_win_index]
    #print('{}....{}').format(current_top_win_index,current_top_win)
    
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
        lwindissim=comp_similarity(lwin[current_top_win_index],lwin,lwindissim)
        #print('\nWindow dissimilarity matrix:') ; print(np.matrix(lwindissim))
        next_candidate_criterion = [dissimilarity/float(popularity) for dissimilarity, popularity \
                                        in zip(np.mean(lwindissim,axis=0), lwin_popularity_index)]  ##consider dissimilarity with all previously selected current_top_win_indexs

	#next_candidate_criterion = [dissimilarity/float(popularity) for dissimilarity, popularity \
        #                                in zip(lwindissim[current_top_win_index], lwin_popularity_index)] ##consider dissimilarity with only the current_top_win_index

        #print(next_candidate_criterion)
        # Sorted list indices
        sorted_candidate_criterion = [ _[0] for _ in sorted(enumerate(next_candidate_criterion), key=lambda x:x[1], reverse=True) ]
        #print(sorted_candidate_criterion)
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

    for i in range(0, len(lwin)):
      if i not in lwin_opt_sorting:
               lwin_opt_sorting.append(i)
  
    print('\nOPTIMAL HEVC GOP ORDER:') ; print(lwin_opt_sorting)

    ## Added by Jubran
    fid = open('OrderedFrames.txt','w')
    for FNum in lwin_opt_sorting:
    	print >> fid, FNum
    #pdb.set_trace()
