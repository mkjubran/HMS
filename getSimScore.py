import os, sys, subprocess
import pdb
import re
import argparse
import numpy as np
from os import listdir
from os.path import isfile, join
import datetime, math, time
#import cv2

INF = 9999999

# Instantiate the parser
parser = argparse.ArgumentParser(description='Optional app description')

# Optional argument
parser.add_argument('--in_dir', type=str,
                    help='Input Directory')

parser.add_argument('--gp', type=int,
                    help='Guard Period')

parser.add_argument('--suffix', type=str,
                    help='suffix added to all output files')

args = parser.parse_args()

input_dir=args.in_dir;
GP=args.gp;
suffix=args.suffix;
wpp=1;
wd=1;


if __name__ == '__main__':
  onlyfiles = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
  rate = [int(r.split('_')[0]) for r in onlyfiles]
  FN = [int(r.split('_')[1]) for r in onlyfiles]
  SF = [int(r.split('_')[2].split('F')[1]) for r in onlyfiles]

  Sim = np.zeros((max(FN)+1,max(FN)+1))
  for i in range(len(rate)):
    Sim[FN[i]-1][SF[i]-1] = rate[i]

  for i in range(max(FN)+1):
     for j in range(max(FN)+1): 
        if (Sim[i][j] == 0) and (j == 0):
          Sim[i][j] = Sim[i-1][j]
        elif (Sim[i][j] == 0):
          Sim[i][j] = Sim[i][j-1]

  lwinsim=np.copy(Sim)
  lwinsim=lwinsim[:,np.mean(lwinsim,axis=0)!=INF]
  lwin_popularity_index = [ 1/np.mean(_) for _ in lwinsim ]
  lwin_popularity_index_Norm_temp=((lwin_popularity_index)/np.amax(np.amax(lwin_popularity_index)))
  lwin_popularity_index_Norm=lwin_popularity_index_Norm_temp
  lwin_popularity_index_Norm=np.transpose(lwin_popularity_index_Norm)
  print(lwin_popularity_index_Norm[0:20])


  lwin_opt_sorting = [] ; lwin_opt_sorting.append(np.argmax(lwin_popularity_index))
  lwin_opt_sorting_GP = [] ;
  for i in range(-GP,GP+1):
    if ((np.argmax(lwin_popularity_index_Norm)+i) > -1 ) and ((np.argmax(lwin_popularity_index_Norm)+i) < len(lwin_popularity_index_Norm)):
       lwin_opt_sorting_GP.append(np.argmax(lwin_popularity_index_Norm)+i)
  current_top_win_index = np.argmax(lwin_popularity_index_Norm) 
  print(current_top_win_index)
  #current_top_win = lwin[current_top_win_index]
  print('Producing Popularity-Dissimilarity List')
  
  SC = int(Sim.shape[0]/(2*GP))
  print(SC)
  for i in range(0, SC):
    lwindissim_0=np.copy(Sim);
    lwindissim_test=np.copy(lwindissim_0);
    lwindissim_test[lwindissim_test==INF]=0
    if len(lwindissim_test[np.mean(lwindissim_test,axis=1)!=0,:])==0:
       lwindissim_0[lwindissim_0==0]=1;
    lwindissim_0[lwindissim_0==INF]=0
    lwindissim_0=lwindissim_0[np.mean(lwindissim_0,axis=1)!=0,:]
    lwindissimNorm=((lwindissim_0.astype(float))/np.amax(np.amax(lwindissim_0)))
    next_candidate_criterion = np.array([((wd*dissimilarity)+(wpp*popularity)) for dissimilarity, popularity \
                                        in zip(np.min(lwindissimNorm,axis=0), lwin_popularity_index_Norm)])  ##consider dissimilarity with all previously selected current_top_win_indexs
    sorted_candidate_criterion = [ _[0] for _ in sorted(enumerate(next_candidate_criterion), key=lambda x:x[1], reverse=True) ]
    sorted_candidate_criterion_Index_Value = [ _ for _ in sorted(enumerate(next_candidate_criterion), key=lambda x:x[1], reverse=True) ]
    sorted_candidate_criterion_Index_Value=np.array(sorted_candidate_criterion_Index_Value)
    for next_candidate in sorted_candidate_criterion:
      if next_candidate not in lwin_opt_sorting_GP:
         lwin_opt_sorting.append(next_candidate)
         current_top_win_index = next_candidate
         for i in range(-GP,GP+1):
           if ((next_candidate+i) > -1 ) and ((next_candidate+i) < Sim.shape[0]):
             lwin_opt_sorting_GP.append(next_candidate+i)
         break
    lwin_opt_sorting_GP=list(np.unique(lwin_opt_sorting_GP))
    print('{} .... {}%'.format(lwin_opt_sorting,100*len(lwin_opt_sorting)/SC))

  for i in range(0, Sim.shape[0]):
    if i not in lwin_opt_sorting:
      lwin_opt_sorting=np.append(lwin_opt_sorting,i)
  
  fid = open('OrderedFrames_'+suffix+'.txt','w')
  for FNum in lwin_opt_sorting:
    print >> fid, FNum
