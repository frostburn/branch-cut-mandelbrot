import argparse
import imageio
import progressbar
from _routines import ffi, lib
from pylab import *
from random import Random

RESOLUTIONS = {
    "2160p": (3840, 2160),
    "1440p": (2560, 1440),
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480),
    "360p": (640, 360),
    "240p": (426, 240),
    "160p": (284, 160),
    "80p": (142, 80),
    "40p": (71, 40),
}

def make_video_frame(rgb, indexing='ij', dither=1.0/256.0):
    if dither:
        rgb = [channel + random(channel.shape)*dither for channel in rgb]
    if indexing == 'ij':
        rgb = [channel.T for channel in rgb]
    frame = stack(rgb, axis=-1)
    frame = clip(frame, 0.0, 1.0)
    return (frame * 255).astype('uint8')


def do_render(args, writer):
    max_iter = 32
    im_buf = ffi.new("double[]", args.width * args.height)
    cut_buf = ffi.new("double[]", max_iter)
    fixed_seed = Random(1)
    for i in range(max_iter):
        cut_buf[i] = i*fixed_seed.random()
    for n in progressbar.progressbar(range(args.num_frames)):
        tg = n / (args.num_frames - 1)
        t = tg
        lib.mandelbrot(im_buf, args.width, args.height, 0.7, 0.8, 3.5, t-20, cut_buf, max_iter)
        im = array(list(im_buf)).reshape(args.height, args.width)
        # for i in range(max_iter):
        #     cut_buf[i] *= 0.05**args.dt
        bg = (im < 0)
        im /= im.max()
        fg = 1 - bg

        red = im
        green = 1 - im
        blue = 4*im*(1-im)

        blue = blue + 0.2*green
        red = 0.1 + 0.8*red + green**3
        green = 0.2 + 0.21*green

        frame = make_video_frame([red*fg + 0.15*bg, green*fg + 0.08*bg, blue*fg + 0.1*bg], indexing=None)
        writer.append_data(frame)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Render audio samples')
    parser.add_argument('outfile', type=str, help='Output file name')
    parser.add_argument('--params', type=str, help='Parameter YAML file name')
    parser.add_argument('--resolution', choices=RESOLUTIONS.keys(), help='Video and simulation grid resolution')
    parser.add_argument('--width', type=int, help='Video and simulation grid width', metavar='W')
    parser.add_argument('--height', type=int, help='Video and simulation grid height', metavar='H')
    parser.add_argument('--framerate', type=int, help='Video frame rate')
    parser.add_argument('--video-quality', type=int, help='Video quality factor')
    parser.add_argument('--video-duration', type=float, help='Duration of video to render in seconds')
    args = parser.parse_args()

    if not args.framerate:
        args.framerate = 24
    if not args.video_quality:
        args.video_quality = 10

    writer = imageio.get_writer(args.outfile, fps=args.framerate, quality=args.video_quality, macro_block_size=1)

    # Compute derived parameters
    if args.resolution:
        width, height = RESOLUTIONS[args.resolution]
        if not args.width:
            args.width = width
        if not args.height:
            args.height = height
    if (not args.width) or (not args.height):
        raise ValueError("Invalid or missing resolution")
    if not args.video_duration:
        raise ValueError("Missing video duration")
    args.aspect = args.width / args.height
    args.num_frames = int(args.video_duration * args.framerate)
    args.dt = 1.0 / args.num_frames

    do_render(args, writer)

    writer.close()
