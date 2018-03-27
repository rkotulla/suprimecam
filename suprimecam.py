#!/usr/bin/env python3

import os
import sys
import pyfits

import overscan

import qr
from podi_collectcells import apply_wcs_distortion

def get_calib_hdu(dir_fn, fallback):

    hdu = None
    if (dir_fn is not None):
        if (os.path.isfile(dir_fn)):
            hdu = pyfits.open(dir_fn)
        elif (os.path.isdir(dir_fn)):
            _fn = os.path.join(dir_fn, fallback)
            if (os.path.isfile(_fn)):
                hdu = pyfits.open(_fn)
    return hdu


def reduce_ccd(input_fn,
           output_fn,
           bias_fn=None, dark_fn=None, flat_fn=None,
               wcs=None, fixwcs=False):

    hdu_in = pyfits.open(input_fn)

    overscan_sub = overscan.overscan(hdu_in)
    extname = overscan_sub.name

    bias_hdu = None
    if (bias_fn is not None):
        if (os.path.isfile(bias_fn)):
            bias_hdu = pyfits.open(bias_fn)
        elif (os.path.isdir(bias_fn)):
            _bias_fn = os.path.join(bias_fn, "bias.fits")
            if (os.path.isfile(_bias_fn)):
                bias_hdu = pyfits.open(_bias_fn)
    if (bias_hdu is not None):
        for ext in bias_hdu:
            if (ext.name == extname):
                overscan_sub.data -= ext.data

    exptime = overscan_sub.header['EXPTIME']
    dark_hdu = get_calib_hdu(dark_fn, "dark.fits")
    if (dark_hdu is not None):
        for ext in dark_hdu[1:]:
            if (ext.name == extname):
                overscan_sub.data -= ext.data * exptime

    filtername = overscan_sub.header['FILTER01']
    fallback = "flat_%s.fits" % (filtername)
    flat_hdu = get_calib_hdu(flat_fn, fallback)
    if (flat_hdu is not None):
        for ext in flat_hdu[1:]:
            if (ext.name == extname):
                overscan_sub.data /= ext.data

    # Apply WCS from distortion file
    if (wcs is not None and os.path.isfile(wcs)):
        apply_wcs_distortion(wcs, overscan_sub, binning=1)

    # Write temporary file

    # Run Sextractor
    src_catalog = None

    return overscan_sub, src_catalog


def reduce_exposure(input_fn,
                    output_fn,
                    bias_fn=None, dark_fn=None, flat_fn=None,
                    fixwcs=False):

    # based on the input fn, work out the name of all files
    dir, bn = os.path.split(input_fn)
    filebase,_ = os.path.splitext(input_fn)

    filelist = ["%s%d.fits" % (filebase[:-1],ccd) for ccd in range(10)]
    print(filelist)

    wcs = "/work/suprimecam/suprimecam_wcs2.fits"

    output_hdus = [pyfits.PrimaryHDU()]
    for fn in filelist:
        img, src_cat = reduce_ccd(input_fn=fn, output_fn=None,
                                      bias_fn=bias_fn, dark_fn=dark_fn, flat_fn=flat_fn,
                                  wcs=wcs, fixwcs=fixwcs)
        output_hdus.append(img)

    hdulist = pyfits.HDUList(output_hdus)

    if (output_fn is not None):
        hdulist.writeto(output_fn, clobber=True)

    return hdulist


if __name__ == "__main__":

    fn =  sys.argv[1]

    calib_dir = sys.argv[2]

    output_fn = fn[:-6]+".sup.fits"
    reduce_exposure(input_fn=fn, output_fn=output_fn,
                    bias_fn=calib_dir, dark_fn=calib_dir,
                    flat_fn=calib_dir)

