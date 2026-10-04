#!/usr/bin/env python3
"""Smoke test for the Neo Vague Denoiser VapourSynth plugin.

Usage: python3 test/test_neo_vd.py [path/to/libneo-vague-denoiser.so]

Without arguments the plugin is expected to be autoloaded (e.g. from the
installed wheel). Requires the vapoursynth Python module only.
"""
import sys

import vapoursynth as vs

core = vs.core

WIDTH, HEIGHT, FRAMES = 96, 64, 4


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)
    print("ok  ", msg)


def checkerboard(fmt, low, high):
    """A clip whose planes alternate between two values pixel by pixel."""
    base = core.std.BlankClip(width=WIDTH, height=HEIGHT, length=1, format=fmt)

    def fill(n, f):
        f = f.copy()
        for p in range(f.format.num_planes):
            plane = f[p]
            h, w = plane.shape
            for y in range(h):
                for x in range(w):
                    plane[y, x] = high if (x + y) % 2 else low
        return f

    return core.std.ModifyFrame(base, base, fill)


def main():
    args = sys.argv[1:]
    if args:
        core.std.LoadPlugin(args[0])
    vd = core.neo_vd.VagueDenoiser

    # 1. Supported formats: integer and float formats of both color families
    #    must be accepted and produce frames of the input format and size.
    for fmt in [vs.GRAY8, vs.GRAY16, vs.GRAYS, vs.YUV420P8, vs.YUV422P10,
                vs.YUV444P16, vs.YUV420PS, vs.RGB24, vs.RGB48, vs.RGBS]:
        f = core.get_video_format(fmt)
        clip = core.std.BlankClip(width=WIDTH, height=HEIGHT, length=FRAMES, format=fmt)
        out = vd(clip, threshold=2.0, nsteps=6)
        check(out.format.id == fmt and out.width == WIDTH and out.height == HEIGHT,
              "%s keeps format and dimensions" % f.name)
        frame = out.get_frame(FRAMES - 1)
        check(frame.width == WIDTH and frame.height == HEIGHT, "%s frame is produced" % f.name)

    # 2. A constant clip stays constant (denoising a flat picture must not alter it)
    #    for each CPU dispatch level, which also exercises every SIMD routine.
    for opt in range(0, 6):
        for fmt, value in [(vs.YUV420P8, 128), (vs.YUV420P16, 32768), (vs.GRAYS, 0.5)]:
            f = core.get_video_format(fmt)
            clip = core.std.BlankClip(width=WIDTH, height=HEIGHT, length=2, format=fmt,
                                      color=[value] * f.num_planes)
            frame = vd(clip, opt=opt).get_frame(1)
            ok = True
            for p in range(f.num_planes):
                plane = frame[p]
                h, w = plane.shape
                for y, x in [(0, 0), (3, 5), (h - 1, w - 1)]:
                    if abs(float(plane[y, x]) - value) > 1e-6:
                        ok = False
            check(ok, "%s constant clip is unchanged with opt=%d" % (f.name, opt))

    # 3. Noise is reduced: a strong checkerboard gets smoothed.
    noisy = checkerboard(vs.GRAY8, 96, 160)
    before = noisy.get_frame(0)[0]
    after = vd(noisy, threshold=50, nsteps=3).get_frame(0)[0]
    diff_before = abs(int(before[10, 10]) - int(before[10, 11]))
    diff_after = abs(int(after[10, 10]) - int(after[10, 11]))
    check(diff_after < diff_before, "checkerboard noise is reduced (%d -> %d)" % (diff_before, diff_after))

    # 4. planes selects what gets processed: unselected planes are copied.
    yuv = checkerboard(vs.YUV444P8, 96, 160)
    src = yuv.get_frame(0)
    only_luma = vd(yuv, threshold=50, nsteps=3, planes=[0]).get_frame(0)
    check(only_luma[1][10, 10] == src[1][10, 10] and only_luma[2][10, 11] == src[2][10, 11] and
          only_luma[0][10, 10] != src[0][10, 10],
          "planes=[0] filters luma only and copies chroma")

    # 5. Out of order frame requests work (the filter is fmParallel with per thread buffers).
    clip = vd(core.std.BlankClip(width=WIDTH, height=HEIGHT, length=12, format=vs.YUV420P16))
    for n in [7, 2, 11, 0, 5]:
        clip.get_frame(n)
    check(True, "out of order frame requests")

    # 6. Invalid arguments and unsupported formats are rejected with an error instead of a crash.
    for kwargs in [dict(threshold=0), dict(method=3), dict(nsteps=0), dict(percent=101), dict(planes=[3])]:
        try:
            vd(core.std.BlankClip(width=WIDTH, height=HEIGHT, format=vs.YUV420P8), **kwargs)
        except vs.Error:
            check(True, "%r is rejected" % (kwargs,))
        else:
            raise SystemExit("FAIL: %r was accepted" % (kwargs,))
    for fmt in [vs.GRAY32, vs.GRAYH]:
        try:
            vd(core.std.BlankClip(width=WIDTH, height=HEIGHT, format=fmt))
        except vs.Error:
            check(True, "%s is rejected" % core.get_video_format(fmt).name)
        else:
            raise SystemExit("FAIL: %s was accepted" % core.get_video_format(fmt).name)

    print("all tests passed")


if __name__ == "__main__":
    main()
