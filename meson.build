project('neo_vague_denoiser', 'cpp',
  default_options : ['buildtype=release', 'b_ndebug=if-release', 'cpp_std=c++17'],
  meson_version : '>=0.64.0',
  version : '1.0.1'
)

cpp = meson.get_compiler('cpp')
is_msvc_like = cpp.get_argument_syntax() == 'msvc'
is_x86 = host_machine.cpu_family().startswith('x86')

# Prefer system VapourSynth/AviSynth+ headers, fall back to the vendored ones (VapourSynth API 4).
system_vs_dep = dependency('vapoursynth', version : '>=55', required : false)
if system_vs_dep.found()
  vapoursynth_dep = system_vs_dep.partial_dependency(compile_args : true, includes : true)
else
  vapoursynth_dep = declare_dependency(include_directories : include_directories('include/vapoursynth'))
endif

system_avs_dep = dependency('avisynth', required : false)
if system_avs_dep.found()
  avisynth_dep = system_avs_dep.partial_dependency(compile_args : true, includes : true)
else
  avisynth_dep = declare_dependency(include_directories : include_directories('include/avisynth'))
endif

version_conf = { 'VERSION' : meson.project_version() }

# src/version.hpp.in -> <builddir>/version.hpp
configure_file(
  input : 'src/version.hpp.in',
  output : 'version.hpp',
  configuration : version_conf
)

sources = [
  'main.cpp',
  'src/cpuid.cpp',
  'src/core.cpp',
]

if host_machine.system() == 'windows'
  version_rc = configure_file(
    input : 'src/version.rc.in',
    output : 'version.rc',
    configuration : version_conf
  )
  sources += import('windows').compile_resources(version_rc)
endif

cpp_args = []
deps = [vapoursynth_dep, avisynth_dep]

# C++17 parallel execution (std::execution::par) for processing the planes of a frame
# concurrently. MSVC ships it with the standard library, libstdc++ needs TBB.
par_opt = get_option('parallel')
if not par_opt.disabled() and cpp.has_header('execution')
  if is_msvc_like
    cpp_args += ['-DHAS_EXECUTION', '-DENABLE_PAR']
  else
    tbb_dep = dependency('tbb', required : par_opt)
    if tbb_dep.found()
      cpp_args += ['-DHAS_EXECUTION', '-DENABLE_PAR']
      deps += tbb_dep
    endif
  endif
elif par_opt.enabled()
  error('parallel execution requested but the <execution> header is not available')
endif

# The SIMD routines are selected at runtime, so they are built as separate
# objects with their own instruction set flags. Other architectures (e.g. arm64) use the C routines.
simd_libs = []
if is_x86
  sse_args = []
  sse41_args = []
  avx_args = []
  avx2_args = []
  if is_msvc_like
    avx_args += '/arch:AVX'
    avx2_args += '/arch:AVX2'
    if host_machine.cpu_family() == 'x86'
      sse_args += '/arch:SSE'
      sse41_args += '/arch:SSE2'
    endif
  else
    sse_args += '-msse'
    sse41_args += '-msse4.1'
    avx_args += '-mavx'
    avx2_args += ['-mfma', '-mavx2']
  endif
  simd_sources = {
    'neo_vd_sse' : ['src/core_SSE.cpp', sse_args],
    'neo_vd_sse41' : ['src/corepadding_SSE41.cpp', sse41_args],
    'neo_vd_avx' : ['src/core_AVX.cpp', avx_args],
    'neo_vd_avx2' : ['src/corepadding_AVX2.cpp', avx2_args],
  }
  foreach name, simd : simd_sources
    simd_libs += static_library(name, simd[0],
      cpp_args : simd[1],
      include_directories : include_directories('.'),
      pic : true,
      gnu_symbol_visibility : 'hidden'
    )
  endforeach
endif

# VapourSynth only autoloads *.dylib on macOS, while Meson defaults to *.so for modules.
module_kwargs = {}
if host_machine.system() == 'darwin'
  module_kwargs += {'name_suffix' : 'dylib'}
endif

if get_option('python_package')
  # Same layout as the VapourSynth PyPI package autoloads from: site-packages/vapoursynth/plugins
  py = import('python').find_installation(pure : false)
  install_dir = join_paths(py.get_install_dir(), 'vapoursynth', 'plugins')
else
  libdir = join_paths(get_option('prefix'), get_option('libdir'))
  if system_vs_dep.found()
    libdir = system_vs_dep.get_variable(pkgconfig : 'libdir', default_value : libdir)
  endif
  install_dir = join_paths(libdir, 'vapoursynth')
endif

shared_module('neo-vague-denoiser', sources,
  cpp_args : cpp_args,
  dependencies : deps,
  include_directories : include_directories('.', 'include/dualsynth'),
  link_with : simd_libs,
  install : true,
  install_dir : install_dir,
  gnu_symbol_visibility : 'hidden',
  kwargs : module_kwargs
)
