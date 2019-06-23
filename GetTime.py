#Frame1: Type POC QPoffset QPOffsetModelOff QPOffsetModelScale CbQPoffset CrQPoffset QPfactor tcOffsetDiv2 betaOffsetDiv2 temporal_id #ref_pics_active #ref_pics reference 
#pictures predict deltaRPS #ref_idcs reference idcs print >> fid, 'Frame1: P 1 5 -6.5 0.2590 0 0 1.0 0 0 0 1 1 -1 0');
import datetime, math, time
import sys
#from memory_profiler import profile

#mem_usage = memory_usage(-1, interval=.2, timeout=1)
curr_time=datetime.datetime.now();
fid = open('../savenpy/MemoryTime_log.txt','a+');
fid.write('Current {} Time = {}\n'.format(sys.argv[1],curr_time));
