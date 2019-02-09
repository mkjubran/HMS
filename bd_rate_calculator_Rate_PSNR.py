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
  h11=LN1[0:][::2]
  h12=LN1[1:][::2]
  h1=zip(h11,h12)

#  print(LN2)
  h21=LN2[0:][::2]
  h22=LN2[1:][::2]
  h2=zip(h21,h22)

  print('Ref: {}'.format(h1))
  print('New: {}'.format(h2))

  BDR=BDrateCalculator.CalcBDRate(h1,h2);
  print('BD-Rate={}'.format(BDR))

  h1=zip(h12,h11)
  h2=zip(h22,h21)

  BDPSNR=BDrateCalculator.CalcBDRate(h1,h2);
  print('BD-PSNR={}'.format(BDPSNR))

