# Neo Vague Denoiser (forked from VapourSynth-VagueDenoiser)

Neo Vague Denoiser Copyright(C) 2020 Xinyue Lu, and previous developers

Vague Denoiser is a wavelet based denoiser.

Basically, it transforms each frame from the video input into the wavelet domain, using Cohen-Daubechies-Feauveau 9/7. Then it applies some filtering to the obtained coefficients. It does an inverse wavelet transform after. Due to wavelet properties, it should give a nice smoothed result, and reduced noise, without blurring picture features.

It was originally written by Lefungus, and later modified by Kurosu and Fizick for further improvement. VapourSynth-VagueDenoiser was ported to VapourSynth interface and refactored by HolyWu. Kudos to them for creating and improving this fantastic tool.

This project backports VapourSynth-VagueDenoiser to AviSynth+. Parameter names follow VapourSynth-VagueDenoiser.

The VapourSynth interface uses the VapourSynth API 4 (VapourSynth R55 or newer). The AviSynth+ interface is unchanged.

## Usage

```python
# AviSynth+
LoadPlugin("neo-vague-denoiser.dll")
neo_vd(clip, threshold=2.0, nsteps=6, y=3, u=3, v=3, ...)
# VapourSynth
core.neo_vd.VagueDenoiser(clip, threshold=2.0, nsteps=6, planes=[0,1,2], ...)
```

Parameters:

[Check original VapourSynth-VagueDenoiser usage documents.](vapoursynth-vaguedenoiser.README.md)

- *y*, *u*, *v* (AviSynth+ only)

    Whether a plane is to be filtered.

        1 - Do not touch, leaving garbage data
        2 - Copy from origin
        3 - Process

    Default: 3.

- *opt*

    Sets which CPU optimizations to use.

        0 - Auto detect
        1 - Use C
        2 - Use up to SSE (for core)
        3 - Use up to SSE4.1 (for data copy)
        4 - Use up to AVX (for core)
        5 - Use up to AVX2 (for data copy)

## Installation

Prebuilt wheels for Windows x64, Linux x86_64 and macOS arm64 are attached to each [GitHub release](../../releases). They are meant for the pip-installed `VapourSynth` package:

```
pip install vapoursynth_neo_vague_denoiser-<version>-py3-none-<platform>.whl
```

The plugin is installed into `site-packages/vapoursynth/plugins`, which VapourSynth autoloads. For other VapourSynth installs (installer, system package), copy the library from the wheel into your plugin folder manually.

On architectures without x86 SIMD (e.g. macOS arm64) only the C routines are available, `opt` has no effect there.

## Compilation (Meson)

Meson and Ninja are required. The VapourSynth API 4 and AviSynth+ headers are bundled, a system installation of either is optional.

```
meson setup build
ninja -C build
```

On macOS the plugin is built as `libneo-vague-denoiser.dylib`, which is the only extension VapourSynth autoloads there. Use `pip wheel .` to build a wheel (requires `meson-python`).

The planes of a frame are processed concurrently with C++17 parallel algorithms when available (`-Dparallel=enabled|disabled|auto`). MSVC supports this out of the box, with GCC/libstdc++ the TBB library is required.

## Compilation (MSVC, CMake)

```bat
set "CONFIG=%~1"
if "%CONFIG%"=="" set "CONFIG=Release"

if not defined CMAKE_GENERATOR set "CMAKE_GENERATOR=Visual Studio 18 2026"

set "SOURCE_DIR=%~dp0."
set "BUILD_DIR=%~dp0build"

cmake --fresh -S "%SOURCE_DIR%" -B "%BUILD_DIR%\msvc-x86" -G "%CMAKE_GENERATOR%" -A Win32 || exit /b 1
cmake --fresh -S "%SOURCE_DIR%" -B "%BUILD_DIR%\msvc-x64" -G "%CMAKE_GENERATOR%" -A x64 || exit /b 1

cmake --build "%BUILD_DIR%\msvc-x86" --config "%CONFIG%" --parallel || exit /b 1
cmake --build "%BUILD_DIR%\msvc-x64" --config "%CONFIG%" --parallel || exit /b 1
```

## License

* GPLv2.
