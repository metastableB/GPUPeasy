import torch.nn.functional as F
import inspect
import os
import traceback
from pprint import pprint


def extract_image_patches1(images, kh, kw, sh=1, sw=1, pad_h=0, pad_w=0):
    '''
    images: Image tensor to extract patches from. We assume the
        image follows [batch_size, channels, H, W].

    kh, kw: Height of patch and width of patch
    sh, sw: Stride on height and width between patches.
    pad_h, pad_w: Padding on width and height.
    '''
    lg = CLog
    msg = "Invalid shape. We expect [batch, channels, H, W]"
    assert len(images.shape) == 4, msg
    # F.Pad takes a pair of arguments for each dimension we
    # want to pad (as a list). Padding starts from the last
    # dimension. Here we have (top, bottom, left, right)
    # Before: [batch, channels, H, W]
    # After: [batch, channels, H+2*pad_h, W + 2*pad_w]
    lg.debug('Shape before padding: ', images.shape)
    x = F.pad(images, (pad_h, pad_h, pad_w, pad_w))
    lg.debug('Shape after padding: ', x.shape)
    # Get patches of size (kh, W) along the height dimension.
    # Assuming no padding;
    # Before: [batch, channels, H, W]
    # After: [batch, channels, num_patches, W, kh]
    # That is, we get patches of size (Wxkh)
    patches = x.unfold(2, kh, sh)
    lg.debug('Shape after unfolding along H: ',
             patches.shape, "kh, sh: ", kh, sh)
    # Before: [batch, channels, num_patches, W, kh]
    # After:  [batch, channels, num_patch_h, num_patch_w, kh, kw]
    patches = patches.unfold(3, kw, sw)
    lg.debug('Shape after unfolding along W: ',
             patches.shape, "kw, sw: ", kw, sw)
    # Before:  [batch, channels, num_patch_h, num_patch_w, kh, kw]
    # After:  [batch,  num_patch_h, num_patch_w, kh, kw, channels]
    # Reorder to [batch, num_patch_h, num_patch_w, kh, kw, channels]
    patches = patches.permute((0, 2, 3, 4, 5, 1))
    lg.debug('Shape after permuting: ', patches.shape)
    return patches


class CLog:
    '''
    Simple colored logger. TODO: Integrate with new python logging module.

    Note: Do not implement pprint as part of this. It is hard to handle. We
    expect user to use pprint.pforamat to obtain a formatted string and provide
    that as the argument to functions here.

    Overall this is a poor design. How do you even disable debug in this setup?
    the logger has no state.

    An alternative approach in the future would be to use decorators to catch
    each of these functions and add the print colors before execution and after
    execution.
    '''
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    PURPLE = '\e[1;95m'
    WARNING = '\033[93m'
    BOLD = '\033[1m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'
    RED = FAIL
    DEBUG = BOLD + OKCYAN + RED
    CKEY = 'CLOG_COLOR_ON'
    DKEY = 'CLOG_DEBUG_ON'
    # Set color_on to whatever int user set if available.
    COLOR_ON = bool(int(os.environ[CKEY])) if CKEY in os.environ else False
    DEBUG_ON = bool(int(os.environ[DKEY])) if DKEY in os.environ else False

    @staticmethod
    def get_ST_ED(func):
        '''get start, end'''
        strbase, c, end = None, None, ''
        if func == CLog.debug:
            strbase = '[DEBUG] '
            c = CLog.DEBUG
        elif func == CLog.info:
            strbase = '[INFO ] '
            c = CLog.OKBLUE
        elif func == CLog.warning:
            strbase = '[WARN ] '
            c = CLog.WARNING
        elif func == CLog.fail:
            strbase = '[FAIL ] '
            c = CLog.FAIL
        elif func == CLog.debug:
            c = CLog.WARNING
            strbase = '[DEBUG] '
        else:
            raise NotImplementedError
        if CLog.COLOR_ON:
            strbase = c + strbase
            end = CLog.ENDC
        return strbase, end

    @staticmethod
    def debug(*args, **kwargs):
        if CLog.DEBUG_ON is False:
            return
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        fn = os.path.basename(info.filename)
        # Regular print
        St, Ed = CLog.get_ST_ED(CLog.debug)
        print(St, end='')
        print(fn + ':%s:%s' % (info.function, info.lineno), *args,
              Ed, **kwargs)

    @staticmethod
    def info(*args, **kwargs):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        fn = os.path.basename(info.filename)
        # Regular print
        St, Ed = CLog.get_ST_ED(CLog.info)
        print(St, end='')
        print(*args, Ed, **kwargs)

    @staticmethod
    def warning(*args, **kwargs):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        fn = os.path.basename(info.filename)
        # Regular print
        St, Ed = CLog.get_ST_ED(CLog.warning)
        print(St, end='')
        print(fn + ':%s:%s' % (info.function, info.lineno), *args,
              Ed, **kwargs)

    @staticmethod
    def fail(*args, **kwargs):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        fn = os.path.basename(info.filename)
        # Regular print
        St, Ed = CLog.get_ST_ED(CLog.fail)
        print(St, end='')
        print(fn + ':%s:%s' % (info.function, info.lineno))
        print(fn + ':%s:%s' % (info.function, info.lineno))
        for cfr in list(reversed(inspect.stack()))[:-1]:
            frame = cfr[0]
            info = inspect.getframeinfo(frame)
            fname, lno, fn, code, idx = info
            print("In %s:%d: %s" % (fname, lno, fn))
            print("\t%s" % code[idx].strip())
        print(*args, Ed, **kwargs)

    @staticmethod
    def pinfo(*args, **kwargs):
        """
        pretty print info
        """
        # Regular print
        St, Ed = CLog.get_ST_ED(CLog.info)
        print(St, end='')
        pprint(*args)
        print(Ed, end='')


