#!/usr/bin/env python3

import os
import sys
import pyfits
import numpy

import suprimecam
import qr
import podi_imcombine

if __name__ == "__main__":

    flatlist = {}
    for fn in sys.argv[2:]:
        hdulist = pyfits.open(fn)
        obstype = hdulist[0].header['DATA-TYP']
        filtername = hdulist[0].header['FILTER01']
        if (obstype == 'DOMEFLAT'):
            if (filtername not in flatlist):
                flatlist[filtername] = []
            flatlist[filtername].append(fn)

    # Now we have a list of flates
    calib_dir = sys.argv[1]
    if (not os.path.isdir(calib_dir)):
        os.mkdir(calib_dir)

    # create individual flat frames
    tmp_dir = os.path.join(calib_dir, "tmp")
    if (not os.path.isdir(tmp_dir)):
        os.mkdir(tmp_dir)

    for filtername in flatlist:


        tmp_filelist = []
        for fn in flatlist[filtername]:
            _,bn = os.path.split(fn)
            tmp_filename = os.path.join(tmp_dir, bn[:-5]+".flat.fits")
            if (not os.path.isfile(tmp_filename)):
                print("Preparing flat frame: %s" % (fn))
                flat_hdu = suprimecam.reduce_exposure(input_fn=fn,
                                           output_fn=None,
                                           bias_fn=calib_dir, dark_fn=calib_dir, flat_fn=None)

                # normalize with mean intensity
                mean_fluxes = []
                for ext in flat_hdu[1:]:
                    mean_fluxes.append(numpy.nanmean(ext.data))
                mean_fluxes = numpy.array(mean_fluxes)
                mean_flux = numpy.nanmean(mean_fluxes)

                for ext in flat_hdu[1:]:
                    ext.data /= mean_flux

                flat_hdu.writeto(tmp_filename, clobber=True)
            else:
                print("Skipping existing file: %s" % (fn))
            tmp_filelist.append(tmp_filename)

        # Now do the final stacking
        calib_file = os.path.join(calib_dir, "flat_%s.fits" % (filtername))
        if (not os.path.isfile(calib_file)):
            podi_imcombine.imcombine(
                input_filelist=tmp_filelist,
                outputfile=calib_file,
                operation='sigmaclipmean')