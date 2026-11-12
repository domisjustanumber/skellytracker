# EP device checks

- GPU: NVIDIA GeForce RTX 3070, CC 8.6, 8192 MB, PCI 10de:2484:37553842
- Driver: 610.88 (max CUDA 13.3); scenario C: R580 or newer
- OS: Windows 11 build 10.0.26300; Python 3.12.13
- Mode: full (L2, L3, L4); precisions fp32; runs 20; duration 107 s

| Route | Predicted (L1) | Observed | Match | Stage / mode | L2 register ms | L3 session ms | L3 max diff | Install s | Download MB |
|---|---|---|---|---|---|---|---|---|---|
| cpu | ok | pass | yes | - | - | 1.1 | 0 | 0.1 | 26.8 |
| cuda-cu13 | ok | pass | yes | - | 304 | 193 | 2.86e-06 | 9.1 | 1039 |
| trt-rtx-cu13 | ok | partial | yes | L4 | 277 | 357 | 0.00847 | 4.5 | 132 |

Strict: the session built with `session.disable_cpu_ep_fallback=1`. When it did not, the numbers come from a second run with the fallback allowed.

| Route | Model | Prec | OK | Strict | Session ms | First ms | Median ms | Max diff | Rel diff | NaN/Inf | CPU nodes (op types) | VRAM MB | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cpu | rtmpose-m | fp32 | True | True | 103 | 7.2 | 5.47 | 0 | 0 | 0/0 | 247 (Add, Clip, Concat, Conv, Div, GlobalAveragePool, HardSigmoid, MatMul, MaxPool, Mul, ReduceSum, Relu, Reshape, Shape, Sigmoid, Slice, Split, Sqrt, Squeeze, Transpose, Unsqueeze) | - |  |
| cpu | rtmo-s | fp32 | True | True | 148 | 31 | 27.1 | 0 | 0 | 0/0 | 656 (Abs, Add, Clip, Concat, ConstantOfShape, Conv, Cos, Div, Equal, Erf, Exp, Expand, Flatten, Gather, Gemm, Less, MatMul, MaxPool, Mul, Neg, NonMaxSuppression, Pow, Range, ReduceMax, ReduceMean, ReduceSum, Relu, Reshape, Resize, Shape, Sigmoid, Sin, Slice, Softmax, Split, Sqrt, Sub, Tile, TopK, Transpose, Unsqueeze, Where) | - |  |
| cpu | yolox-m | fp32 | True | True | 175 | 66.7 | 63.1 | 0 | 0 | 0/0 | 415 (Add, Concat, Conv, Div, Exp, Flatten, Gather, Less, MaxPool, Mul, NonMaxSuppression, ReduceMax, Reshape, Resize, Shape, Sigmoid, Slice, Squeeze, Sub, TopK, Transpose, Unsqueeze, Where) | - |  |
| cpu | rtmw-x-384x288 | fp32 | True | True | 388 | 39.3 | 35.5 | 0 | 0 | 0/0 | 456 (Add, Clip, Concat, Conv, DepthToSpace, Div, GlobalAveragePool, HardSigmoid, MatMul, MaxPool, Mul, ReduceSum, Relu, Reshape, Resize, Shape, Sigmoid, Slice, Split, Sqrt, Squeeze, Transpose, Unsqueeze) | - |  |
| cuda-cu13 | rtmpose-m | fp32 | True | False | 161 | 373 | 2.5 | 0.00294 | 0.00288 | 0/0 | 2 (Concat, Slice) | 277 |  |
| cuda-cu13 | rtmo-s | fp32 | True | False | 211 | 428 | 7.77 | 0.0759 | 0.000119 | 0/0 | 103 (Concat, Div, Gather, Less, Mul, Reshape, Slice, Unsqueeze, Where) | 277 |  |
| cuda-cu13 | yolox-m | fp32 | True | False | 184 | 373 | 20.6 | 0.0326 | 7.98e-05 | 0/0 | 4 (Gather, Less, Reshape, Where) | 404 |  |
| cuda-cu13 | rtmw-x-384x288 | fp32 | True | False | 266 | 366 | 9.96 | 0.00978 | 0.00105 | 0/0 | 4 (Concat, Slice) | 663 |  |
| trt-rtx-cu13 | rtmpose-m | fp32 | True | True | 2092 | 1456 | 1.53 | 0.00185 | 0.00182 | 0/0 | 0 () | 309 |  |
| trt-rtx-cu13 | rtmo-s | fp32 | False | False | - | - | - | - | - | -/- | 0 () | 137 | EPFail: [ONNXRuntimeError] : 11 : EP_FAIL : [NvTensorRTRTX EP] Failed to create serialized engine for fused node: NvTensorRTRTXExecutionProvider_NvTensorRTRTXExecutionProvider_3490884969149716963_0_0 / EP log: ERROR] [tacticSupply.cpp::nvinfer1::builder::StdEngineTacticSupply::getSupportedFormats::4 |
| trt-rtx-cu13 | yolox-m | fp32 | False | False | - | - | - | - | - | -/- | 0 () | 138 | EPFail: [ONNXRuntimeError] : 11 : EP_FAIL : [NvTensorRTRTX EP] Failed to create serialized engine for fused node: NvTensorRTRTXExecutionProvider_NvTensorRTRTXExecutionProvider_17550978497922745958_0_0 / EP log: ERROR] IBuilder::buildSerializedNetworkToStream: Error Code 4: API Usage Error (ITopKLaye |
| trt-rtx-cu13 | rtmw-x-384x288 | fp32 | True | True | 2490 | 1670 | 6.91 | 0.0112 | 0.00121 | 0/0 | 0 () | 430 |  |

## Findings

- trt-rtx-cu13: L4 rtmo-s fp32 failed: EPFail: [ONNXRuntimeError] : 11 : EP_FAIL : [NvTensorRTRTX EP] Failed to create serialized engine for fused node: NvTensorRTRTXExecutionProvider_NvTensorRTRTXExecutionProvider_3490884969149716963_0_0; EP log: ERROR] [tacticSupply.cpp::nvinfer1::builder::StdEngineTacticSupply::getSupportedFormats::48] Error Code 2: Internal Error (Assertion !layerImpls.empty() failed. NonMaxSuppression_493_969 has no runners that implement it In nvinfer1::builder::StdEngin
- trt-rtx-cu13: L4 yolox-m fp32 failed: EPFail: [ONNXRuntimeError] : 11 : EP_FAIL : [NvTensorRTRTX EP] Failed to create serialized engine for fused node: NvTensorRTRTXExecutionProvider_NvTensorRTRTXExecutionProvider_17550978497922745958_0_0; EP log: ERROR] IBuilder::buildSerializedNetworkToStream: Error Code 4: API Usage Error (ITopKLayer TopK_564: TopK_564: K exceeds the maximum value allowed (3840). In nvinfer1::builder::`anonymous-namespace'::ShapeAnalyzerImpl::processCheck at C:\_src\optimiz
