from __future__ import print_function
from vmaf.tools.bd_rate_calculator import BDrateCalculator
import unittest
import numpy as np
#from vmaf.tools.bd_rate_calculator import BDrateCalculator

__copyright__ = "Copyright 2016, Netflix, Inc."
__license__ = "Apache, Version 2.0"


if __name__ == '__main__':
  import sys
  if not len(sys.argv[1:]):
    print('Must supply a filename', file=sys.stderr)
    sys.exit(1)
  LN1 = list()
  LN2 = list()
  try:
    with open(sys.argv[1], 'Ur') as input_data:
      for each_line in input_data:
        Line=each_line.split()
        for L in Line:
          try:
             LN1.append(float(L))
          except ValueError as e:
             print('Warning: Unable to parse %s: %s' % (L, e),
             file=sys.stderr)
  except EnvironmentError as err_open:
    print('Error accessing file %s: %s' % (sys.argv[1], err_open),
     file=sys.stderr)
    sys.exit(err_open.errno)

  try:
    with open(sys.argv[2], 'Ur') as input_data:
      for each_line in input_data:
        Line=each_line.split()
        for L in Line:
          try:
             LN2.append(float(L))
          except ValueError as e:
             print('Warning: Unable to parse %s: %s' % (L, e),
             file=sys.stderr)
  except EnvironmentError as err_open:
    print('Error accessing file %s: %s' % (sys.argv[1], err_open),
     file=sys.stderr)
    sys.exit(err_open.errno)


#  print(LN1)
  h11=LN1[2:][::5]
  h12=LN1[3:][::5]
  h13=LN1[4:][::5]

  h21=LN2[2:][::5]
  h22=LN2[3:][::5]
  h23=LN2[4:][::5]

  Rate_PSNR_1=zip(h11,h12)
  PSNR_Rate_1=zip(h12,h11)
  Rate_VMAF_1=zip(h11,h13)
  VMAF_Rate_1=zip(h13,h11)

  Rate_PSNR_2=zip(h21,h22)
  PSNR_Rate_2=zip(h22,h21)
  Rate_VMAF_2=zip(h21,h23)
  VMAF_Rate_2=zip(h23,h21)

  h1=zip(h11,h12,h13)
  h2=zip(h21,h22,h23)

  print('Ref: {}'.format(h1))
  print('New: {}'.format(h2))

  BD_Rate_PSNR=BDrateCalculator.CalcBDRate(Rate_PSNR_1,Rate_PSNR_2);
  print('BD-Rate-PSNR={}'.format(BD_Rate_PSNR))

  BD_PSNR_Rate=BDrateCalculator.CalcBDRate(PSNR_Rate_1,PSNR_Rate_2);
  print('BD-PSNR-Rate={}'.format(BD_PSNR_Rate))

  BD_Rate_VMAF=BDrateCalculator.CalcBDRate(Rate_VMAF_1,Rate_VMAF_2);
  print('BD-Rate-VMAF={}'.format(BD_Rate_VMAF))

  BD_VMAF_Rate=BDrateCalculator.CalcBDRate(VMAF_Rate_1,VMAF_Rate_2);
  print('BD-VMAF-Rate={}'.format(BD_VMAF_Rate))

