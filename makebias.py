#!/usr/bin/env python3

import os
import sys
import pyfits
import numpy

import suprimecam
import qr
import podi_imcombine

if __name__ == "__main__":

    biaslist = []
    for fn in sys.argv[2:]:
        hdulist = pyfits.open(fn)
        obstype = hdulist[0].header['DATA-TYP']
        if (obstype == 'BIAS'):
            biaslist.append(fn)

    # Now we have a list of biases
    calib_dir = sys.argv[1]
    if (not os.path.isdir(calib_dir)):
        os.mkdir(calib_dir)

    # create individual bias frames
    tmp_dir = os.path.join(calib_dir, "tmp")
    if (not os.path.isdir(tmp_dir)):
        os.mkdir(tmp_dir)

    tmp_filelist = []
    for fn in biaslist:
        _,bn = os.path.split(fn)
        tmp_filename = os.path.join(tmp_dir, bn[:-5]+".bias.fits")
        if (not os.path.isfile(tmp_filename)):
            print("Preparing BIAS frame: %s" % (fn))
            suprimecam.reduce_exposure(input_fn=fn,
                                       output_fn=tmp_filename,
                                       bias_fn=None, dark_fn=None, flat_fn=None)
        else:
            print("Skipping existing file: %s" % (fn))
        tmp_filelist.append(tmp_filename)

    # Now do the final stacking
    calib_file = os.path.join(calib_dir, "bias.fits")
    if (not os.path.isfile(calib_file)):
        podi_imcombine.imcombine(
            input_filelist=tmp_filelist,
            outputfile=calib_file,
            operation='sigmaclipmean')