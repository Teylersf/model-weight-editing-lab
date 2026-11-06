#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <cuda.h>

#include "native_effective_q8.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace p283 {
namespace {

constexpr std::size_t expected_cubin_bytes = 89896;
constexpr unsigned block_threads = 256;
static_assert(std::endian::native == std::endian::little && sizeof(float) == 4 && sizeof(CUdeviceptr) == 8);

void check(CUresult status, const char * operation) {
    if (status == CUDA_SUCCESS) return;
    const char * name = nullptr;
    const char * description = nullptr;
    cuGetErrorName(status, &name);
    cuGetErrorString(status, &description);
    throw std::runtime_error(std::string(operation) + ": " + (name ? name : "CUDA error") +
                             " (" + (description ? description : std::to_string(status)) + ")");
}

std::vector<std::uint8_t> read_exact_cubin(const std::filesystem::path & path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file || file.tellg() != static_cast<std::streamoff>(expected_cubin_bytes)) {
        throw std::runtime_error("Unexpected exact sm_86 cubin extent");
    }
    std::vector<std::uint8_t> bytes(expected_cubin_bytes);
    file.seekg(0);
    if (!file.read(reinterpret_cast<char *>(bytes.data()), static_cast<std::streamsize>(bytes.size())) ||
        file.peek() != std::char_traits<char>::eof()) {
        throw std::runtime_error("Short or trailing exact cubin read");
    }
    BCRYPT_ALG_HANDLE alg = nullptr;
    if (BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) != 0) {
        throw std::runtime_error("Could not initialize SHA-256");
    }
    std::array<std::uint8_t, 32> hash{};
    const auto result = BCryptHash(alg, nullptr, 0, bytes.data(), static_cast<ULONG>(bytes.size()),
                                  hash.data(), static_cast<ULONG>(hash.size()));
    BCryptCloseAlgorithmProvider(alg, 0);
    if (result != 0) throw std::runtime_error("Could not hash exact cubin");
    std::ostringstream hex;
    hex << std::hex << std::setfill('0');
    for (const auto byte : hash) hex << std::setw(2) << static_cast<unsigned>(byte);
    if (hex.str() != cubin_sha256 || bytes[0] != 0x7f || bytes[1] != 'E' || bytes[2] != 'L' || bytes[3] != 'F') {
        throw std::runtime_error("Exact installed CUDA cubin SHA-256 differs");
    }
    return bytes;
}

class CurrentContext {
public:
    explicit CurrentContext(CUcontext context) { check(cuCtxPushCurrent(context), "cuCtxPushCurrent"); }
    ~CurrentContext() {
        CUcontext popped = nullptr;
        cuCtxPopCurrent(&popped);
    }
    CurrentContext(const CurrentContext &) = delete;
    CurrentContext & operator=(const CurrentContext &) = delete;
};

float scale_from_half(std::uint16_t bits) {
    const int exponent = (bits >> 10) & 31;
    const int fraction = bits & 1023;
    if (bits >= 0x8000 || exponent == 31) throw std::runtime_error("Nonfinite or negative CUDA Q8 scale");
    return exponent == 0 ? std::ldexp(static_cast<float>(fraction), -24)
                         : std::ldexp(static_cast<float>(1024 + fraction), exponent - 25);
}

struct Fastdiv {
    std::uint32_t multiplier;
    std::uint32_t shift;
    std::uint32_t divisor;
};
static_assert(sizeof(Fastdiv) == 12);

void verify_launch_abi(CUfunction function) {
    constexpr std::array<std::size_t, 9> offsets{0, 8, 16, 24, 32, 40, 48, 56, 60};
    constexpr std::array<std::size_t, 9> sizes{8, 8, 8, 8, 8, 8, 8, 4, 12};
    for (std::size_t i = 0; i < offsets.size(); ++i) {
        std::size_t offset = 0, size = 0;
        check(cuFuncGetParamInfo(function, i, &offset, &size), "cuFuncGetParamInfo");
        if (offset != offsets[i] || size != sizes[i]) throw std::runtime_error("Exact cubin kernel parameter ABI differs");
    }
    int threads = 0;
    check(cuFuncGetAttribute(&threads, CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK, function), "cuFuncGetAttribute");
    if (threads != block_threads) throw std::runtime_error("Exact cubin launch block differs");
}

}

void validate_exact_cubin(const std::filesystem::path & path) { (void) read_exact_cubin(path); }

std::array<float, width> decode_effective(const std::array<std::uint8_t, block_count * block_bytes> & blocks) {
    std::array<float, width> output{};
    for (std::size_t index = 0; index < block_count; ++index) {
        const auto * block = blocks.data() + index * block_bytes;
        const auto bits = static_cast<std::uint16_t>(block[0] | (block[1] << 8));
        const float scale = scale_from_half(bits);
        for (std::size_t lane = 0; lane < 32; ++lane) {
            const auto code = std::bit_cast<std::int8_t>(block[4 + lane]);
            if (code == -128) throw std::runtime_error("Out-of-range exact CUDA Q8 code");
            output[32 * index + lane] = scale * static_cast<float>(code);
        }
    }
    return output;
}

struct NativeEffectiveQ8::Impl {
    CUdevice device = 0;
    CUcontext context = nullptr;
    CUmodule module = nullptr;
    CUfunction function = nullptr;
    CUdeviceptr device_input = 0, device_output = 0;
    float * host_input = nullptr;
    CUstream stream = nullptr;

    ~Impl() {
        if (!context) return;
        if (cuCtxPushCurrent(context) == CUDA_SUCCESS) {
            if (stream) {
                cuStreamSynchronize(stream);
                cuStreamDestroy(stream);
            }
            if (host_input) cuMemFreeHost(host_input);
            if (device_output) cuMemFree(device_output);
            if (device_input) cuMemFree(device_input);
            if (module) cuModuleUnload(module);
            CUcontext popped = nullptr;
            cuCtxPopCurrent(&popped);
        }
        cuDevicePrimaryCtxRelease(device);
    }
};

NativeEffectiveQ8::NativeEffectiveQ8(const std::filesystem::path & cubin, int device_ordinal)
    : impl_(std::make_unique<Impl>()) {
    const auto bytes = read_exact_cubin(cubin);
    check(cuInit(0), "cuInit");
    check(cuDeviceGet(&impl_->device, device_ordinal), "cuDeviceGet");
    int major = 0, minor = 0;
    check(cuDeviceGetAttribute(&major, CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR, impl_->device), "device compute major");
    check(cuDeviceGetAttribute(&minor, CU_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR, impl_->device), "device compute minor");
    if (major != 8 || minor != 6) throw std::runtime_error("Exact installed cubin requires sm_86");
    check(cuDevicePrimaryCtxRetain(&impl_->context, impl_->device), "cuDevicePrimaryCtxRetain");
    const CurrentContext current(impl_->context);
    check(cuModuleLoadData(&impl_->module, bytes.data()), "cuModuleLoadData exact installed sm_86 cubin");
    check(cuModuleGetFunction(&impl_->function, impl_->module, kernel_symbol), "cuModuleGetFunction exact installed quantize_q8_1");
    verify_launch_abi(impl_->function);
    check(cuMemAlloc(&impl_->device_input, width * sizeof(float)), "cuMemAlloc activation");
    check(cuMemAlloc(&impl_->device_output, block_count * block_bytes), "cuMemAlloc Q8 blocks");
    void * pinned = nullptr;
    check(cuMemAllocHost(&pinned, width * sizeof(float)), "cuMemAllocHost pinned activation");
    impl_->host_input = static_cast<float *>(pinned);
    check(cuStreamCreate(&impl_->stream, CU_STREAM_NON_BLOCKING), "cuStreamCreate");
}

NativeEffectiveQ8::~NativeEffectiveQ8() = default;

Q8Result NativeEffectiveQ8::quantize(std::span<const float, width> activation) {
    if (!std::all_of(activation.begin(), activation.end(), [](float x) { return std::isfinite(x); })) {
        throw std::runtime_error("Nonfinite activation supplied to exact CUDA Q8 quantizer");
    }
    const CurrentContext current(impl_->context);
    std::copy(activation.begin(), activation.end(), impl_->host_input);
    check(cuMemcpyHtoDAsync(impl_->device_input, impl_->host_input, width * sizeof(float), impl_->stream),
          "cuMemcpyHtoDAsync exact F32 activation on kernel stream");
    std::int64_t ne00 = width, s01 = width, s02 = width, s03 = width, ne0 = width;
    std::uint32_t ne1 = 1;
    // Both outer indices are zero for grid.z=1. The exact divisor is 1, and 0/divisor is invariant to the magic multiplier.
    Fastdiv ne2{0, 0, 1};
    void * args[]{&impl_->device_input, &impl_->device_output, &ne00, &s01, &s02, &s03, &ne0, &ne1, &ne2};
    check(cuLaunchKernel(impl_->function, static_cast<unsigned>(width / block_threads), 1, 1,
                         block_threads, 1, 1, 0, impl_->stream, args, nullptr), "cuLaunchKernel exact quantize_q8_1");
    check(cuStreamSynchronize(impl_->stream), "cuStreamSynchronize exact quantize_q8_1");
    Q8Result result;
    check(cuMemcpyDtoH(result.blocks.data(), impl_->device_output, result.blocks.size()), "cuMemcpyDtoH exact Q8 blocks");
    result.effective = decode_effective(result.blocks);
    return result;
}

}
