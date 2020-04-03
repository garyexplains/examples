from PIL import Image,ImageFilter, ImageEnhance, ImageOps, ExifTags
from PIL.ImageFilter import (
    GaussianBlur, ModeFilter, MedianFilter
    )
import os, sys

def rotate_by_exif(image):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break

        exif=dict(image._getexif().items())
        if exif[orientation] == 3:
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image=image.rotate(90, expand=True)
        return image

    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        return image


def isLandscape(w, h):
    if(w > h):
        return True
    else:
        return False

# Trim to 1:1
def trim_to_sq(im):
    width, height = im.size

    if isLandscape(width, height) == True:
        offset = (width-height)/2
        (left, upper, right, lower) = (offset, 0, offset+height, height)
    else:
        offset = (height-width)/2
        (left, upper, right, lower) = (0, offset,width, offset + width)

    # Here the image "im" is cropped and resized
    im_crop = im.crop((left, upper, right, lower))
    im_crop = im_crop.resize((1080,1080))
    return im_crop

def blur_sq(origim, alreadysqim):
    width, height = origim.size
    alreadysqim = alreadysqim.filter(GaussianBlur(radius=7))   
    if isLandscape(width, height) == True:
        delta = int(1080 / (width/height))
        im_topaste = origim.resize((1080, delta))
        (left, upper) = (0, int((1080-delta)/2))
    else:
        delta = int(1080 / (height/width))
        im_topaste = origim.resize((delta, 1080))
        (left, upper) = (int((1080-delta)/2), 0)
    alreadysqim.paste(im_topaste, (left, upper))

    return alreadysqim

def filters3(alreadysqim):
    modeim = alreadysqim.filter(ModeFilter(size=9))
    bw = (0.2, 0.5, 0.3, 0)
    bwim = alreadysqim.convert("L", bw)
    shim = ImageEnhance.Sharpness(bwim)
    bwim = shim.enhance(2)
    satim = ImageEnhance.Color(alreadysqim)
    satim = satim.enhance(1.1)
    return modeim, bwim, satim


#
# Check that a filename has been provided
#
if(len(sys.argv)!=2):
    print("Please provide the name of one image to process")
    exit(-1)

#
# Process the input filename and generate some output filenames
#
infile = sys.argv[1]
root, ext = os.path.splitext(infile)
outfiletrim = root + "_sqtrim" + ext
outfileblur = root + "_sqblur" + ext
outfilef1 = root + "_sqf1" + ext
outfilef2 = root + "_sqf2" + ext
outfilef3 = root + "_sqf3" + ext

# Open the file and print its size
im = Image.open(infile)
im = rotate_by_exif(im)
print(im.format, im.size, im.mode)

# Trim to 1:1
im_crop = trim_to_sq(im)
im_crop.save(outfiletrim, "JPEG")

im_blursq = im_crop.copy()
im_blursq = blur_sq(im, im_blursq)
im_blursq.save(outfileblur, "JPEG")

im_4f = im_crop.copy()
im_f1, im_f2, im_f3 = filters3(im_4f)
im_f1.save(outfilef1, "JPEG")
im_f2.save(outfilef2, "JPEG")
im_f3.save(outfilef3, "JPEG")
