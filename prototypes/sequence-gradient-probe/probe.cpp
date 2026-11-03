// Synthetic CPU-only Q4_K head pullback. No model files, optimization or writes.
// Compile against the pinned API headers; a syntax-only pass is NOT a native run.
#include "ggml.h"
#include "ggml-backend.h"
#include "ggml-alloc.h"
#include "ggml-cpu.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
#if defined(__APPLE__) || defined(__linux__)
#include <sys/resource.h>
#endif

namespace {
constexpr int H = 256, VOC = 17, B = 3, DIN = 7, RANK = 2;
constexpr double EPSILON = 1e-5;
constexpr const char * PIN = "8642541b255bfb5dc39cd351a178be09013a55d6";
constexpr size_t MAX_BACKEND_BYTES = 16u * 1024u * 1024u;
void need(bool ok, const char * why) { if (!ok) throw std::runtime_error(why); }

struct Fixture {
    std::vector<float> w = std::vector<float>(VOC*H);
    std::vector<float> base = std::vector<float>(B*H);
    std::vector<float> gamma = std::vector<float>(H);
    std::vector<float> a = std::vector<float>(B*DIN);
    std::vector<float> u = std::vector<float>(H*RANK);
    std::vector<float> v = std::vector<float>(RANK*DIN);
    std::vector<int> target = {2,7,13};
    Fixture() {
        for (int k=0;k<VOC;++k) for (int j=0;j<H;++j)
            w[k*H+j] = float((((k*37+j*13)%101)-50)*0.003 + (k%3-1)*0.002);
        for (int b=0;b<B;++b) for (int j=0;j<H;++j)
            base[b*H+j] = float((((b*17+j*11)%89)-44)/29.0 + b*0.1);
        for (int j=0;j<H;++j) gamma[j] = float(0.8+(j%9)/25.0);
        for (int b=0;b<B;++b) for (int i=0;i<DIN;++i)
            a[b*DIN+i] = float((((b*7+i*5)%17)-8)/9.0);
        for (int j=0;j<H;++j) for (int q=0;q<RANK;++q)
            u[j*RANK+q] = float((((j*5+q*3)%19)-9)*0.007);
        for (int q=0;q<RANK;++q) for (int i=0;i<DIN;++i)
            v[q*DIN+i] = float((((q*11+i*3)%13)-6)*0.03);
    }
};

struct State {
    std::vector<double> r = std::vector<double>(B*H);
    std::vector<double> h = std::vector<double>(B*H);
    std::vector<double> key = std::vector<double>(B*RANK);
    std::vector<double> scale = std::vector<double>(B);
};
State state(const Fixture& f, const std::vector<double>& u) {
    State s;
    for (int b=0;b<B;++b) {
        for (int q=0;q<RANK;++q) for (int i=0;i<DIN;++i)
            s.key[b*RANK+q] += double(f.a[b*DIN+i])*double(f.v[q*DIN+i]);
        double ss=0;
        for (int j=0;j<H;++j) {
            double r=f.base[b*H+j];
            for (int q=0;q<RANK;++q) r += u[j*RANK+q]*s.key[b*RANK+q];
            s.r[b*H+j]=r; ss+=r*r;
        }
        s.scale[b]=std::sqrt(ss/H+EPSILON);
        for (int j=0;j<H;++j) s.h[b*H+j]=double(f.gamma[j])*s.r[b*H+j]/s.scale[b];
    }
    return s;
}

struct CpuGraph {
    ggml_backend_t cpu=nullptr;
    ggml_context * ctx=nullptr;
    ggml_backend_buffer_t buffer=nullptr;
    ggml_tensor * w=nullptr, * h=nullptr, * z=nullptr, * delta=nullptr, * dh=nullptr;
    ggml_cgraph * forward=nullptr, * pullback=nullptr;
    size_t bytes=0;
    CpuGraph() {
        // All tensor sizes are compile-time fixed. No arbitrary dimensions/paths.
        cpu=ggml_backend_cpu_init(); need(cpu && ggml_backend_is_cpu(cpu),"CPU backend unavailable");
        ggml_backend_cpu_set_n_threads(cpu,2);
        ggml_backend_cpu_set_use_ref(cpu,true);
        ggml_init_params params{}; params.mem_size=2u*1024u*1024u; params.no_alloc=true;
        ctx=ggml_init(params); need(ctx,"metadata context allocation failed");
        w=ggml_new_tensor_2d(ctx,GGML_TYPE_Q4_K,H,VOC);
        h=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,H,B);
        delta=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,VOC,B);
        z=ggml_mul_mat(ctx,w,h);
        dh=ggml_out_prod(ctx,w,ggml_transpose(ctx,delta));
        need(w && h && delta && z && dh,"tensor construction failed");
        need(dh->ne[0]==H && dh->ne[1]==B && dh->type==GGML_TYPE_F32,"OUT_PROD shape mismatch");
        ggml_set_input(w); ggml_set_input(h); ggml_set_input(delta);
        ggml_set_output(z); ggml_set_output(dh);
        forward=ggml_new_graph_custom(ctx,128,false);
        pullback=ggml_new_graph_custom(ctx,128,false);
        need(forward && pullback,"graph metadata allocation failed");
        ggml_build_forward_expand(forward,z); ggml_build_forward_expand(pullback,dh);
        for (auto * graph : {forward,pullback}) for (int i=0;i<ggml_graph_n_nodes(graph);++i)
            need(ggml_backend_supports_op(cpu,ggml_graph_node(graph,i)),"CPU graph contains an unsupported operation");
        auto buft=ggml_backend_get_default_buffer_type(cpu);
        bytes=ggml_backend_alloc_ctx_tensors_from_buft_size(ctx,buft);
        need(bytes>0 && bytes<=MAX_BACKEND_BYTES,"backend tensor allocation exceeds synthetic bound");
        buffer=ggml_backend_alloc_ctx_tensors_from_buft(ctx,buft); need(buffer,"backend buffer allocation failed");
    }
    ~CpuGraph() {
        if (buffer) ggml_backend_buffer_free(buffer);
        if (ctx) ggml_free(ctx);
        if (cpu) ggml_backend_free(cpu);
    }
    CpuGraph(const CpuGraph&)=delete; CpuGraph& operator=(const CpuGraph&)=delete;
    std::vector<float> logits(const std::vector<double>& x) {
        need(x.size()==size_t(B*H),"hidden input shape mismatch");
        std::vector<float> f(x.size()), out(B*VOC);
        for (size_t i=0;i<x.size();++i) f[i]=static_cast<float>(x[i]);
        ggml_backend_tensor_set(h,f.data(),0,f.size()*sizeof(float));
        need(ggml_backend_graph_compute(cpu,forward)==GGML_STATUS_SUCCESS,"CPU forward failed");
        ggml_backend_tensor_get(z,out.data(),0,out.size()*sizeof(float));
        for (float v:out) need(std::isfinite(v),"nonfinite CPU logits");
        return out;
    }
    std::vector<float> hidden_gradient(const std::vector<float>& g) {
        need(g.size()==size_t(B*VOC),"logit cotangent shape mismatch");
        ggml_backend_tensor_set(delta,g.data(),0,g.size()*sizeof(float));
        need(ggml_backend_graph_compute(cpu,pullback)==GGML_STATUS_SUCCESS,"CPU OUT_PROD failed");
        std::vector<float> out(B*H);
        ggml_backend_tensor_get(dh,out.data(),0,out.size()*sizeof(float));
        for (float v:out) need(std::isfinite(v),"nonfinite OUT_PROD gradient");
        return out;
    }
};

double ce(const std::vector<float>& z,const Fixture& f,std::vector<float> * cotangent=nullptr) {
    double loss=0;
    if (cotangent) cotangent->assign(B*VOC,0);
    for (int b=0;b<B;++b) {
        double m=-std::numeric_limits<double>::infinity(),sum=0;
        for (int k=0;k<VOC;++k) m=std::max(m,double(z[b*VOC+k]));
        for (int k=0;k<VOC;++k) sum+=std::exp(double(z[b*VOC+k])-m);
        loss+=(m+std::log(sum)-double(z[b*VOC+f.target[b]]))/B;
        if (cotangent) for (int k=0;k<VOC;++k)
            (*cotangent)[b*VOC+k]=float((std::exp(double(z[b*VOC+k])-m)/sum-(k==f.target[b]?1.0:0.0))/B);
    }
    need(std::isfinite(loss),"nonfinite cross entropy"); return loss;
}
struct Grad { std::vector<double> r=std::vector<double>(B*H),u=std::vector<double>(H*RANK),v=std::vector<double>(RANK*DIN); };
Grad chain(const Fixture& f,const State& s,const std::vector<float>& dh) {
    Grad g;
    for (int b=0;b<B;++b) {
        double radial=0;
        for (int j=0;j<H;++j) radial+=double(dh[b*H+j])*double(f.gamma[j])*s.r[b*H+j];
        for (int j=0;j<H;++j) {
            double dr=double(dh[b*H+j])*double(f.gamma[j])/s.scale[b]
                     -s.r[b*H+j]*radial/(H*std::pow(s.scale[b],3));
            g.r[b*H+j]=dr;
            for (int q=0;q<RANK;++q) {
                g.u[j*RANK+q]+=dr*s.key[b*RANK+q];
                for (int i=0;i<DIN;++i) g.v[q*DIN+i]+=dr*double(f.u[j*RANK+q])*double(f.a[b*DIN+i]);
            }
        }
    }
    return g;
}

template<class T> void array(const std::vector<T>& a) {
    std::cout<<'[';
    for (size_t i=0;i<a.size();++i) { if(i)std::cout<<','; std::cout<<a[i]; }
    std::cout<<']';
}
template<class T> void matrix(const std::vector<T>& a,int rows,int cols) {
    need(a.size()==size_t(rows*cols),"JSON matrix shape mismatch");
    std::cout<<'[';
    for(int i=0;i<rows;++i) { if(i)std::cout<<','; std::cout<<'[';
        for(int j=0;j<cols;++j) { if(j)std::cout<<',';std::cout<<a[i*cols+j]; }
        std::cout<<']'; }
    std::cout<<']';
}
void quoted(const std::string& s) {
    std::cout<<'"'; for(unsigned char c:s) { if(c=='"'||c=='\\') std::cout<<'\\'<<char(c);
        else if(c>=32 && c<127) std::cout<<char(c); else std::cout<<'?'; }
    std::cout<<'"';
}
long long peak_rss_bytes() {
#if defined(__APPLE__) || defined(__linux__)
    rusage usage{}; if (getrusage(RUSAGE_SELF,&usage)) return -1;
# if defined(__APPLE__)
    return static_cast<long long>(usage.ru_maxrss);
# else
    return static_cast<long long>(usage.ru_maxrss)*1024;
# endif
#else
    return -1;
#endif
}
} // namespace

int main(int argc,char **) {
    try {
        need(argc==1,"No input files, arbitrary dimensions or flags are accepted");
        Fixture f; CpuGraph graph;
        need(ggml_blck_size(GGML_TYPE_Q4_K)==H,"unexpected Q4_K block size");
        need(ggml_get_type_traits_cpu(GGML_TYPE_Q4_K)->vec_dot_type==GGML_TYPE_Q8_K,"unexpected CPU activation dot type");
        need(!ggml_quantize_requires_imatrix(GGML_TYPE_Q4_K),"Q4_K unexpectedly requires an importance matrix");
        size_t row_bytes=ggml_row_size(GGML_TYPE_Q4_K,H);
        std::vector<uint8_t> packed(row_bytes*VOC);
        need(ggml_quantize_chunk(GGML_TYPE_Q4_K,f.w.data(),packed.data(),0,VOC,H,nullptr)==packed.size(),"quantizer output size mismatch");
        need(ggml_nbytes(graph.w)==packed.size(),"packed tensor size mismatch");
        ggml_backend_tensor_set(graph.w,packed.data(),0,packed.size());
        const auto * traits=ggml_get_type_traits(GGML_TYPE_Q4_K); need(traits && traits->to_float,"public Q4_K decoder unavailable");
        std::vector<float> decoded(VOC*H);
        for(int k=0;k<VOC;++k) traits->to_float(packed.data()+k*row_bytes,decoded.data()+k*H,H);
        std::vector<double> u(f.u.begin(),f.u.end()); State s=state(f,u);
        auto z=graph.logits(s.h); std::vector<float> delta; double loss=ce(z,f,&delta);
        auto dh=graph.hidden_gradient(delta); Grad g=chain(f,s,dh);
        double out_error=0,forward_error=0;
        for(int b=0;b<B;++b) for(int j=0;j<H;++j) {
            double expected=0;for(int k=0;k<VOC;++k)expected+=double(delta[b*VOC+k])*double(decoded[k*H+j]);
            out_error=std::max(out_error,std::abs(expected-double(dh[b*H+j])));
        }
        need(out_error<=1e-5,"native OUT_PROD disagrees with independently decoded head pullback");
        for(int b=0;b<B;++b)for(int k=0;k<VOC;++k) {
            double expected=0;for(int j=0;j<H;++j)expected+=double(decoded[k*H+j])*double(float(s.h[b*H+j]));
            forward_error=std::max(forward_error,std::abs(expected-double(z[b*VOC+k])));
        }
        std::vector<double> direction(H*RANK); double norm=0;
        for(int j=0;j<H;++j)for(int q=0;q<RANK;++q) { double v=((j*13+q*7)%23)-11;direction[j*RANK+q]=v;norm+=v*v; }
        norm=std::sqrt(norm);for(double&v:direction)v/=norm;
        double surrogate=0;for(size_t j=0;j<g.u.size();++j)surrogate+=g.u[j]*direction[j];
        std::vector<double> steps={1e-2,1e-3,1e-4,1e-5,1e-6},fd;
        for(double step:steps) {
            auto plus=u,minus=u;for(size_t j=0;j<u.size();++j) {plus[j]+=step*direction[j];minus[j]-=step*direction[j];}
            double derivative=(ce(graph.logits(state(f,plus).h),f)-ce(graph.logits(state(f,minus).h),f))/(2*step);
            need(std::isfinite(derivative),"nonfinite quantized forward finite difference");fd.push_back(derivative);
        }
        long long rss=peak_rss_bytes();need(rss<0 || rss<=256ll*1024ll*1024ll,"synthetic process RSS exceeds 256MiB");
        std::cout<<std::setprecision(17);
        std::cout<<"{\"schema\":\"synthetic-q4k-sequence-gradient-probe-v1\",\"epsilon\":"<<EPSILON;
        std::cout<<",\"runtime\":{\"expected_source_commit\":\""<<PIN<<"\",\"runtime_source_commit_verified_by_binary\":false,\"ggml_version\":";quoted(ggml_version());
        std::cout<<",\"backend\":\"CPU\",\"cpu_use_ref\":true,\"threads\":2,\"backend_tensor_bytes\":"<<graph.bytes<<",\"peak_rss_bytes\":"<<rss<<"}";
        std::cout<<",\"fixtures\":{\"head_decoded_f32\":";matrix(decoded,VOC,H);
        std::cout<<",\"base_r_f32\":";matrix(f.base,B,H);std::cout<<",\"gamma_f32\":";array(f.gamma);
        std::cout<<",\"a_f32\":";matrix(f.a,B,DIN);std::cout<<",\"u_f32\":";matrix(f.u,H,RANK);
        std::cout<<",\"v_f32\":";matrix(f.v,RANK,DIN);std::cout<<",\"target_ids\":";array(f.target);std::cout<<'}';
        std::cout<<",\"native\":{\"cpu_logits\":";matrix(z,B,VOC);
        std::cout<<",\"out_prod_hidden_gradient\":";matrix(dh,B,H);std::cout<<",\"analytic_r_gradient\":";matrix(g.r,B,H);
        std::cout<<",\"u_gradient\":";matrix(g.u,H,RANK);std::cout<<",\"v_gradient\":";matrix(g.v,RANK,DIN);
        std::cout<<",\"mean_ce\":"<<loss<<",\"out_prod_vs_decoded_fixed_cotangent_max_abs\":"<<out_error;
        std::cout<<",\"forward_vs_decoded_h_f32_max_abs\":"<<forward_error;
        std::cout<<",\"quantized_forward_finite_differences\":{\"objective\":\"actual_CPU_Q4_K_Q8_K_mean_CE\",\"direction\":\"unit_F64_U_direction\",\"steps\":";array(steps);
        std::cout<<",\"central_differences\":";array(fd);std::cout<<",\"native_cotangent_decoded_linear_surrogate_directional_gradient\":"<<surrogate;
        std::cout<<",\"finite_difference_agreement_required\":false}";
        std::cout<<",\"rounding\":\"F32 fixtures; host F64 factor/RMS calculation; hidden and logit cotangent rounded to F32 at native graph inputs\"}";
        std::cout<<",\"scope\":\"Synthetic packed-head pullback and factor-chain probe only; no model, optimization, Metal equivalence or mathematical-answer gain\"}\n";
        ggml_quantize_free(); return 0;
    } catch(const std::exception& e) {std::cerr<<"probe failed: "<<e.what()<<'\n';return 1;}
}
