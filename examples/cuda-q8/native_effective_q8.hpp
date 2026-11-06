#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>

namespace p283 {

inline constexpr std::size_t width = 5120;
inline constexpr std::size_t block_count = width / 32;
inline constexpr std::size_t block_bytes = 36;
inline constexpr const char * kernel_symbol = "_Z13quantize_q8_1PKfPvxxxxxj5uint3";
inline constexpr const char * cubin_sha256 = "ea66ff6e8a06b80ad225b4d0942166fb36bc22e57ccd92af14c56021405b8e76";

struct Q8Result {
    std::array<std::uint8_t, block_count * block_bytes> blocks{};
    std::array<float, width> effective{};
};

void validate_exact_cubin(const std::filesystem::path & path);
std::array<float, width> decode_effective(const std::array<std::uint8_t, block_count * block_bytes> & blocks);

// Construction retains the device primary context. Calls push it and restore the caller's context.
// One instance owns its transfer buffers and must be used serially.
class NativeEffectiveQ8 {
public:
    explicit NativeEffectiveQ8(const std::filesystem::path & cubin, int device_ordinal = 0);
    ~NativeEffectiveQ8();
    NativeEffectiveQ8(const NativeEffectiveQ8 &) = delete;
    NativeEffectiveQ8 & operator=(const NativeEffectiveQ8 &) = delete;
    Q8Result quantize(std::span<const float, width> activation);

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}
