// Isolated raw five-shot MMLU four-choice scoring through the pinned Windows CUDA runtime.
#include <llama.h>
#include <ggml-backend.h>
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <chrono>
#include <ctime>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iterator>
#include <iostream>
#include <limits>
#include <memory>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <io.h>

using Clock = std::chrono::steady_clock;
static double ms(Clock::time_point a) { return std::chrono::duration<double,std::milli>(Clock::now()-a).count(); }
static std::string quote(const std::string &s) {
    std::string o="\"";
    for(size_t i=0;i<s.size();) {
        unsigned char c=s[i];
        if(c=='"'||c=='\\') {o+='\\';o+=c;++i;}
        else if(c<32) { char b[7];snprintf(b,sizeof b,"\\u%04x",c);o+=b;++i; }
        else if(c<128) {o+=c;++i;}
        else {
            size_t n=c>=0xf0&&c<=0xf4?4:c>=0xe0&&c<=0xef?3:c>=0xc2&&c<=0xdf?2:0;
            bool ok=n && i+n<=s.size();
            for(size_t j=1;ok&&j<n;++j)ok=((unsigned char)s[i+j]&0xc0)==0x80;
            if(ok&&n==3)ok=!(c==0xe0&&(unsigned char)s[i+1]<0xa0)&&!(c==0xed&&(unsigned char)s[i+1]>=0xa0);
            if(ok&&n==4)ok=!(c==0xf0&&(unsigned char)s[i+1]<0x90)&&!(c==0xf4&&(unsigned char)s[i+1]>=0x90);
            if(ok){o.append(s,i,n);i+=n;}else{o+="\\ufffd";++i;}
        }
    }
    return o+'"';
}
static std::string number(double x){if(!std::isfinite(x))return "null";std::ostringstream s;s<<std::setprecision(17)<<x;return s.str();}
static std::string arr(const std::vector<std::string>&v){std::string s="[";for(size_t i=0;i<v.size();++i){if(i)s+=',';s+=v[i];}return s+"]";}
static std::string obj(const std::vector<std::pair<std::string,std::string>>&v){std::string s="{";for(size_t i=0;i<v.size();++i){if(i)s+=',';s+=quote(v[i].first)+":"+v[i].second;}return s+"}";}
// Only external model output is streamed here; no host-agent reasoning exists in this driver.
static void live(const std::string&event,const std::string&id,int step,
                 std::vector<std::pair<std::string,std::string>> fields={}) {
    auto now=std::chrono::system_clock::now();auto epoch_ms=std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
    std::time_t seconds=std::chrono::system_clock::to_time_t(now);std::tm utc{};char stamp[32];
    if (gmtime_s(&utc, &seconds) != 0 || !std::strftime(stamp, sizeof stamp, "%Y-%m-%dT%H:%M:%S", &utc))
        throw std::runtime_error("UTC timestamp formatting failed");
    std::ostringstream timestamp;timestamp<<stamp<<'.'<<std::setw(3)<<std::setfill('0')<<(epoch_ms%1000)<<'Z';
    std::vector<std::pair<std::string,std::string>> all={{"timestamp_utc",quote(timestamp.str())},{"origin",quote("local_qwen_model_runtime")},{"event",quote(event)},{"case_id",quote(id)},{"step",std::to_string(step)}};
    all.insert(all.end(),fields.begin(),fields.end());std::cerr<<"WR_LIVE "<<obj(all)<<std::endl;
}
namespace fs = std::filesystem;

static std::string utf8(const std::wstring &value) {
    if (value.empty()) return {};
    const int length = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(),
        static_cast<int>(value.size()), nullptr, 0, nullptr, nullptr);
    if (!length) throw std::runtime_error("Invalid UTF-16 command line or path");
    std::string result(length, '\0');
    if (!WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(),
            static_cast<int>(value.size()), result.data(), length, nullptr, nullptr))
        throw std::runtime_error("UTF-16 to UTF-8 conversion failed");
    return result;
}

static fs::path local_path(const std::string &value) {
    if (value.empty()) throw std::runtime_error("Empty path");
    const auto input = fs::u8path(value);
    if (input.has_root_name() && !input.is_absolute())
        throw std::runtime_error("Drive-relative paths are unsupported");
    const auto path = fs::absolute(input).lexically_normal().make_preferred();
    const auto drive = path.root_name().native();
    if (drive.size() != 2 || drive[1] != L':' || !path.has_root_directory())
        throw std::runtime_error("Use a local Windows drive path");
    const auto drive_type = GetDriveTypeW(path.root_path().c_str());
    if (drive_type != DRIVE_FIXED && drive_type != DRIVE_REMOVABLE)
        throw std::runtime_error("Use a fixed or removable local Windows drive");
    for (const auto &part : path.relative_path()) {
        const auto name = part.native();
        if (name.empty()) continue;
        if (name.back() == L'.' || name.back() == L' ' ||
            name.find_first_of(L"<>:\"|?*") != std::wstring::npos ||
            std::any_of(name.begin(), name.end(), [](wchar_t c) { return c < 32; }))
            throw std::runtime_error("Unsafe Windows path component");
        auto stem = name.substr(0, name.find(L'.'));
        while (!stem.empty() && stem.back() == L' ') stem.pop_back();
        for (auto &c : stem) if (c >= L'a' && c <= L'z') c -= L'a' - L'A';
        if (stem == L"CON" || stem == L"PRN" || stem == L"AUX" || stem == L"NUL" ||
            stem == L"CONIN$" || stem == L"CONOUT$" ||
            (stem.size() == 4 && (stem.substr(0, 3) == L"COM" || stem.substr(0, 3) == L"LPT") &&
                std::wstring(L"123456789\u00b9\u00b2\u00b3").find(stem[3]) != std::wstring::npos))
            throw std::runtime_error("Windows device paths are unsupported");
    }
    return path;
}

static std::string sha(const void *data, size_t n) {
    if (n > std::numeric_limits<ULONG>::max()) throw std::runtime_error("SHA-256 input too large");
    struct Provider {
        BCRYPT_ALG_HANDLE handle = nullptr;
        ~Provider() { if (handle) BCryptCloseAlgorithmProvider(handle, 0); }
    } provider;
    unsigned char digest[32];
    if (BCryptOpenAlgorithmProvider(&provider.handle, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0 ||
        BCryptHash(provider.handle, nullptr, 0, static_cast<PUCHAR>(const_cast<void *>(data)),
            static_cast<ULONG>(n), digest, sizeof digest) < 0)
        throw std::runtime_error("Windows BCrypt SHA-256 failed");
    std::ostringstream result;
    for (const auto byte : digest) result << std::hex << std::setw(2) << std::setfill('0') << unsigned(byte);
    return result.str();
}

static std::string read_file(const std::string &p, size_t limit = 65536) {
    const auto path = local_path(p);
    if (!fs::is_regular_file(path)) throw std::runtime_error("Prompt must be a regular file: " + p);
    std::ifstream f(path, std::ios::binary);
    if (!f) throw std::runtime_error("Cannot read prompt file: " + p);
    std::string s(limit + 1, '\0');
    f.read(s.data(), s.size());
    if (f.bad()) throw std::runtime_error("Prompt read failed: " + p);
    s.resize(static_cast<size_t>(f.gcount()));
    if (s.size() > limit) throw std::runtime_error("Prompt byte cap exceeded");
    if (s.find('\0') != std::string::npos) throw std::runtime_error("NUL in prompt is not supported");
    return s;
}

static void output(const std::string &p, const std::string &s) {
    if (p.empty()) { std::cout << s << '\n'; return; }
    struct File {
        HANDLE handle;
        ~File() { if (handle != INVALID_HANDLE_VALUE) CloseHandle(handle); }
    } file{CreateFileW(local_path(p).c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW,
        FILE_ATTRIBUTE_NORMAL, nullptr)};
    if (file.handle == INVALID_HANDLE_VALUE) throw std::runtime_error("Output must be a fresh writable path");
    const auto write = [&file](const char *data, size_t count) {
        while (count) {
            DWORD written = 0;
            const auto chunk = static_cast<DWORD>(std::min<size_t>(count, 1024 * 1024));
            if (!WriteFile(file.handle, data, chunk, &written, nullptr) || !written)
                throw std::runtime_error("Output write failed");
            data += written;
            count -= written;
        }
    };
    write(s.data(), s.size());
    write("\n", 1);
}

static void verify_loaded(const fs::path &dir, const wchar_t *dll) {
    const HMODULE module = GetModuleHandleW(dll);
    wchar_t path[32768];
    const DWORD length = module ? GetModuleFileNameW(module, path, static_cast<DWORD>(std::size(path))) : 0;
    const auto expected = (dir / dll).native();
    if (!length || length >= std::size(path) ||
        CompareStringOrdinal(path, -1, expected.c_str(), -1, TRUE) != CSTR_EQUAL)
        throw std::runtime_error("Runtime DLL outside the declared directory: " + utf8(dll));
}

static ggml_backend_dev_t load_cuda0(const std::string &runtime) {
    const auto dir = fs::canonical(local_path(runtime));
    if (!fs::is_directory(dir)) throw std::runtime_error("Runtime must be a directory");
    for (const auto dll : {L"llama.dll", L"ggml.dll", L"ggml-base.dll"}) verify_loaded(dir, dll);
    if (std::string(ggml_commit()).rfind("8642541b", 0) != 0)
        throw std::runtime_error("Unexpected GGML build commit");
    const auto cuda = ggml_backend_load(utf8((dir / L"ggml-cuda.dll").native()).c_str());
    if (!cuda || std::strcmp(ggml_backend_reg_name(cuda), "CUDA") != 0 ||
        ggml_backend_reg_dev_count(cuda) == 0)
        throw std::runtime_error("Pinned CUDA backend or CUDA0 unavailable");
    verify_loaded(dir, L"ggml-cuda.dll");
    const auto dev = ggml_backend_reg_dev_get(cuda, 0);
    if (!dev || ggml_backend_dev_type(dev) != GGML_BACKEND_DEVICE_TYPE_GPU ||
        std::strcmp(ggml_backend_dev_name(dev), "CUDA0") != 0)
        throw std::runtime_error("Pinned CUDA backend did not expose CUDA0 as a GPU");
    // llama.cpp still needs a CPU backend for host operations, including input tensors.
    const auto cpu = ggml_backend_load(utf8((dir / L"ggml-cpu-x64.dll").native()).c_str());
    if (!cpu || !ggml_backend_dev_by_type(GGML_BACKEND_DEVICE_TYPE_CPU))
        throw std::runtime_error("Required CPU host backend unavailable");
    verify_loaded(dir, L"ggml-cpu-x64.dll");
    return dev;
}

struct BackendSession {
    BackendSession() { llama_backend_init(); }
    ~BackendSession() { llama_backend_free(); }
};


struct Item {
    std::string id;
    std::string prompt;
    std::string digest;
};

struct Options {
    std::string model, out, runtime, manifest;
    bool validate = false;
};

static Options options(int argc, wchar_t **argv) {
    Options o;
    std::set<std::string> seen;
    for (int i = 1; i < argc; ++i) {
        const auto key = utf8(argv[i]);
        if (!seen.insert(key).second) throw std::runtime_error("Duplicate option: " + key);
        if (key == "--validate-only") {
            o.validate = true;
            continue;
        }
        if (++i == argc) throw std::runtime_error("Missing value for " + key);
        const auto value = utf8(argv[i]);
        if (key == "--model") o.model = value;
        else if (key == "--runtime-dir") o.runtime = value;
        else if (key == "--manifest") o.manifest = value;
        else if (key == "--output") o.out = value;
        else throw std::runtime_error("Unknown option: " + key);
    }
    if (o.manifest.empty()) throw std::runtime_error("Supply --manifest");
    if (!o.validate && (o.model.empty() || o.runtime.empty() || o.out.empty()
            || !fs::is_regular_file(local_path(o.model)))) {
        throw std::runtime_error("Scoring requires a model, runtime, and fresh output");
    }
    if (!o.out.empty()) {
        const auto out = local_path(o.out);
        if (fs::exists(out) || !fs::is_directory(out.parent_path()))
            throw std::runtime_error("Output must be fresh with an existing parent");
    }
    return o;
}

static std::vector<Item> read_manifest(const std::string &path) {
    std::istringstream manifest(read_file(path, 1024 * 1024));
    std::vector<Item> items;
    std::set<std::string> ids;
    const std::regex identifier("^[a-z0-9_-]{1,80}$");
    std::string row;
    while (std::getline(manifest, row)) {
        const auto tab = row.find('\t');
        if (tab == std::string::npos || row.find('\t', tab + 1) != std::string::npos)
            throw std::runtime_error("Expected ID and prompt path in manifest");
        auto id = row.substr(0, tab);
        if (!std::regex_match(id, identifier) || !ids.insert(id).second || items.size() == 370)
            throw std::runtime_error("Invalid, duplicate, or excess manifest ID");
        auto prompt = read_file(row.substr(tab + 1));
        if (prompt.size() < 7 || prompt.compare(prompt.size() - 7, 7, "Answer:") != 0)
            throw std::runtime_error("Raw MMLU prompt lacks exact Answer: suffix");
        auto digest = sha(prompt.data(), prompt.size());
        items.push_back({std::move(id), std::move(prompt), std::move(digest)});
    }
    if (items.empty()) throw std::runtime_error("Empty manifest");
    return items;
}

static std::vector<llama_token> tokenize(const llama_vocab *vocab, const std::string &text,
                                        bool add_special) {
    auto n = llama_tokenize(vocab, text.data(), static_cast<int32_t>(text.size()),
                            nullptr, 0, add_special, false);
    if (n == INT32_MIN) throw std::runtime_error("Tokenizer overflow");
    if (n < 0) n = -n;
    std::vector<llama_token> tokens(static_cast<size_t>(n));
    if (llama_tokenize(vocab, text.data(), static_cast<int32_t>(text.size()), tokens.data(),
                       n, add_special, false) != n)
        throw std::runtime_error("Tokenizer count mismatch");
    return tokens;
}

static const std::vector<std::string> labels = {" A", " B", " C", " D"};

static std::vector<llama_token> choice_ids(const llama_vocab *vocab) {
    std::vector<llama_token> result;
    for (const auto &label : labels) {
        const auto ids = tokenize(vocab, label, false);
        char piece[16]{};
        if (ids.size() != 1 || ids[0] < 0 || ids[0] >= llama_vocab_n_tokens(vocab)
                || llama_token_to_piece(vocab, ids[0], piece, sizeof(piece), 0, false) != 2
                || std::string(piece, 2) != label)
            throw std::runtime_error("Exact leading-space answer is not one vocabulary token");
        result.push_back(ids[0]);
    }
    if (std::set<llama_token>(result.begin(), result.end()).size() != labels.size())
        throw std::runtime_error("Answer token IDs must differ");
    return result;
}

static bool appendable_choices(const llama_vocab *vocab, const std::string &prompt,
                               const std::vector<llama_token> &tokens,
                               const std::vector<llama_token> &choices) {
    for (size_t i = 0; i < labels.size(); ++i) {
        const auto with_label = tokenize(vocab, prompt + labels[i], true);
        if (with_label.size() != tokens.size() + 1 || with_label.back() != choices[i]
                || !std::equal(tokens.begin(), tokens.end(), with_label.begin()))
            return false;
    }
    return true;
}

int wmain(int argc, wchar_t **argv) {
    try {
        if (_setmode(_fileno(stdout), _O_BINARY) == -1 || _setmode(_fileno(stderr), _O_BINARY) == -1)
            throw std::runtime_error("Cannot configure binary stdout/stderr");
        const auto o = options(argc, argv);
        const auto items = read_manifest(o.manifest);
        if (o.validate) {
            std::vector<std::string> rows;
            for (const auto &item : items)
                rows.push_back(obj({{"id", quote(item.id)}, {"prompt_sha256", quote(item.digest)}}));
            output(o.out, obj({{"validated", "true"}, {"model_loaded", "false"}, {"prompts", arr(rows)}}));
            return 0;
        }

        const auto cuda0 = load_cuda0(o.runtime);
        BackendSession backend;
        const auto start = Clock::now();
        auto mp = llama_model_default_params();
        mp.n_gpu_layers = -1;
        mp.load_mode = LLAMA_LOAD_MODE_MMAP;
        mp.use_extra_bufts = false;
        ggml_backend_dev_t devices[] = {cuda0, nullptr};
        mp.devices = devices;
        mp.split_mode = LLAMA_SPLIT_MODE_NONE;
        mp.main_gpu = 0;
        const auto path = utf8(local_path(o.model).native());
        live("model_load_start", "", -1);
        std::unique_ptr<llama_model, decltype(&llama_model_free)>
            model(llama_model_load_from_file(path.c_str(), mp), llama_model_free);
        if (!model) throw std::runtime_error("Model load failed");
        auto cp = llama_context_default_params();
        cp.n_ctx = 4096;
        cp.n_batch = cp.n_ubatch = 64;
        cp.n_seq_max = 1;
        cp.n_threads = cp.n_threads_batch = 4;
        cp.type_k = cp.type_v = GGML_TYPE_F16;
        cp.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
        std::unique_ptr<llama_context, decltype(&llama_free)>
            ctx(llama_init_from_model(model.get(), cp), llama_free);
        if (!ctx || llama_n_ctx(ctx.get()) != 4096 || llama_n_batch(ctx.get()) != 64
                || llama_n_ubatch(ctx.get()) != 64)
            throw std::runtime_error("Unexpected context allocation");
        const auto *vocab = llama_model_get_vocab(model.get());
        const auto choices = choice_ids(vocab);
        std::vector<std::string> choice_numbers;
        for (auto id : choices) choice_numbers.push_back(std::to_string(id));
        live("context_init_complete", "", -1, {{"load_ms", number(ms(start))}});

        std::vector<std::string> rows;
        for (const auto &item : items) {
            const auto begin = Clock::now();
            auto tokens = tokenize(vocab, item.prompt, true);
            std::string status = "scored";
            std::vector<std::string> scores;
            if (tokens.empty()) {
                status = "invalid_empty_tokenization";
            } else if (tokens.size() > 2048) {
                status = "censored_prompt_token_cap";
            } else if (!appendable_choices(vocab, item.prompt, tokens, choices)) {
                status = "invalid_answer_token_boundary";
            } else {
                llama_memory_clear(llama_get_memory(ctx.get()), true);
                const auto n = static_cast<int32_t>(tokens.size());
                for (int32_t offset = 0; offset < n; offset += 64) {
                    auto batch = llama_batch_get_one(tokens.data() + offset, std::min(64, n - offset));
                    if (llama_decode(ctx.get(), batch) != 0) throw std::runtime_error("Prompt prefill failed");
                }
                llama_synchronize(ctx.get());
                const auto *logits = llama_get_logits_ith(ctx.get(), -1);
                if (!logits || !std::all_of(choices.begin(), choices.end(),
                        [logits](auto id) { return std::isfinite(logits[id]); })) {
                    status = "invalid_choice_logits";
                } else {
                    for (auto id : choices) scores.push_back(number(logits[id]));
                }
            }
            const auto elapsed = number(ms(begin));
            rows.push_back(obj({{"id", quote(item.id)}, {"prompt_sha256", quote(item.digest)},
                {"prompt_tokens", std::to_string(tokens.size())}, {"status", quote(status)},
                {"choice_logits", arr(scores)}, {"elapsed_ms", elapsed}}));
            live("mmlu_case_complete", item.id, static_cast<int>(rows.size()),
                 {{"status", quote(status)}, {"prompt_tokens", std::to_string(tokens.size())},
                  {"elapsed_ms", elapsed}});
        }
        output(o.out, obj({{"schema", quote("windows-mmlu-next-choice-logits-v1")}, {"model", quote(o.model)},
            {"runtime", quote(o.runtime)}, {"backend", quote("CUDA0")}, {"llama_build", quote(ggml_commit())},
            {"choice_pieces", arr({quote(" A"), quote(" B"), quote(" C"), quote(" D")})},
            {"choice_token_ids", arr(choice_numbers)}, {"context", "4096"}, {"batch", "64"}, {"threads", "4"},
            {"generation_tokens", "0"}, {"prompt_token_cap", "2048"}, {"rows", arr(rows)}}));
        ctx.reset();
        model.reset();
        live("run_complete", "", -1, {{"completed_prompts", std::to_string(rows.size())}});
        return 0;
    } catch (const std::exception &e) {
        live("error", "", -1, {{"message", quote(e.what())}});
        std::cerr << "mmlu_choice_score: " << e.what() << '\n';
        return 2;
    }
}
