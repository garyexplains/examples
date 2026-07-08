# Installing PyTorch, NumPy, and tqdm

The project requires the following Python packages:

* **PyTorch** for tensor operations and GPU acceleration
* **NumPy** for numerical operations
* **tqdm** for progress bars

A basic installation is:

```bash
pip install torch numpy tqdm
```

However, the correct PyTorch package may depend on your operating system and hardware. In particular, users with an NVIDIA, AMD, Intel, or Apple GPU should ensure that they install a compatible PyTorch build.

PyTorch currently requires Python 3.9 or newer. A supported 64-bit version of Python is recommended.

## Using a virtual environment

Installing the packages inside a virtual environment prevents them from conflicting with packages used by other Python projects.

### Windows

Open PowerShell or Command Prompt in the project directory:

```powershell
py -m venv .venv
.venv\\Scripts\\activate
```

Upgrade `pip`:

```powershell
python -m pip install --upgrade pip
```

### Linux and macOS

Open a terminal in the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

After activation, `python` and `pip` refer to the versions inside the virtual environment.

\---

# Windows

## CPU installation

For a computer that does not have a supported GPU, install the packages with:

```powershell
python -m pip install torch numpy tqdm
```

To explicitly request the CPU-only PyTorch package, use the CPU package repository:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy tqdm
```

## NVIDIA GPU installation

PyTorch uses CUDA to run on NVIDIA GPUs.

First, check that Windows can see the NVIDIA GPU:

```powershell
nvidia-smi
```

If this displays information about the GPU and NVIDIA driver, obtain the recommended installation command from the official PyTorch installation selector:

1. Select **Windows**.
2. Select **Pip**.
3. Select **Python**.
4. Select the recommended **CUDA** version.
5. Run the command produced by the selector.

A CUDA installation command normally has this form:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/cuXXX
python -m pip install numpy tqdm
```

Here, `cuXXX` identifies the CUDA build selected on the PyTorch website. Do not copy an arbitrary CUDA number from another computer, because the available builds and driver requirements can change. PyTorch recommends using its installation selector to choose the appropriate CUDA package.

In most cases, it is not necessary to install the complete CUDA Toolkit separately. The PyTorch wheel includes the CUDA runtime libraries it needs, but the computer must have a sufficiently recent NVIDIA display driver.

## Intel GPU installation

Recent versions of PyTorch also provide an Intel GPU, or XPU, package for supported Intel hardware:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/xpu
python -m pip install numpy tqdm
```

Intel GPU support is hardware- and driver-dependent. Consult the current PyTorch Intel GPU requirements before using this package.

AMD ROCm builds of PyTorch are generally intended for Linux rather than native Windows.

\---

# Linux

## Ensure that Python and pip are installed

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

Other Linux distributions provide equivalent Python packages through their package managers.

## CPU installation

Install the normal packages:

```bash
python -m pip install torch numpy tqdm
```

Alternatively, explicitly select the CPU-only PyTorch repository:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy tqdm
```

## NVIDIA GPU installation

Confirm that the NVIDIA driver can see the GPU:

```bash
nvidia-smi
```

Use the official PyTorch installation selector to choose:

* **Linux**
* **Pip**
* **Python**
* The recommended **CUDA** version

The resulting installation will normally resemble:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cuXXX
python -m pip install numpy tqdm
```

Replace `cuXXX` only with a repository identifier provided by the PyTorch selector. PyTorch recommends selecting the CUDA build appropriate for the machine through its current installation page.

## AMD GPU installation with ROCm

Supported AMD GPUs can run PyTorch through ROCm on Linux.

Use the PyTorch installation selector and choose:

* **Linux**
* **Pip**
* **Python**
* The compatible **ROCm** version

The command will normally have this form:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/rocmX.Y
python -m pip install numpy tqdm
```

The exact ROCm version must match a currently available PyTorch build and must support the installed AMD GPU. AMD ROCm PyTorch packages are primarily supported on Linux.

After installation, PyTorch continues to use the `torch.cuda` Python interface for many ROCm operations. Therefore, `torch.cuda.is\_available()` may return `True` on an AMD ROCm system even though the computer does not contain an NVIDIA GPU.

## Intel GPU installation

For supported Intel GPUs:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/xpu
python -m pip install numpy tqdm
```

The Intel GPU driver and hardware must meet the requirements documented by PyTorch.

\---

# macOS

## Install Python

Python can be installed from the official Python installer or through Homebrew.

Using Homebrew:

```bash
brew install python
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install the packages

The standard macOS PyTorch package supports both CPU execution and Apple’s Metal Performance Shaders backend where compatible:

```bash
python -m pip install --upgrade pip
python -m pip install torch numpy tqdm
```

On some installations, the command may be named `pip3`:

```bash
pip3 install torch numpy tqdm
```

No special CUDA package should be installed on macOS. CUDA is an NVIDIA technology and current Macs do not use it for PyTorch acceleration.

## Apple Silicon GPU acceleration

On Apple Silicon Macs, including M1, M2, M3, M4, and later compatible processors, PyTorch can use the integrated GPU through the **MPS** backend.

There is no separate Apple Silicon GPU edition to install. Install the normal macOS package:

```bash
python -m pip install torch numpy tqdm
```

Applications must then select the `mps` device:

```python
import torch

if torch.backends.mps.is\_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print(f"Using device: {device}")
```

Move tensors and models to this device:

```python
tensor = torch.ones(5, device=device)
model = model.to(device)
```

PyTorch describes `mps` as its backend for running operations through Apple’s Metal framework. Availability depends on the PyTorch build, macOS version, and whether the Mac has an MPS-compatible device.

To ensure that Python itself is running natively on Apple Silicon rather than through Rosetta, check its architecture:

```bash
python -c "import platform; print(platform.machine())"
```

The expected output on Apple Silicon is:

```text
arm64
```

If the output is `x86\_64`, install an ARM64 version of Python and recreate the virtual environment.

\---

# Verify the installation

Run:

```bash
python -c "import torch, numpy, tqdm; print('PyTorch:', torch.\_\_version\_\_); print('NumPy:', numpy.\_\_version\_\_); print('tqdm:', tqdm.\_\_version\_\_)"
```

## Check the selected accelerator

Create a file named `check\_torch.py` containing:

```python
import torch

print(f"PyTorch version: {torch.\_\_version\_\_}")

if torch.cuda.is\_available():
    print("GPU acceleration is available through CUDA or ROCm.")
    print(f"Device: {torch.cuda.get\_device\_name(0)}")
elif hasattr(torch, "xpu") and torch.xpu.is\_available():
    print("Intel XPU acceleration is available.")
    print(f"Device: {torch.xpu.get\_device\_name(0)}")
elif torch.backends.mps.is\_available():
    print("Apple Metal acceleration is available.")
    print("Device: MPS")
else:
    print("No supported GPU accelerator was detected.")
    print("PyTorch will use the CPU.")
```

Run it with:

```bash
python check\_torch.py
```

## Test a tensor on the selected device

```python
import torch

if torch.cuda.is\_available():
    device = torch.device("cuda")
elif hasattr(torch, "xpu") and torch.xpu.is\_available():
    device = torch.device("xpu")
elif torch.backends.mps.is\_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

x = torch.rand(1000, 1000, device=device)
y = x @ x

print(f"PyTorch is working on: {device}")
print(y.shape)
```

\---

# Troubleshooting

## `pip` is not recognized

Use Python to launch `pip`:

```bash
python -m pip install torch numpy tqdm
```

On Windows, this may also work:

```powershell
py -m pip install torch numpy tqdm
```

On Linux or macOS, try:

```bash
python3 -m pip install torch numpy tqdm
```

## `No matching distribution found for torch`

Check:

```bash
python --version
python -c "import platform; print(platform.architecture(), platform.machine())"
```

Make sure that:

* Python is a supported version.
* Python is 64-bit.
* An ARM64 Python installation is being used on Apple Silicon.
* `pip` is up to date.

Upgrade `pip` with:

```bash
python -m pip install --upgrade pip setuptools wheel
```

## PyTorch cannot see an NVIDIA GPU

Check:

```bash
nvidia-smi
```

Then inspect PyTorch:

```bash
python -c "import torch; print(torch.\_\_version\_\_); print(torch.version.cuda); print(torch.cuda.is\_available())"
```

If `torch.version.cuda` prints `None`, a CPU-only build of PyTorch is installed. Uninstall it and install the CUDA build selected by the official PyTorch installer:

```bash
python -m pip uninstall torch
```

Then run the appropriate CUDA installation command.

## Apple Silicon reports that MPS is unavailable

Run:

```bash
python -c "import torch; print('Built:', torch.backends.mps.is\_built()); print('Available:', torch.backends.mps.is\_available())"
```

If `is\_built()` is false, reinstall a current native macOS build of PyTorch.

If `is\_built()` is true but `is\_available()` is false, check the macOS version, the Mac hardware, and whether Python is running as ARM64. PyTorch distinguishes between an installation that was not built with MPS and a compatible build running on a system where MPS cannot be used.

## Reinstall all three packages

```bash
python -m pip uninstall torch numpy tqdm
python -m pip install --upgrade pip
python -m pip install torch numpy tqdm
```

For NVIDIA, AMD, or Intel acceleration, reinstall `torch` from the appropriate PyTorch package repository rather than using the generic final command.

# Replacing a CPU-only installation

If PyTorch was previously installed without GPU support, installing a GPU-enabled package over it may leave incompatible files or dependencies in the environment. The safest approach is to uninstall the existing PyTorch packages before installing the appropriate accelerated version.

## Check the current installation

Run:

```bash
python -c "import torch; print('PyTorch:', torch.\_\_version\_\_); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is\_available())"
```

On an NVIDIA system, a CPU-only installation will normally show:

```text
CUDA build: None
CUDA available: False
```

Before replacing PyTorch, confirm that the correct virtual environment is active:

```bash
python -c "import sys; print(sys.executable)"
```

## Remove the existing CPU-only package

Uninstall PyTorch and its related packages:

```bash
python -m pip uninstall torch torchvision torchaudio
```

If prompted, answer `y`.

Running the command a second time can confirm that no duplicate installation remains:

```bash
python -m pip uninstall torch torchvision torchaudio
```

It should then report that the packages are not installed.

Upgrading `pip` before reinstalling is also recommended:

```bash
python -m pip install --upgrade pip
```

NumPy and tqdm do not normally need to be removed.

\---

## Replace CPU-only PyTorch with NVIDIA CUDA support

This applies to supported NVIDIA GPUs on Windows or Linux.

First, confirm that the NVIDIA driver is working:

```bash
nvidia-smi
```

Next, use the official PyTorch installation selector to obtain the current command for the required CUDA build. Select the operating system, **Pip**, **Python**, and a supported CUDA version. PyTorch publishes separate package repositories for its CPU and CUDA builds.

The installation command will resemble:

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cuXXX
```

Here, `cuXXX` must be replaced by the CUDA repository identifier shown by the current PyTorch installation selector.

Do not reinstall using only:

```bash
python -m pip install torch
```

That command may install a build that does not match the intended accelerator or platform.

Verify the new installation:

```bash
python -c "import torch; print('PyTorch:', torch.\_\_version\_\_); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is\_available()); print('GPU:', torch.cuda.get\_device\_name(0) if torch.cuda.is\_available() else 'Not detected')"
```

A successful installation should report:

```text
CUDA available: True
```

The CUDA version embedded in the PyTorch package does not necessarily need to match the CUDA Toolkit installed system-wide. For normal use, the important requirement is a sufficiently recent NVIDIA driver.

\---

## Replace CPU-only PyTorch with AMD ROCm support

This applies primarily to supported AMD GPUs on Linux.

Remove the existing installation:

```bash
python -m pip uninstall torch torchvision torchaudio
```

Use the official PyTorch installation selector to choose the currently supported ROCm version. The command will resemble:

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocmX.Y
```

The exact ROCm repository identifier must come from the current PyTorch installation instructions because supported ROCm versions change between releases. PyTorch publishes version-specific ROCm wheels.

Verify the installation:

```bash
python -c "import torch; print('HIP build:', torch.version.hip); print('GPU available:', torch.cuda.is\_available()); print('GPU:', torch.cuda.get\_device\_name(0) if torch.cuda.is\_available() else 'Not detected')"
```

PyTorch uses much of the `torch.cuda` Python API for both CUDA and ROCm. Therefore, `torch.cuda.is\_available()` can return `True` on an AMD ROCm system.

\---

## Replace CPU-only PyTorch with Intel XPU support

For supported Intel GPUs, remove the existing packages:

```bash
python -m pip uninstall torch torchvision torchaudio
```

Install the Intel XPU build:

```bash
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu
```

Verify it with:

```bash
python -c "import torch; print('XPU available:', hasattr(torch, 'xpu') and torch.xpu.is\_available())"
```

When available, display the device name:

```bash
python -c "import torch; print(torch.xpu.get\_device\_name(0) if hasattr(torch, 'xpu') and torch.xpu.is\_available() else 'Intel XPU not detected')"
```

\---

## Apple Silicon: replacing an Intel or unsuitable PyTorch installation

PyTorch does not have a separate downloadable “MPS edition.” The normal native macOS ARM64 package includes support for Apple’s Metal Performance Shaders backend when the hardware and operating system are compatible.

First, check whether Python is running natively on Apple Silicon:

```bash
python -c "import platform; print(platform.machine())"
```

The result should be:

```text
arm64
```

If it reports `x86\_64`, Python is probably running through Rosetta. Install an ARM64 version of Python and create a new virtual environment. Reusing a virtual environment created with an Intel version of Python is not recommended.

Remove the existing PyTorch packages:

```bash
python -m pip uninstall torch torchvision torchaudio
```

Install the normal macOS packages:

```bash
python -m pip install torch torchvision torchaudio
python -m pip install numpy tqdm
```

Verify MPS support:

```bash
python -c "import torch; print('MPS built:', torch.backends.mps.is\_built()); print('MPS available:', torch.backends.mps.is\_available())"
```

A usable Apple GPU installation should report:

```text
MPS built: True
MPS available: True
```

Applications must explicitly select the `mps` device:

```python
import torch

if torch.backends.mps.is\_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

print(f"Using: {device}")
```

Installing a newer PyTorch package does not automatically make existing code use the Apple GPU. The model and its tensors must be moved to the `mps` device.

\---

# Installing MLX after previously installing PyTorch

MLX is not an optional PyTorch component and does not replace a CPU PyTorch wheel with an accelerated one. It is a separate NumPy-like machine-learning framework designed specifically for Apple Silicon.

PyTorch and MLX can be installed in the same virtual environment:

```bash
python -m pip install mlx
```

There is no need to uninstall PyTorch unless the project does not use it.

Verify MLX:

```bash
python -c "import mlx.core as mx; print('MLX imported successfully'); print(mx.default\_device())"
```

A simple MLX test is:

```python
import mlx.core as mx

x = mx.ones((1000, 1000))
y = x @ x

mx.eval(y)

print(y.shape)
print(mx.default\_device())
```

Apple’s official MLX installation documentation specifies that MLX can be installed with `pip` on an Apple Silicon computer.

## Installing MLX for running language models

For projects that use the higher-level MLX language-model tools, install `mlx-lm`:

```bash
python -m pip install mlx-lm
```

The `mlx-lm` package provides tools for running and fine-tuning language models using MLX on Apple Silicon.

Verify it with:

```bash
python -m mlx\_lm.generate --help
```

## PyTorch MPS versus MLX

Use **PyTorch with MPS** when:

* The application is already written using PyTorch.
* The model or library expects PyTorch tensors.
* Cross-platform compatibility is important.
* The same code should run on CPU, CUDA, ROCm, or Apple Silicon.

Use **MLX** when:

* The application is intended specifically for Apple Silicon.
* The model or project already supports MLX.
* Using MLX-native language-model tools or converted MLX models.
* Taking advantage of MLX’s unified-memory design is important.

Installing MLX does not make this PyTorch code use MLX:

```python
model.to("mps")
```

That code continues to use PyTorch’s MPS backend. Similarly, MLX arrays are not PyTorch tensors and cannot generally be passed directly to a PyTorch model without conversion.

\---

# Clean reinstall when acceleration still does not work

If the wrong package continues to load, completely recreate the virtual environment.

## Windows PowerShell

Deactivate and remove the environment:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
```

Create it again:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
```

Then install the correct CPU, CUDA, or XPU package.

## Linux and macOS

Deactivate and remove the environment:

```bash
deactivate
rm -rf .venv
```

Create it again:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Then install the appropriate PyTorch, ROCm, MPS-compatible, or MLX packages.

Creating a fresh environment is often more reliable than repeatedly installing different PyTorch builds into the same environment.

