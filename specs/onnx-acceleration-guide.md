## The goal
In an ideal world, we'd be able to download a single model file, run it and it runs as fast as is possible on the hardware we have. Perhaps there are different sizes of the model to choose from and download, but that's the goal.

In reality things are a little more complex, as we need to support Windows, Mac, and Linux, and we also want to support, and thus get acceleration from as many hardware types as we can. Unfortunately each of these platforms and hardware vendors have different implementations and functionality, so a single file for all is tough.

Luckily ONNX exists to try and solve this problem - you no longer need to make a model for each platform or hardware you want to accelerate on (e.g. a tensorrt engine), you can just make a standard ONNX file, then at runtime, use the relevant Execution Provider for your exact setup.

As we'll see, things aren't (yet!) quite as simple as that, so this guide is here to walk through the 3 main levels that need to be in place to get the best possible acceleration on any given platform or hardware. Those levels are:

1. Execution Providers
2. Fixed dimensions
3. Precision and Quantization
## Guide to optimal Execution Providers and Precisions
Let's start with this table, then work through what it all means in the sections below.

| **Operating System**      | **Hardware Vendor**       | **Hardware Target**                                                                 | **Optimal ONNX Execution Provider**                                                                       | **Optimal Quant / Precision**                       | **Relative Performance Tier**                                                                                                                 |
| ------------------------- | ------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Linux / Windows**       | **AMD**                   | AMD Instinct / Radeon GPU (MI200–MI300, RX 7000+)                                   | `MIGraphXExecutionProvider`<br><br>  <br><br>_(Note: `ROCmEP` is deprecated)_                             | **FP16** or **INT8 (Static)**                       | **A-Tier (High)**<br><br>Optimized graph compilation for AMD ROCm stack.                                                                      |
| **Linux / Windows**       | **Apple**                 | ARM CPU (Apple Silicon, Ampere)                                                     | `XNNPACKExecutionProvider` _(or default CPU)_                                                             | **INT8 (Static)** or **FP32**                       | **D-Tier (Low)**<br><br>Lightweight execution tailored for edge CPUs via ARM NEON.                                                            |
| **Linux / Windows**       | **Intel**                 | x86 CPU (Intel Core/Xeon w/ AVX-512 / AMX)                                          | `OpenVINOExecutionProvider`<br><br>_(Fallback: `CPUExecutionProvider` + `XNNPACK`)_                       | **INT8 (Static QDQ)** or **FP32**                   | **C-Tier (CPU Baseline)**<br><br>OpenVINO accelerates INT8 via Intel VNNI/AMX instructions.                                                   |
| **Linux / Windows**       | **Intel**                 | Intel Arc / Iris Xe GPU (Discrete & iGPU)                                           | `OpenVINOExecutionProvider`                                                                               | **FP16** or **INT8 (Static)**                       | **A-Tier to B-Tier**<br><br>Accelerated via Intel Xe matrix extension pipelines.                                                              |
| **Linux / Windows**       | **NVIDIA**                | NVIDIA Enterprise GPU (Datacenter / H100 / B200 / L40S)                             | `TensorrtExecutionProvider`                                                                               | **FP16** or **INT8 (Static QDQ)** _(FP8 supported)_ | **S-Tier (Maximum)**<br><br>Full ahead-of-time (AOT) kernel fusion & hardware memory layout optimization.                                     |
| **Linux / Windows**       | **NVIDIA**                | NVIDIA Consumer GPU (RTX 20 / 30 / 40 / 50 Series, Jetson)                          | `TensorrtExecutionProvider` / `TensorRTRTXExecutionProvider`<br><br>_(Fallback: `CUDAExecutionProvider`)_ | **FP16** or **INT8 (Static QDQ)**                   | **S-Tier to A-Tier**<br><br>TensorRT yields highest throughput via Tensor Cores; CUDA EP sits slightly lower due to cuDNN boundaries.         |
| **Linux / Windows**       | **NVIDIA**                | Older NVIDIA Consumer GPU (GTX 1080 Ti, GTX 1070, GTX 980 - Pre-RTX/Pascal/Maxwell) | `CUDAExecutionProvider`                                                                                   | **FP32** _(Avoid FP16/INT8)_                        | **B-Tier (Legacy GPU)**<br><br>Lacks Tensor Cores. FP32 provides the best throughput because FP16/INT8 undergo slow FP32 CUDA core emulation. |
| **Linux / Windows**       | **Qualcomm**              | Qualcomm Snapdragon NPU / Mobile Platform                                           | `QNNExecutionProvider`                                                                                    | **INT8 (Static)** or **FP16**                       | **A-Tier (High)**<br><br>Direct offload to Qualcomm Hexagon NPU hardware pipelines.                                                           |
| **Linux / Windows**       | **Generic / AMD / Intel** | x86 CPU (AMD Ryzen/EPYC w/ AVX2 / AVX-512)                                          | `CPUExecutionProvider` _(with oneDNN / OpenMP)_                                                           | **INT8 (Static QDQ)** or **FP32**                   | **C-Tier to D-Tier**<br><br>Vector execution via AVX instructions; compute-bound on large spatial vision models.                              |
| **Linux / Win (Native)**  | **Cross-Vendor**          | Cross-Vendor Native GPU (NVIDIA, AMD, Intel via Dawn)                               | `WebGPUExecutionProvider`<br><br>_(Plugin EP: `onnxruntime-ep-webgpu`)_                                   | **FP32** or **FP16**                                | **B-Tier to C-Tier**<br><br>Native WebGPU pipeline via Vulkan/D3D12/Metal; bypasses vendor-specific SDK tuning.                               |
| **macOS**                 | **Apple**                 | Apple Silicon iGPU / ANE (M1–M4 Series)                                             | `CoreMLExecutionProvider`                                                                                 | **FP16** _(Targeting Neural Engine)_                | **A-Tier (High)**<br><br>Offloads subgraphs to Apple Neural Engine (ANE).                                                                     |
| **Web Browser / Node.js** | **Cross-Vendor**          | Cross-Platform In-Browser GPU (Chromium, Edge)                                      | `WebGPUExecutionProvider`<br><br>_(or `'webgpu'` in ONNX Runtime Web)_                                    | **FP32**, **FP16**, or **INT4/INT8**                | **C-Tier (Portable)**<br><br>Fastest in-browser engine (2–5x vs WASM CPU), but slower than native GPU EPs due to sandbox limits.              |
| **Windows**               | **AMD**                   | AMD Radeon Consumer GPU (RX 6000/7000+)                                             | `DmlExecutionProvider` (DirectML)                                                                         | **FP16**                                            | **B-Tier (Moderate)**<br><br>Cross-vendor DX12 abstraction layer introduces slight dispatch overhead.                                         |
| **Windows**               | **Cross-Vendor**          | Any DirectX 12 GPU (NVIDIA, AMD, Intel)                                             | `DmlExecutionProvider` (DirectML)                                                                         | **FP16**                                            | **B-Tier (Moderate)**<br><br>Standardized DX12 execution layer; highly portable across consumer GPUs.                                         |

- Technically the non-RTX TensorRT Execution Provider does give better performance than CUDA, but it has to compile an engine the first time you run a model. On my old GTX1650 laptop this took 15+ minutes, with no progress indication and the GPU sitting at 100% utilization the whole time. I suspect implementing that will give more complaints than it's worth, but older hardware is also the place you want to squeeze the most performance out, so could be worth implementation with a carefully thought out UI that clearly warns the user and tells them what's going on.

- TensorRT-RTX has the same performance as regular TensorRT, but all the heavy computational optimization work has already been done for RTX 3000 and later cards. That means you get the same heavily optimized performance as TensorRT, and the startup times are only a few seconds. Best of both worlds!

- All Nvidia GPUs support CUDA as well as the TensorRT note above, but the TensorRT EP runs a heavy optimization pass for the specific GPU on the specific machine that's running it, so gains ~30% performance (depending on a whole bunch of factors).
## Execution Providers
ONNX runtime has the concept of Execution Providers - a series of plugins for ONNX runtime that take a standard ONNX file and allow you to accelerate it on a specific type of hardware. There's one for CUDA, another for TensorRT, another for CoreML (Apple silicon).

There is not (yet) a single Execution Provider that you can use on any platform and any hardware that also gets you the absolute best performance. WebGPU is trying to be that, but it is not quite yet. Keep an eye on it though, as it's getting better all the time.

So instead we must install the relevant Execution Provider plugin for the specific platform (Windows/Mac/Linux), *and* hardware model we have.

Previous versions of ONNX runtime used to come bundled in a slew od python wheels - each wheel contained both the ONNx runtime and a specific Execution Provider. For example, despite its name, `onnxruntime-gpu` was ONNX Runtime, plus the CUDA Execution Provider. As of version 1.29 of ONNX Runtime, releases are becoming much more modular, so now you install just the onnxruntime and then any Execution Providers you need are installed as separate dependencies.
### Knowing the best Execution Provider to use
Ok, so what Execution Providers do we need for which platforms and hardware? This is a constantly evolving list, so keep an eye on both the onnxruntime releases, and the Execution Provider release notes themselves.

Here's a list of all the EPs that ONNX Runtime supports: [Execution Providers \| onnxruntime](https://onnxruntime.ai/docs/execution-providers/)
### Cross-vendor Execution Providers
In an ideal world, you wouldn't have to worry about what hardware the end user has, and just use the same EP for everything. That's not quite the case just yet, but there are a couple of interesting options that trade off some absolute peak performance for ease-of-use.

- On Windows, it's possible to use the DirectML EP that lets Windows figure out how to drive the GPU.
- On Windows, Linux, and Mac there's WebGPU that attempts to be the cross-platform option that works with all GPUs. It does a decent job of accelerating things, but still isn't matched by TensorRT on Nvidia GPUs (have not tested AMD or others).

Rather than implementing and supporting every single Execution Provider for every single plaform and GPU, it might be easier to implement just the few that you know will be most used (TensorRT RTX, CoreML maybe) and leave the rest to WebGPU until there is a time where there's an appetite to support more.

That being said, there's also minimal overhead with supporting all of them if AI tools are keeping them updated.
### Installing the best Execution Provider
Now we know what Execution Provider we want to use, there are two tasks
1. Ensure the best EP and any dependencies it has are installed with the main software (and perhaps the ability to modify that later, so you can add a new GPU, and re-run the installer to change installed EPs)
2. Select the best EP at runtime

Currently there's a script I made for skellytracker to detect GPU model(s) installed, look up the best EP for that hardware (using a hard coded lookup), and install that Execution Provider.

I haven't looked at the main FMC installer and how to incorporate the same logic there. As an aside, it would be extremely useful to manually pick the installed EPs for testing purposes!
### Using the best Execution Provider
Selecting the best EP is done at onnx runtime session creation, and can be done it two ways:
1. Provide an ordered list of EPs to ONNX runtime at session creation.
2. Provide a single EP at session creation, catch the startup error if the EP does not exist.

For the first scenario, that skellytracker was previously using, you provide an ordered list of all EPs at session creation
 ONNX runtime will walk through each of them in turn, use the first one it finds, and let you know which EP is actually being used. You can also put CPU as the very last option, then you are always guaranteed to get a session started. The downside to this is that the walk down EPs takes a few seconds, slowing session startup, and if you have a misconfiguration of an EP, you can end up with a slower EP being used and you don't necessarily notice.

The second option is to do the EP detection work in skellytracker, and then only ask for that specific EP on session creation. If the session fails to start, you can then catch it and do something about it and/or get a clear signal that the EP is not correctly installed.

I was favououring option 2, as it gives a faster session startup time and a bit more control.
## Fix dimensions
Using the optimal Execution Provider gets you some very significant acceleration over using the CPU, and is what skellytracker has done so far. A further acceleration (another ~30%?) can be achieved by fixing all the dimensions of the model. Fixing dimensions allows the Execution Provider (e.g. TensorRT) to know precisely every dimension of all possible calculations, and build a highly optimized engine to accelerate things with.

In the context of machine vision models, fixing dimensions comes down to two elements:
1. Input image size
2. Input batch size
### Input image size
Skellytracker already uses fixed image sizes, so this is really a case of also ensuring the onnx model itself has a fixed input image size. This can be specified when exporting the model from wherver it comes from, e.g. when you export YOLO from Ultralytics.
### Input batch size
This is where things get a little trickier. The optimal way to run a model is with a batch size that matches the number of cameras in a session. Instead of processing one camera after another, just process all x cameras at the same time. However, there is no way to know ahead of time what the number of cameras will be. One solution to this is to have a version of the model with a fixed batch size for every possible batch size we might encounter. That's clearly going to be ridiculous to maintain, so I propose another approach.

Having inspected models we use, there are essentially two things that change between a model with batch size of 1 and batch size of n:
1. A bunch of places that say 1 now say n
2. Batch sizes above 1 have a couple of split/aggregate nodes

Using ONNX tools, it's very easy to modify the model file at runtime and set the batch size to whatever you want. That allows you to distribute a single model with say, batch 2, and then convert that model to a fixed batch size of whatever you need at runtime.

I've tested this and it works well for both YOLO26 and RTMW, so I propose a model sidecar spec addition that has a section explaining how to convert a model between the default of batch=3 and batch n.

Batch 3 may not be the best one to distribute, as 3 cameras may not be the most common number of cameras in a session, meaning model conversation must happen every time, so maybe another number works better instead. The key is to have batch >1 as a starting point, as that model will already have any split/aggregate nodes in it that can be deleted if running a  batch of 1.
### A note on caching
Obviously it's going to make sense to cache these converted models, and indeed any compiled runtimes (i.e. the TensorRT engine files it creates), but there's a trade off between space used and startup time. Also, checksums, and keeping track of which models are created from which sources will be extremely helpful in case a model is updated in the future.
## Precision & Quantization
With the optimal Execution Provider and a fixed dimension model, you get some very significant speed up vs CPU alone. I have left the most significant, but also the most complex stage for last.

All ONNX models `skellytracker` has been using up until this point have been using float32 precision. That means every value in the model is 32 bits wide. You can double your throughput by making those numbers 16 bits instead of 32. And double it again by dropping it to 8 bits. Even better than that, GPUs have hardware on them designed to optimize specific sized (precision) operations. This can mean if you have a GPU with dedicated float16 hardware, you get far more than double the performance of going from float32 to float16. Your numbers are all half the size, *and* the dedicated hardware gets used to accelerate those specific tasks even further.

Hurrah you might say! I'll have my free lunch thank you very much!

But... it's not that easy for the following reasons
1. Dropping precision lowers accuracy.
2. GPUs (even different models from the same vendor) have different hardware that accelerate different precisions.
3. Most hardware will refuse or at least run slower it doesn't support the provided precision of model.
4. Converting from one precision to the other can take significant time, so isn't something you can really do at runtime.

As with batch sizes, one way of handling this might be to have multiple versions of the same model, each with a different precision, and then pull the correct one at runtime. This is a bit annoying to maintain, but creating them all could be automated, and of we're converting batch size, the precision versions would only be one variant to keep. Creating the different precision ONNX model files is all handled by the exporter for wherever the model comes from. E.g. Ultralytics takes precision/quantization as an argument when exporting Yolo and supports float32, float16 and int8.

Another option is to pick a middle ground that is better than float32, but not absolutely optimal for every hardware platform. Unfortunately, CPU only supports float32, but a second float16 model would run dramatically faster on most GPUs.
### A note on Quantization
Going from a floating point number to an integer (e.g. float 32 > int8) requires what's called quantization, essentially rounding of values. This causes some significant loss of accuracy and needs to be accompanied by a moderate bit of re-calibration. Ultralytics handles this internally when exporting YOLO, but this step must be performed manually when exporting RTMW. It's a 3 stage process:
1. Export float32 model using MMDeploy - this includes calibration data?
2. Use onnx runtime to quantize the model to int8
3. Calibrate the model

Dropping the precision from one floating point to another (e.g. float32 to float16) does also lose precision, but because everything is floating point, the change doesn't typically require re-calibration because rounding is nowhere near as severe as moving to an integer precision.
## Implementation stages
### Stage 1 - Execution Providers
- OS and hardware detection
- Execution Provider installer
- Runtime Execution Provider selector
- Fallback handling in case an EP cannot start or cannot work with the selected model
### Stage 2 - Batch size conversion
- Export YOLO26 [ONNX Export for YOLO26 Models \| Ultralytics](https://docs.ultralytics.com/integrations/onnx) with batch = 1, 2, and 3
- Compare them to find the differences
- Write a sidecar that describes how to convert from b=3 to any other batch size
- Write the spec to do it
- Implement code to do it
### Stage 3 - Batch conversion calculator & sidecar generator
- Take three versions of the same model with batch=1, batch=2, batch=3
- Compare the models to see what changes between them
- Ideally create scripts to find the differences between batch sizes and create the sidecar sections explaining how to do that
	- Else an AI plugin that can do that part
- Create a sidecar for the model family that includes batch conversion instructions
- Ideally can run as a GH Action?
### Stage 4 - Export YOLO26 Models
- Create a script that exports YOLO26 models, then passes the exported models to the above sidecar creation tool to create the sidcars
- [domisjustanumber/YOLO-Exporter](https://github.com/domisjustanumber/YOLO-Exporter)
 - Possibly also upload the results to a HuggingFace repo 
### Stage 5 - Precision selection
 - Expand the existing EP selection logic to also select a precision/quant of a model at runtime
### Stage 6 - RTMW with fixed batches and different precisions
- Now do the same for RTMW using MMDeploy
	- I started building a repo to do this here: [domisjustanumber/mmlabs-model-exporter](https://github.com/domisjustanumber/mmlabs-model-exporter)
	- Official docs [How to convert model — mmdeploy 1.3.1 documentation](https://mmdeploy.readthedocs.io/en/latest/02-how-to-run/convert_model.html)
### Stage 7 - Add RF-DETR as an object detector
- [domisjustanumber/RF-DETR-Exporter](https://github.com/domisjustanumber/RF-DETR-Exporter)
- Probably replicate the YOLO26 Exporter and modify it for RF-DETR