"""
Video Quality Metrics
Copyright (c) 2014 Alex Izvorski <aizvorski@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy
import re
import sys
import scipy.misc
import math
import scipy.io

import vifp
import ssim
import mse
#import ssim_theano
#import psnr
#import niqe
#import reco

numpy.set_printoptions(threshold='nan')

def img_read_yuv(src_file, width, height):
    y_imgtemp = numpy.fromfile(src_file, dtype=numpy.uint8, count=(width * height))
    if numpy.size(y_imgtemp)<width * height:
	return (0,0,0)
    y_img=y_imgtemp.reshape((height, width))
    u_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    v_img = numpy.fromfile(src_file, dtype=numpy.uint8, count=((width/2) * (height/2))).reshape( (height/2, width/2) )
    return (y_img, u_img, v_img)

ref_file = sys.argv[1]
dist_file = sys.argv[2]

height=int(sys.argv[4])
width=int(sys.argv[3])

ref_fh = open(ref_file, "rb")
dist_fh = open(dist_file, "rb")

frame_num = 1
mseY = 0
mseU = 0
mseV = 0
mseYUV = 0

while True:
	refY, refU, refV = img_read_yuv(ref_fh, width, height)
	distY, distU, distV = img_read_yuv(dist_fh, width, height)

	if numpy.size(refY) < width * height:
		break
        if numpy.size(distY) < width * height:
		break

	refY=refY.astype(float);refU=refU.astype(float);refV=refV.astype(float)
	distY=distY.astype(float);distU=distU.astype(float);distV=distV.astype(float);

	#if frame_num!=1:
	#	refYM=numpy.dstack((refYM,refY))
	#	distYM=numpy.dstack((distYM,distY))
	#else:
	#	refYM=refY
	#	distYM=distY

	refYUV=numpy.concatenate((refY.reshape(1,height*width),refU.reshape(1,height*width/4),refV.reshape(1,height*width/4)),axis=1)
        distYUV=numpy.concatenate((distY.reshape(1,height*width),distU.reshape(1,height*width/4),distV.reshape(1,height*width/4)),axis=1)

	refYUV=refYUV.astype(float);
	distYUV=distYUV.astype(float);
        
	msefY   = mse.mse(refY, distY)
	msefU   = mse.mse(refU, distU)
	msefV   = mse.mse(refV, distV)
        msefYUV = mse.mse(refYUV, distYUV)

        PIXEL_MAX = 255.0
        if msefY == 0:
		msefY=6.5175e-96
	if msefU == 0:
		msefU=6.5175e-96
	if msefV == 0:
		msefV=6.5175e-96
	if msefYUV == 0:
		msefYUV=6.5175e-96

        mseY = mseY+msefY;
	mseU = mseU+msefU;
	mseV = mseV+msefV;
	mseYUV = mseYUV + msefYUV

	#vifp_value = vifp.vifp_mscale(refY.astype(float), distY.astype(float))
	#ssim_value = ssim.ssim(refY, distY)

        PSNRfY=20 * math.log10(PIXEL_MAX / (math.sqrt(msefY)))
	PSNRfU=20 * math.log10(PIXEL_MAX / (math.sqrt(msefU)))
	PSNRfV=20 * math.log10(PIXEL_MAX / (math.sqrt(msefV)))
        PSNRfYUV=20 * math.log10(PIXEL_MAX / (math.sqrt(msefYUV)))

        PSNRY=20 * math.log10(PIXEL_MAX / (math.sqrt(mseY/frame_num)))
	PSNRU=20 * math.log10(PIXEL_MAX / (math.sqrt(mseU/frame_num)))
	PSNRV=20 * math.log10(PIXEL_MAX / (math.sqrt(mseV/frame_num)))
	PSNRYUV=20 * math.log10(PIXEL_MAX / (math.sqrt(mseYUV/frame_num)))

	#print "Frame=%d	  PSNR(Frame)=%f   PSNR(Video)=%f   VIFP=%f   SSIM=%f" % (frame_num, PSNRFrame, PSNR, vifp_value, ssim_value)
	print("Frame {0:3d}: [Y {1:1.4f}dB   U {2:1.4f}dB   V {3:1.4f}dB   YUV {4:1.4f}dB]  ..... Video: [Y {5:1.4f}dB   U {6:1.4f}dB   V {7:1.4f}dB   YUV {8:1.4f}dB]").format(frame_num,PSNRfY,PSNRfU,PSNRfV,PSNRfYUV,PSNRY,PSNRU,PSNRV,PSNRYUV)
	frame_num += 1

####used for debuging the code
#res=numpy.subtract(refYM,distYM)
#scipy.io.savemat('refYM.mat', mdict={'refYM': refYM})
#scipy.io.savemat('distYM.mat', mdict={'distYM': distYM})
#scipy.io.savemat('res.mat', mdict={'res': res})
