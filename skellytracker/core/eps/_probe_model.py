"""The probe model of the EP verification: Conv and Relu on a 1x3x64x64 input, opset 17.

`skellytracker/tests/test_eps_probe_model.py` makes the same bytes with the `onnx` package. The
package does not need `onnx` at run time.
"""

import base64

import numpy as np

_MODEL = """
CAgSDXNrZWxseXRyYWNrZXI6oAgKKwoBeAoBdwoBYhIBYxoEY29udiIEQ29udioRCgRwYWRzQAFAAUABQAGgAQcKEgoBYxIBeRoEcmVsdSIEUm
VsdRIFcHJvYmUq8AYICAgDCAMIAxABQgF3SuAGbL8APX9GB7298iM+39XWPKEhCb79Irk9eemmPuZzcj7+JzS+VfmhvuqOH75uRSk8Ts0Uv+wK
YL0Dep++4HU7vo9UC74Y8qG9PcHSPRRxhT6XngO9RuiuPjNKKr4h+bM90klnPoWJwDz4VT6+MvZrvgpb6r3VemE9KzuBvh8yVr3iCyO923QKPp
rPWz1p87U9UGEnvnC5BL2eskg+wCi/Pg8pob5ByME+pUWsPgYESD66Zoc9frqgvWyguj6/6fo++ZvmPlJVqD6R+rY9L6qavvrzkbq+Dig+B+mk
vnBNyj0YF9w92y8yPi2Rl75XZSm+cXTfvRK8lb6bo94+A+j9vbVuqD2fY4S9Pa/KPpcBqT5mIyI+TgYNv1UcVTwPBi8+0IGAPigvHr6rN+k+4g
OpvudZKb5wX28+fu1IPDMnAD8tC0E9AhkivgFQwb2tqou+BoujvqZiIT5IxxQ+GrSlPtgtQb6sNNg+eySTvTaGyT4blt29okg8vr3Hfz2oBoQ+
st8kPTjlFb4Wrau+BGWzvtOvAD7VXX0+1zwovcqEib6xf18+8+OjvqGLNr4H+x4+UAIQvzzSxT1q5hS+Cc7fPGcJm7wT9049QbUxPoUkQr694r
U+SOE5Pt3+Vz5DGpU+Yp9JPooVWD7T0Jo8h6C2vkNJCr3p/kS+Zxy2vu1ThD11jBG+otCDvg+Bhb73bYk92qO3PUlGqT5a+mO7AVuFPmp9sz6h
OJM+JGEXv4JFnT6s4q09j/jYPYURvj2/+MM9Q4qjPXzDt73JaPO+rw7fvF/BTb7LQoo+NNmTvSH1qjzHf1m+J7gCviv1PLvGIL6+ZvOZPWk82b
yrxZe+pnwZv2JXAz7vXJi9oq4HvoXScb1Jgug+GvxLvHFlsTxnWL6+AtzSPn7gaj5SkYg+e0RDPOOpaj6+7L099vkcPnnYG71cqLy+gLGDPsKs
9771sXW9WG5RvXF8hb6j9Rw+OyNNvTWt371ZFAU+KwL0vRnKsT7r8bM9xtvyva3d+L51ZKe+RR2LPjVGT7zF9ZC9ElbSPtotpL6r7RW+A/fxvT
MaFj5x3Sm+9Agdvol1zb6ktjo+Jl9OPqfn872WQic9bnWlvn6R8b2yYLA+//wKPf/cEz93hUm+hY0UPq4ySL1w2RA+KikICBABQgFiSiBFTey7
rqoPvyIcXr/yOURAFmeevfgQAcCwCia/A5QtP1obCgF4EhYKFAgBEhAKAggBCgIIAwoCCEAKAghAYhsKAXkSFgoUCAESEAoCCAEKAggICgIIQA
oCCEBCBAoAEBE=
"""


def model_bytes() -> bytes:
    return base64.b64decode(_MODEL)


def probe_input() -> np.ndarray:
    """The fixed input `x` of the probe model."""
    return np.random.default_rng(1).standard_normal((1, 3, 64, 64)).astype(np.float32)
