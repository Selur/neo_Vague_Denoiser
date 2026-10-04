#pragma once

#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>

#if defined(__x86_64__) || defined(_M_X64) || defined(__i386__) || defined(_M_IX86)
  #define NEO_VD_X86 1
#endif

#ifndef _WIN32
  #include <cstdlib>
  // aligned_alloc() requires the size to be a multiple of the alignment on some
  // platforms (e.g. macOS), posix_memalign() does not.
  inline void* _aligned_malloc(size_t size, size_t alignment) {
    void* ptr = nullptr;
    if (posix_memalign(&ptr, alignment, size) != 0)
      return nullptr;
    return ptr;
  }
  #define _aligned_free(a) free(a)
#endif

struct EngineParams
{
  int process[4];
  float threshold {2.0f};
  int method {2};
  int nsteps {6};
  float percent {85.0f};

  int width[3], height[3];
  int peak;
  float lower[3] {0.0f, 0.0f, 0.0f}, upper[3] {1.0f, 1.0f, 1.0f};

  int padStrideElements[3], padSizeBytes[3], tmpSizeBytes[3];
  std::vector<float*> padBuffer[3];
  std::vector<float*> tmpBuffer[3][3]; // tmpBuffer[plane][tmpIn=0/tmpOut=1/tmp2=2]
  std::vector<std::vector<int>> hvBuffer[3][4]; // hvBuffer[plane][hL=0/hH=1/vL=2/vH=3]
  const float * analysisLow, * analysisHigh, * synthesisLow, * synthesisHigh;
};
