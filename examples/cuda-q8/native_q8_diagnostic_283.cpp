#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include "native_effective_q8.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace {

std::array<float, p283::width> activation(const std::filesystem::path & path, bool authored_bundle) {
    std::ifstream stream(path, std::ios::binary | std::ios::ate);
    const std::size_t bytes = (p283::width + (authored_bundle ? 4 : 0)) * sizeof(float);
    if (!stream || stream.tellg() != static_cast<std::streamoff>(bytes)) throw std::runtime_error("Wrong F32 input extent");
    std::array<float, p283::width> values{};
    stream.seekg(0);
    if (!stream.read(reinterpret_cast<char *>(values.data()), sizeof(values)) ||
        !std::all_of(values.begin(), values.end(), [](float x) { return std::isfinite(x); })) {
        throw std::runtime_error("Short or nonfinite F32 activation input");
    }
    return values;
}

void write_new(const std::filesystem::path & path, const void * data, DWORD bytes) {
    const HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) throw std::runtime_error("Could not create new diagnostic output");
    DWORD written = 0;
    const bool complete = WriteFile(file, data, bytes, &written, nullptr) && written == bytes && FlushFileBuffers(file);
    CloseHandle(file);
    if (!complete) throw std::runtime_error("Could not flush exact diagnostic output");
}

void fixture() {
    std::array<std::uint8_t, p283::block_count * p283::block_bytes> bits{};
    bits[1] = 0x3c;
    bits[4] = 127;
    bits[5] = 255;
    bits[36] = 1;
    bits[40] = 3;
    const auto got = p283::decode_effective(bits);
    if (got[0] != 127.f || got[1] != -1.f || got[32] != std::ldexp(3.f, -24) || got.back() != 0.f) {
        throw std::runtime_error("CPU Q8 half/code decode fixture differed");
    }
}

}

int wmain(int argc, wchar_t ** argv) {
    try {
        if (argc == 2 && std::wstring_view(argv[1]) == L"--fixture") {
            fixture();
            std::cout << "{\"passed\":true,\"gpu_used\":false,\"mode\":\"decode_fixture\"}\n";
            return 0;
        }
        if (argc != 6 && argc != 7) throw std::runtime_error("Usage: --run|--validate-only cubin input q8-blocks.bin effective.f32 [--authored-bundle]");
        const auto mode = std::wstring_view(argv[1]);
        const bool bundle = argc == 7;
        if ((mode != L"--run" && mode != L"--validate-only") ||
            (bundle && std::wstring_view(argv[6]) != L"--authored-bundle")) throw std::runtime_error("Unknown diagnostic mode");
        const std::filesystem::path cubin(argv[2]), input(argv[3]), packed(argv[4]), effective(argv[5]);
        if (std::filesystem::absolute(packed) == std::filesystem::absolute(effective) ||
            std::filesystem::exists(packed) || std::filesystem::exists(effective)) {
            throw std::runtime_error("Diagnostic output paths must be fresh and distinct");
        }
        fixture();
        const auto values = activation(input, bundle);
        if (mode == L"--validate-only") {
            p283::validate_exact_cubin(cubin);
            std::cout << "{\"passed\":true,\"gpu_used\":false,\"mode\":\"validate_only\",\"activation_values\":5120}\n";
            return 0;
        }
        p283::NativeEffectiveQ8 engine(cubin);
        const auto result = engine.quantize(values);
        write_new(packed, result.blocks.data(), static_cast<DWORD>(result.blocks.size()));
        write_new(effective, result.effective.data(), static_cast<DWORD>(sizeof(result.effective)));
        std::cout << "{\"passed\":true,\"gpu_used\":true,\"mode\":\"exact_installed_cubin\","
                     "\"activation_values\":5120,\"q8_block_bytes\":5760,\"effective_f32_bytes\":20480}\n";
        return 0;
    } catch (const std::exception & error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
