#!/usr/bin/env python3

import os
import sys
import pyfits
import numpy

def overscan(hdu_in):

    ext = hdu_in[0]

    output_img = numpy.empty((4176,2044)) #ext.data.shape)
    output_img[:,:] = numpy.NaN

    xflip = ext.header['S_XFLIP']
    yflip = ext.header['S_YFLIP']

    for channel in range(4):
        x1 = ext.header['S_EFMN%d1' % (channel + 1)]
        x2 = ext.header['S_EFMX%d1' % (channel + 1)]
        y1 = ext.header['S_EFMN%d2' % (channel + 1)]
        y2 = ext.header['S_EFMX%d2' % (channel + 1)]

        os_x1 = ext.header['S_OSMN%d1' % (channel + 1)]
        os_x2 = ext.header['S_OSMX%d1' % (channel + 1)]
        os_y1 = ext.header['S_OSMN%d2' % (channel + 1)]
        os_y2 = ext.header['S_OSMX%d2' % (channel + 1)]

        cutout = ext.data[y1:y2, x1:x2].astype(numpy.float)
        overscan_level = numpy.median(ext.data[os_y1:os_y2, os_x1:os_x2].astype(numpy.float))

        cutout -= overscan_level
        _x1 = channel*(x2-x1)
        _x2 = _x1+cutout.shape[1] #_x1+(x2-x1)
        _y1 = 0
        _y2 = cutout.shape[0] #(y2-y1)
        # print(cutout.shape, _x2-_x1, _y2-_y1)

        if (xflip):
            cutout = cutout[:, ::-1]
        if (yflip):
            cutout = cutout[::-1, :]

        output_img[_y1:_y2, _x1:_x2] = cutout

    hdu_in[0].data = output_img

    img_hdu = pyfits.ImageHDU(data=output_img, header=ext.header)

    reverse_headers = []
    if (xflip):
        for key in ['CD1_1', 'CD1_2']:
            img_hdu.header[key] *= -1
        img_hdu.header['CRPIX1'] = output_img.shape[1]-img_hdu.header['CRPIX1']
    if (yflip):
        for key in ['CD2_1', 'CD2_2']:
            img_hdu.header[key] *= -1
        img_hdu.header['CRPIX2'] = output_img.shape[0]-img_hdu.header['CRPIX2']
    #     reverse_headers.extend(['CD1_1', 'CD1_2'])
    # for key in reverse_headers:
    #     #img_hdu.header[key] *= -1.
    #     pass

    # delete a few headers we no longer need
    for key in ['BLANK',
                'S_EFMN11', 'S_EFMN21', 'S_EFMN31', 'S_EFMN41',
                'S_EFMN12', 'S_EFMN22', 'S_EFMN32', 'S_EFMN42',
                'S_EFMX11', 'S_EFMX21', 'S_EFMX31', 'S_EFMX41',
                'S_EFMX12', 'S_EFMX22', 'S_EFMX32', 'S_EFMX42',
                'S_OSMN11', 'S_OSMN21', 'S_OSMN31', 'S_OSMN41',
                'S_OSMN12', 'S_OSMN22', 'S_OSMN32', 'S_OSMN42',
                'S_OSMX11', 'S_OSMX21', 'S_OSMX31', 'S_OSMX41',
                'S_OSMX12', 'S_OSMX22', 'S_OSMX32', 'S_OSMX42',
                'DATASUM', 'CHECKSUM',
                ]:
        if (key in img_hdu.header):
            del img_hdu.header[key]

    # Give this CCD a name
    # img_hdu.name = 'SUP.%04d' % (int(img_hdu.header['S_FRMPOS']))
    img_hdu.name = 'SUP%d%d.SCI' % (int(img_hdu.header['S_FRMPOS'][0:2]),
                                    int(img_hdu.header['S_FRMPOS'][2:4]))

    return img_hdu

    return output_img




if __name__ == "__main__":

    for in_fn in sys.argv[1:]:
    # in_fn = sys.argv[1]
        hdu_in = pyfits.open(in_fn)

        overscan_sub_hdu = overscan(hdu_in)

        # hdu_in[0].data = overscan_sub
        out_fn = in_fn[:-5]+".overscan.fits"
        hdulist = pyfits.HDUList([pyfits.PrimaryHDU(), overscan_sub_hdu])
        hdulist.writeto(out_fn, clobber=True)

