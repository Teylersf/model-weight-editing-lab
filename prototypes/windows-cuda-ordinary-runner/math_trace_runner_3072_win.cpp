// Local bounded activation observer. Uses installed llama.cpp/ggml C APIs only.
// Does not modify weights, expose an API server, or download anything.
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

struct Options{
    std::string model,out,runtime_dir,regex="^ffn_mul-63$";
    std::vector<std::string>files,ids;std::set<std::string>exact;
    int max_tokens=1024,ctx=4096,threads=4,batch=64,gpu_layers=-1,prompt_cap=2048;
    int events=0,sample_elements=17408,trace_values=64;size_t trace_bytes=1048576;
    uint32_t seed=42;float temperature=0;bool raw=false,validate=false,check_cuda=false;
};
static long long integer(const std::string&s){size_t n=0;long long v=std::stoll(s,&n);if(n!=s.size())throw std::runtime_error("Invalid integer");return v;}
static int int_value(const std::string&s){long long v=integer(s);if(v<INT32_MIN||v>INT32_MAX)throw std::runtime_error("Integer outside int32 range");return (int)v;}
static Options options(int argc,wchar_t**argv){
    Options o;
    for(int i=1;i<argc;++i){const std::string k=utf8(argv[i]);
        if(k=="--help"){std::cout<<"Bounded native llama.cpp Windows CUDA0 trace/inference runner\n"
          "--runtime-dir DIR --model FILE --prompt-file UTF8_FILE [--id ID] (repeat for <=4 prompts)\n"
          "--check-cuda --runtime-dir DIR (never loads model)\n"
          "--output FRESH_JSON (default stdout) --seed 42 --max-tokens 1024 --ctx 4096\n"
          "--threads 4 --batch 64 --gpu-layers -1 --temperature 0 --raw\n"
          "--trace-regex REGEX --trace-tensor EXACT_NAME (repeat) --trace-max-events 0\n"
          "--trace-max-bytes 1048576 --trace-elements 17408 --trace-values 64\n"
          "--prompt-token-cap 2048 --validate-only (never loads model)\n"
          "Hard limits: generated tokens3072, context8192, prompttokens2048, prompts4,\n"
          "trace readback1MiB overall, events16/prompt and64overall, values64/event.\n"
          "Canonical server-rendered --raw prompt is REQUIRED; special pieces preserved.\n";exit(0);}
        if(k=="--raw"){o.raw=true;continue;}if(k=="--validate-only"){o.validate=true;continue;}
        if(k=="--check-cuda"){o.check_cuda=true;continue;}
        if(i+1==argc)throw std::runtime_error("Missing value for "+k);const std::string v=utf8(argv[++i]);
        if(k=="--runtime-dir")o.runtime_dir=v;else if(k=="--model")o.model=v;else if(k=="--output")o.out=v;else if(k=="--prompt-file")o.files.push_back(v);
        else if(k=="--id")o.ids.push_back(v);else if(k=="--trace-regex")o.regex=v;else if(k=="--trace-tensor")o.exact.insert(v);
        else if(k=="--seed"){long long n=integer(v);if(n<0||uint64_t(n)>=UINT32_MAX)throw std::runtime_error("seed must be 0..4294967294");o.seed=(uint32_t)n;}
        else if(k=="--temperature"){size_t p=0;o.temperature=std::stof(v,&p);if(p!=v.size())throw std::runtime_error("Invalid temperature");}
        else if(k=="--max-tokens")o.max_tokens=int_value(v);else if(k=="--ctx")o.ctx=int_value(v);
        else if(k=="--threads")o.threads=int_value(v);else if(k=="--batch")o.batch=int_value(v);else if(k=="--gpu-layers")o.gpu_layers=int_value(v);
        else if(k=="--trace-max-events")o.events=int_value(v);else if(k=="--trace-max-bytes"){long long n=integer(v);if(n<0)throw std::runtime_error("Negative trace bytes");o.trace_bytes=n;}
        else if(k=="--trace-elements")o.sample_elements=int_value(v);else if(k=="--trace-values")o.trace_values=int_value(v);
        else if(k=="--prompt-token-cap")o.prompt_cap=int_value(v);else throw std::runtime_error("Unknown option: "+k);
    }
    if(o.check_cuda) {
        if(argc!=4 || o.runtime_dir.empty()) throw std::runtime_error("Use --check-cuda --runtime-dir DIR alone");
        return o;
    }
    if(o.model.empty()||o.files.empty()||o.files.size()>4)throw std::runtime_error("Supply a model and1..4 prompt files");
    if(o.ids.empty())for(size_t i=0;i<o.files.size();++i)o.ids.push_back(std::to_string(i));
    if(o.ids.size()!=o.files.size())throw std::runtime_error("ID/prompt count mismatch");
    if(o.max_tokens<1||o.max_tokens>3072||o.ctx<128||o.ctx>8192||o.threads<1||o.threads>16||o.batch<1||o.batch>512||o.gpu_layers < -1||o.gpu_layers>256||o.prompt_cap<1||o.prompt_cap>2048)throw std::runtime_error("Runtime hard limit exceeded");
    if(o.events<0||o.events>16||o.trace_bytes>1048576||o.sample_elements<1||o.sample_elements>17408||o.trace_values<0||o.trace_values>64||o.regex.size()>256||o.exact.size()>16||!std::isfinite(o.temperature)||o.temperature<0||o.temperature>2)throw std::runtime_error("Trace/sampling hard limit exceeded");
    if(!o.raw)throw std::runtime_error("Canonical server-rendered prompt requires --raw");
    if(o.temperature!=0||o.threads!=4||o.batch!=64||o.gpu_layers!=-1)throw std::runtime_error("Math baseline requires greedy, threads4, batch64 and all-GPU");
    if(!o.regex.empty())std::regex r(o.regex);
    const auto model_path=local_path(o.model);
    if(!o.validate && (!fs::is_regular_file(model_path) || o.runtime_dir.empty()))
        throw std::runtime_error("Inference requires a regular model file and --runtime-dir");
    if(!o.out.empty()) {
        const auto out_path=local_path(o.out);
        if(fs::exists(out_path)) throw std::runtime_error("Output exists; refusing overwrite");
        if(!fs::is_directory(out_path.parent_path())) throw std::runtime_error("Output parent must exist");
    }
    for(auto&f:o.files)read_file(f);
    return o;
}
struct Trace{
    const Options&o;std::regex rx;std::vector<std::string>records,names;
    std::set<std::string>seen;size_t bytes=0,total_events=0,matched=0,skipped=0;
    std::string phase;int step=0;
    Trace(const Options&x):o(x),rx(x.regex.empty()?"a^":x.regex){}
    void begin(){records.clear();names.clear();seen.clear();matched=0;skipped=0;phase.clear();step=0;}
    bool selected(ggml_tensor*t){std::string n=t->name;return o.exact.count(n)||(!o.regex.empty()&&std::regex_search(n,rx));}
    static bool callback(ggml_tensor*t,bool ask,void*ud)noexcept{
        Trace&s=*(Trace*)ud;
        try{
            if(ask){
                if(s.phase.empty())return false;
                if(s.names.size()<256&&s.seen.insert(t->name).second)s.names.push_back(quote(t->name));
                bool yes=s.selected(t);
                if(yes)++s.matched;
                return yes&&s.records.size()<(size_t)s.o.events&&s.total_events<64&&s.bytes<s.o.trace_bytes;
            }
            if(s.records.size()>=(size_t)s.o.events||s.total_events>=64)return true;
            size_t unit=t->type==GGML_TYPE_F32?4:(t->type==GGML_TYPE_F16||t->type==GGML_TYPE_BF16?2:0);
            if(!unit||!ggml_is_contiguous(t)){++s.skipped;return true;}
            size_t total=ggml_nelements(t),count=std::min<size_t>(total,s.o.sample_elements);
            count=std::min(count,(s.o.trace_bytes-s.bytes)/unit);
            if(!count)return true;
            size_t offset=(total-count)*unit,nbytes=count*unit;
            std::vector<unsigned char>data(nbytes);ggml_backend_tensor_get(t,data.data(),offset,nbytes);
            std::vector<std::string>values;double sum=0,sq=0,lo=INFINITY,hi=-INFINITY;size_t finite=0;
            for(size_t i=0;i<count;++i){float v=0;
                if(unit==4)memcpy(&v,data.data()+i*4,4);
                else{uint16_t h;memcpy(&h,data.data()+i*2,2);if(t->type==GGML_TYPE_F16)v=ggml_fp16_to_fp32(h);else{uint32_t z=uint32_t(h)<<16;memcpy(&v,&z,4);}}
                if(i<(size_t)s.o.trace_values)values.push_back(number(v));
                if(std::isfinite(v)){++finite;sum+=v;sq+=double(v)*v;lo=std::min(lo,double(v));hi=std::max(hi,double(v));}
            }
            std::vector<std::string>shape;for(int i=0;i<GGML_MAX_DIMS;++i)shape.push_back(std::to_string(t->ne[i]));
            s.records.push_back(obj({{"tensor",quote(t->name)},{"phase",quote(s.phase)},{"step",std::to_string(s.step)},
                {"type",quote(ggml_type_name(t->type))},{"shape",arr(shape)},{"tensor_elements",std::to_string(total)},
                {"tensor_bytes",std::to_string(ggml_nbytes(t))},{"sample_scope",quote(count==total?"entire contiguous tensor":"bounded contiguous tail sample")},
                {"sample_offset_bytes",std::to_string(offset)},{"sample_bytes",std::to_string(nbytes)},{"sample_elements",std::to_string(count)},
                {"sample_sha256",quote(sha(data.data(),data.size()))},{"first_sample_values",arr(values)},
                {"statistics_scope",quote("sample only")},{"finite_count",std::to_string(finite)},{"nonfinite_count",std::to_string(count-finite)},
                {"min",number(lo)},{"max",number(hi)},{"mean",finite?number(sum/finite):"null"},
                {"rms",finite?number(std::sqrt(sq/finite)):"null"},{"l2",number(std::sqrt(sq))}}));
            s.bytes+=nbytes;++s.total_events;return true;
        }catch(...){++s.skipped;return !ask;}
    }
};
static std::string render(llama_model*m,const std::string&p,bool raw){
    if(raw)return p;const char*tmpl=llama_model_chat_template(m,nullptr);
    if(!tmpl)throw std::runtime_error("No model chat template; supply an explicitly formatted --raw prompt");
    llama_chat_message msg{"user",p.c_str()};std::vector<char>b(std::max<size_t>(8192,p.size()*3+1024));
    int n=llama_chat_apply_template(tmpl,&msg,1,true,b.data(),static_cast<int32_t>(b.size()));
    if(n<0)throw std::runtime_error("Native template unsupported; use explicitly formatted --raw prompt");
    if(n==INT32_MAX)throw std::runtime_error("Chat template byte count overflow");
    if((size_t)n>=b.size()){b.resize(n+1);n=llama_chat_apply_template(tmpl,&msg,1,true,b.data(),static_cast<int32_t>(b.size()));}
    if(n<0||(size_t)n>=b.size())throw std::runtime_error("Chat template rendering failed");return std::string(b.data(),n);
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

int wmain(int argc,wchar_t**argv){
  try{
    if(_setmode(_fileno(stdout), _O_BINARY)==-1 || _setmode(_fileno(stderr), _O_BINARY)==-1)
        throw std::runtime_error("Cannot configure binary stdout/stderr");
    Options o=options(argc,argv);
    if(o.validate){
        std::vector<std::string> hashes;
        for(const auto &path:o.files){
            const auto prompt=read_file(path);
            hashes.push_back(quote(sha(prompt.data(),prompt.size())));
        }
        output(o.out,obj({{"validated","true"},{"model_loaded","false"},{"prompts",std::to_string(o.files.size())},
            {"formatted_prompt_sha256",arr(hashes)}}));
        return 0;
    }
    Trace trace(o);
    const auto cuda0=load_cuda0(o.runtime_dir);
    BackendSession backend;
    ggml_backend_dev_props cuda_props{};
    ggml_backend_dev_get_props(cuda0,&cuda_props);
    if(o.check_cuda){
        std::unique_ptr<ggml_backend,decltype(&ggml_backend_free)> device(
            ggml_backend_dev_init(cuda0,nullptr),ggml_backend_free);
        if(!device || ggml_backend_get_device(device.get())!=cuda0)
            throw std::runtime_error("CUDA0 backend initialization failed");
        output("",obj({{"cuda_device",quote(cuda_props.name)},{"cuda_description",quote(cuda_props.description)},
            {"cuda_pci_device_id",quote(cuda_props.device_id?cuda_props.device_id:"")},
            {"llama_version",quote(llama_version())},{"ggml_version",quote(ggml_version())},
            {"ggml_commit",quote(ggml_commit())},{"model_loaded","false"}}));
        return 0;
    }
    live("run_start","",-1,{{"prompts",std::to_string(o.files.size())},
        {"max_tokens",std::to_string(o.max_tokens)},{"ctx",std::to_string(o.ctx)}});
    live("cuda_device_selected","",-1,{{"device",quote(cuda_props.name)},{"description",quote(cuda_props.description)}});
    live("model_load_start","",-1);
    auto start=Clock::now();auto mp=llama_model_default_params();mp.n_gpu_layers=o.gpu_layers;mp.load_mode=LLAMA_LOAD_MODE_MMAP;mp.use_extra_bufts=false;
    ggml_backend_dev_t devices[]={cuda0,nullptr};
    mp.devices=devices;mp.split_mode=LLAMA_SPLIT_MODE_NONE;mp.main_gpu=0;
    const auto model_path=utf8(local_path(o.model).native());
    std::unique_ptr<llama_model,decltype(&llama_model_free)>model(llama_model_load_from_file(model_path.c_str(),mp),llama_model_free);
    if(!model)throw std::runtime_error("Model load failed");
    live("model_load_complete","",-1,{{"load_elapsed_ms",number(ms(start))}});
    live("context_init_start","",-1);
    auto cp=llama_context_default_params();cp.n_ctx=o.ctx;cp.n_batch=o.batch;cp.n_ubatch=o.batch;cp.n_seq_max=1;
    cp.n_threads=o.threads;cp.n_threads_batch=o.threads;cp.no_perf=false;
    cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED;
    cp.cb_eval=o.events>0?Trace::callback:nullptr;cp.cb_eval_user_data=o.events>0?&trace:nullptr;
    std::unique_ptr<llama_context,decltype(&llama_free)>ctx(llama_init_from_model(model.get(),cp),llama_free);
    if(!ctx)throw std::runtime_error("Context allocation failed");double load_ms=ms(start);
    live("context_init_complete","",-1,{{"shared_load_ms",number(load_ms)}});
    const llama_vocab*vocab=llama_model_get_vocab(model.get());std::vector<std::string>results;
    for(size_t pi=0;pi<o.files.size();++pi){
        live("prompt_start",o.ids[pi],0,{{"prompt_index",std::to_string(pi)}});
        trace.begin();llama_synchronize(ctx.get());llama_memory_clear(llama_get_memory(ctx.get()),true);
        live("memory_reset",o.ids[pi],0);
        std::string prompt=read_file(o.files[pi]),formatted=render(model.get(),prompt,o.raw);
        int n=llama_tokenize(vocab,formatted.data(),static_cast<int32_t>(formatted.size()),nullptr,0,true,true);
        if(n==INT32_MIN)throw std::runtime_error("Tokenizer overflow");if(n<0)n=-n;
        if(n<1||n>o.prompt_cap||n+o.max_tokens>(int)llama_n_ctx(ctx.get()))throw std::runtime_error("Prompt token/context cap exceeded");
        std::vector<llama_token>tokens(n);int got=llama_tokenize(vocab,formatted.data(),static_cast<int32_t>(formatted.size()),tokens.data(),static_cast<int32_t>(tokens.size()),true,true);
        if(got!=n)throw std::runtime_error("Tokenization count mismatch");
        live("prompt_tokenized",o.ids[pi],0,{{"prompt_tokens",std::to_string(n)},{"formatted_prompt_sha256",quote(sha(formatted.data(),formatted.size()))}});
        std::unique_ptr<llama_sampler,decltype(&llama_sampler_free)>sampler(llama_sampler_chain_init(llama_sampler_chain_default_params()),llama_sampler_free);
        if(o.temperature==0)llama_sampler_chain_add(sampler.get(),llama_sampler_init_greedy());
        else{llama_sampler_chain_add(sampler.get(),llama_sampler_init_temp(o.temperature));llama_sampler_chain_add(sampler.get(),llama_sampler_init_dist(o.seed));}
        live("sampler_reset",o.ids[pi],0,{{"seed",std::to_string(o.seed)},{"sampling",quote("greedy")} });
        auto pstart=Clock::now();trace.phase="prefill";live("prefill_start",o.ids[pi],0);
        for(int at=0;at<n;at+=o.batch){trace.step=at;auto batch=llama_batch_get_one(tokens.data()+at,std::min(o.batch,n-at));if(llama_decode(ctx.get(),batch)!=0)throw std::runtime_error("Prefill decode failed");live("prefill_progress",o.ids[pi],at,{{"processed_tokens",std::to_string(std::min(at+o.batch,n))},{"total_prompt_tokens",std::to_string(n)}});}
        llama_synchronize(ctx.get());double prefill_ms=ms(pstart);live("prefill_complete",o.ids[pi],0,{{"prefill_ms",number(prefill_ms)}});auto dstart=Clock::now();
        live("decode_start",o.ids[pi],0);
        std::string text,finish="length";std::vector<std::string>ids,pids,pieces,piece_hex,completion_pieces;for(auto t:tokens)pids.push_back(std::to_string(t));int sampled_count=0;
        for(int i=0;i<o.max_tokens;++i){
            llama_token token=llama_sampler_sample(sampler.get(),ctx.get(),-1);++sampled_count;ids.push_back(std::to_string(token));
            std::vector<char>b(512);int z=llama_token_to_piece(vocab,token,b.data(),static_cast<int32_t>(b.size()),0,true);if(z==INT32_MIN)throw std::runtime_error("Token detokenization byte count overflow");if(z<0){b.resize(-z);z=llama_token_to_piece(vocab,token,b.data(),static_cast<int32_t>(b.size()),0,true);}if(z<0)throw std::runtime_error("Token detokenization failed");
            std::string piece(b.data(),z);pieces.push_back(quote(piece));std::ostringstream hex;for(unsigned char c:piece)hex<<std::hex<<std::setw(2)<<std::setfill('0')<<(unsigned)c;piece_hex.push_back(quote(hex.str()));
            live("token",o.ids[pi],i,{{"token_id",std::to_string(token)},{"piece",quote(piece)},{"piece_utf8_hex",quote(hex.str())},{"eog",llama_vocab_is_eog(vocab,token)?"true":"false"},{"decode_elapsed_ms",number(ms(dstart))}});
            if(llama_vocab_is_eog(vocab,token)){finish="eog";break;}
            completion_pieces.push_back(quote(piece));text.append(piece);
            if(i+1==o.max_tokens)break;
            trace.phase="decode";trace.step=i;auto batch=llama_batch_get_one(&token,1);if(llama_decode(ctx.get(),batch)!=0)throw std::runtime_error("Generation decode failed");
        }
        llama_synchronize(ctx.get());double decode_ms=ms(dstart);trace.phase.clear();
        results.push_back(obj({{"id",quote(o.ids[pi])},{"prompt",quote(prompt)},{"formatted_prompt",quote(formatted)},{"formatted_prompt_sha256",quote(sha(formatted.data(),formatted.size()))},
            {"text",quote(text)},{"prompt_tokens",std::to_string(n)},{"completion_tokens",std::to_string(sampled_count)},{"token_ids",arr(ids)},{"token_pieces",arr(pieces)},{"completion_token_pieces",arr(completion_pieces)},{"token_piece_utf8_hex",arr(piece_hex)},{"prompt_token_ids",arr(pids)},
            {"finish_reason",quote(finish)},{"load_ms",number(pi==0?load_ms:0)},{"model_load_shared", "true"},{"prefill_ms",number(prefill_ms)},{"decode_ms",number(decode_ms)},
            {"traces",arr(trace.records)},{"trace_matched_ask_calls",std::to_string(trace.matched)},{"trace_skipped_unsupported_or_failed",std::to_string(trace.skipped)},
            {"observed_tensor_names_bounded",arr(trace.names)}}));
        live("prompt_complete",o.ids[pi],sampled_count,{{"completion_tokens",std::to_string(sampled_count)},{"finish_reason",quote(finish)},{"prefill_ms",number(prefill_ms)},{"decode_ms",number(decode_ms)}});
    }
    std::string record=obj({{"schema_version","1"},{"logging",obj({{"enabled","true"},{"format",quote("WR_LIVE prefixed flushed JSONL on stderr")},{"scope",quote("External Qwen model token pieces and runtime phases only")}})},{"backend",obj({{"library",quote("installed Windows llama.cpp / GGML CUDA")},
        {"llama_version",quote(llama_version())},{"ggml_version",quote(ggml_version())},
        {"llama_build",quote(ggml_commit())},{"runtime_dir",quote(o.runtime_dir)},
        {"cuda_device",quote(cuda_props.name)},{"cuda_description",quote(cuda_props.description)},
        {"cuda_pci_device_id",quote(cuda_props.device_id?cuda_props.device_id:"")},{"system_info",quote(llama_print_system_info())}})},
      {"model",quote(o.model)},{"model_tensor_bytes",std::to_string(llama_model_size(model.get()))},{"load_ms",number(load_ms)},
      {"params",obj({{"seed",std::to_string(o.seed)},{"temperature",number(o.temperature)},{"sampling",quote(o.temperature==0?"greedy":"temperature + seeded categorical")},
        {"max_tokens",std::to_string(o.max_tokens)},{"ctx_requested",std::to_string(o.ctx)},{"ctx_actual",std::to_string(llama_n_ctx(ctx.get()))},
        {"batch_actual",std::to_string(llama_n_batch(ctx.get()))},{"ubatch_actual",std::to_string(llama_n_ubatch(ctx.get()))},{"threads",std::to_string(o.threads)},
        {"gpu_layers_requested",std::to_string(o.gpu_layers)},{"model_load_mode",quote("MMAP")},{"cache_type_k",quote("f16")},{"cache_type_v",quote("f16")},{"flash_attention",quote("enabled")},{"detokenize_special","true"},{"trace_enabled",o.events>0?"true":"false"},{"extra_weight_repacking","false"},{"prompt_mode",quote("required explicit raw canonical server-rendered prompt")},
        {"trace_regex",quote(o.regex)},{"trace_events_per_prompt_cap",std::to_string(o.events)},{"trace_global_event_cap","64"},{"trace_readback_global_byte_cap",std::to_string(o.trace_bytes)}})},
      {"trace_total_events",std::to_string(trace.total_events)},{"trace_total_readback_bytes",std::to_string(trace.bytes)},{"results",arr(results)}});
    output(o.out,record);ctx.reset();model.reset();live("run_complete","",-1,{{"completed_prompts",std::to_string(results.size())}});return 0;
  }catch(const std::exception&e){live("error","",-1,{{"message",quote(e.what())}});std::cerr<<"math_trace_runner_3072: "<<e.what()<<'\n';return 2;}
}
