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
parser.add_argument('--fn', type=str,
                    help='rate file name')

parser.add_argument('--gp', type=int,
                    help='Guard Period')

#parser.add_argument('--suffix', type=str,
#                    help='suffix added to all output files')

args = parser.parse_args()

fn=args.fn;
GP=args.gp;
#suffix=args.suffix;
wpp=1;
wd=1;


if __name__ == '__main__':
  with open(fn) as f:
    lines = f.readlines()
  lines = [x.strip() for x in lines] 
  rate = [float(r.split(' ')[-1]) for r in lines]
  FN = [int(r.split('_')[1]) for r in lines]
  SF = [int(r.split('_')[2].split('F')[1]) for r in lines]

  #pdb.set_trace()
  Sim = np.zeros((max(FN)+1,max(FN)+1))
  Sim = Sim.astype(int)
  for i in range(len(rate)):
    Sim[SF[i]-1][FN[i]-1] = rate[i] # row is the SF number

  for i in range(len(rate)):
     if Sim[FN[i]-1][SF[i]-1] == 0 :
       Sim[FN[i]-1][SF[i]-1] = Sim[SF[i]-1][FN[i]-1]

  lwinsim=np.copy(Sim)
  lwinsim=lwinsim[:,np.mean(lwinsim,axis=0)!=0]
  lwinsim[lwinsim==0]=np.amax(np.amax(lwinsim))
  lwin_popularity_index = [ 1/np.mean(_) for _ in lwinsim ]
  lwin_popularity_index_Norm_temp=((lwin_popularity_index)/np.amax(np.amax(lwin_popularity_index)))
  lwin_popularity_index_Norm=lwin_popularity_index_Norm_temp
  lwin_popularity_index_Norm=np.transpose(lwin_popularity_index_Norm)
  #pdb.set_trace()

  lwin_opt_sorting = [] ; lwin_opt_sorting.append(np.argmax(lwin_popularity_index))
  lwin_opt_sorting_GP = [] ;
  for i in range(-GP,GP+1):
    if ((np.argmax(lwin_popularity_index_Norm)+i) > -1 ) and ((np.argmax(lwin_popularity_index_Norm)+i) < len(lwin_popularity_index_Norm)):
       lwin_opt_sorting_GP.append(np.argmax(lwin_popularity_index_Norm)+i)
  current_top_win_index = np.argmax(lwin_popularity_index_Norm) 
  #print(current_top_win_index)
  #current_top_win = lwin[current_top_win_index]
  print('Producing Popularity-Dissimilarity List')
  #pdb.set_trace()

  SC = int(Sim.shape[0]/(2*GP))
  print(SC)
  lwin_opt_sorting = [current_top_win_index]
  lwindissim=np.full((Sim.shape[0],Sim.shape[1]), INF)
  for i in range(0, SC):
    lwindissim[lwin_opt_sorting,:]=Sim[lwin_opt_sorting,:]
    lwindissim_0=np.copy(lwindissim);
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
  
  fid = open('OrderedFrames_'+os.path.basename(fn),'w')
  for FNum in lwin_opt_sorting:
    print >> fid, FNum
