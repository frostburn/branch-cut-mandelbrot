import argparse
import imageio
import progressbar
from _routines import ffi, lib
from pylab import *

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
    max_iter = 256
    im_buf = ffi.new("double[]", args.width * args.height)
    cut_buf = ffi.new("double[]", max_iter)
    for i in range(max_iter):
        cut_buf[i] = 100*(random()-0.5)
    for n in progressbar.progressbar(range(args.num_frames)):
        tg = n / (args.num_frames - 1)
        if tg < 0.9:
            t = tg / 0.9
            lib.mandelbrot(im_buf, args.width, args.height, -t*tanh(t*3), -0.35*t*tanh(t*3), (2*t*t-0.5), 1.01 + t*tanh(t*3)/tanh(3)*0.99, cut_buf, max_iter)
        else:
            t = (tg - 0.9)/0.1
            tp = tg / 0.9
            prev_x = -tp*tanh(tp*3)
            prev_y = -0.35*tp*tanh(tp*3)
            prev_zoom = (2*tp*tp-0.5)
            new_x = -1+0.3*t
            new_y = -0.35*(1-t)
            new_zoom = 1.5 - 2*t*t
            x = prev_x + (new_x - prev_x) * t
            y = prev_y + (new_y - prev_y) * t
            z = prev_zoom + (new_zoom - prev_zoom) * t
            lib.mandelbrot(im_buf, args.width, args.height, x, y, z, 2.0, cut_buf, max_iter)
        im = array(list(im_buf)).reshape(args.height, args.width)
        for i in range(max_iter):
            cut_buf[i] *= 0.05**args.dt
        im = sqrt(abs(im) / abs(im).max())
        frame = make_video_frame([im, im, im], indexing=None)
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
