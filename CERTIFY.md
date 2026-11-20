# Run the certify suite on your machine

You help the project when you run the certify suite. The suite tests the ONNX Runtime
execution providers (EPs) of skellytracker on your hardware. The project has only a few kinds of
hardware to test on. Your report tells the maintainers what works on yours.

You do not need to know the project. You need about 10 minutes and a terminal.

## What the suite does to your machine

- The suite runs one command and writes one report file.
- The suite needs no administrator rights. It installs no system software, with one exception:
  on Windows with an AMD GPU, Windows downloads and installs the Windows ML package of each AMD EP
  that the Windows ML catalog offers for your GPU. The plan on the screen names each EP. At the
  end, the suite removes each package that it installed, also after a failure or after Ctrl+C. It
  never removes a package that was on your machine before, also when Windows updates that package
  during the run. If a removal fails, the report has a `fail` check `remove-<package>` with the
  full package name, and the terminal tells you how to remove the package.
- If the run stops while Windows installs such a package, the suite removes the package at the end
  when the Windows ML catalog gives its package family. Windows can finish an install after the
  suite has ended. The suite does not remove such a package. To see the Windows ML packages of your
  user account, run this command in PowerShell: `Get-AppxPackage -Name "*WinML*"`.
- The suite keeps its files in the folder `.certify-work/` of your clone. It deletes that folder
  at the end. It also deletes it after a failure, after Ctrl+C, and when the process gets SIGTERM
  or SIGHUP. If you close the terminal window on Windows, Windows stops the suite with no cleanup.
  The next run then removes what the earlier run left.
- If the folder `.certify-work/` of an earlier run cannot be deleted, the suite stops before it
  runs anything. Delete the folder by hand, then run the suite again.
- The suite uses its own EP store. It does not read or change the EP store, the EP cache or the
  model cache of your user account.
- The suite downloads these files. The plan on the screen shows the size of each file before
  anything runs. 1 MB is 1,000,000 bytes.
  - The EP packs that a GPU of your machine can use: on Windows, about 111 MB for `trt-rtx` and
    about 1009 MB for `cuda`; on Linux, about 146 MB and about 1213 MB. DirectML and CoreML need
    no download.
  - The model files of the test pipeline: about 346 MB.
  - One public test image: about 0.2 MB.
- The suite deletes the model files and the test image at the end.
- The first `uv run` also makes a Python environment in `.venv/` in your clone. It downloads
  Python 3.13.18 and the dependencies of the project. It does this before the suite starts. The
  suite does not delete `.venv/`. Delete the whole clone when you finish.
- `uv` keeps its own download cache. The suite cannot delete it. Run `uv cache clean` if you want
  to remove it.
- A run takes about 5 minutes on a fast link. The plan on the screen shows the estimate for your
  machine. A slow link or a slow GPU makes it longer. Each section has a time limit. The suite
  stops a section that is over its limit and goes on.
- The suite sends nothing. You send the report yourself.

## Prerequisites

You need these on each OS:

- `git`.
- `uv`. Follow the [official install page](https://docs.astral.sh/uv/getting-started/installation/).
  `uv` downloads the right Python version itself.
- A network connection. Without one, use `--wheel-dir` (see [Options](#options)).

| OS | Notes |
|---|---|
| Windows 11 (x86_64) | An NVIDIA GPU needs a driver of R580 or later (the driver floor for `trt-rtx` is 580.88). DirectML needs a DirectX 12 GPU. |
| Ubuntu 24.04 (x86_64) | An NVIDIA GPU needs a driver of R580 or later for `cuda`, and of R590 or later for `trt-rtx` (the driver floor is 590.48.01). |
| macOS on Apple Silicon | No driver is needed. The suite tests CoreML. macOS on Intel is not supported. |

The driver floors come from the EP catalog and from the [GPU setup guide](GPU_SETUP_GUIDE.md).
The EP `trt-rtx` needs an NVIDIA GPU with compute capability 8.0 or higher (RTX 30 series or
newer). The EP `cuda` needs compute capability 7.5 or higher (GTX 16 and RTX 20 series or newer).
If your driver is older than the floor, the suite records the EP as not usable. It does not stop.

On Linux with an AMD GPU, the suite tests the MIGraphX EP when ROCm 10.0, 10.1 or 10.2 is
installed. The suite installs no ROCm.

## The three steps

1. Clone the repository at the certification tag. A tag name has the form `certify-vN`, for
   example `certify-v1`. The project gives you the tag name. Replace `<tag>` with it.

   ```sh
   git clone --branch <tag> https://github.com/domisjustanumber/skellytracker.git
   cd skellytracker
   ```

2. Run the suite.

   ```sh
   uv run python tools/certify_platform.py
   ```

3. Send the report file to the project (see [Send the report](#send-the-report)).

Do not change any file in the clone before the run. Do not run the suite on a different commit
than the tag. A report from a modified clone is not valid as evidence.

## The questions

At the start, the suite prints its plan: each section with its time estimate, the total time and
each download with its size. Then it asks `Run the suite now? [y/N]`. Type `y` and press Enter to
run. Any other answer stops the suite before it runs anything. If the terminal is not interactive
and you gave no `--yes`, the suite stops and runs nothing.

At the end, the suite asks the yes/no questions that a section has. Type `y` or `n`, or press
Enter to skip. In this version, no section has such a question.

Then the suite asks for one optional line of notes. Write a problem that you saw, if any. Do not
write your name, contact details or other personal details. Press Enter to skip.

## Options

| Option | What it does |
|---|---|
| `--only N[,N...]` | Runs only these sections, for example `--only 1,2`. The report is then not valid as evidence. |
| `--yes` | Skips the consent question. |
| `--out FILE` | Writes the report to `FILE`. The default is `certify-report-<UTC start time>.md` in the current folder. |
| `--wheel-dir DIR` | Installs the EP packs from the wheel files in `DIR` and uses no network for them. |

## The sections

| Section | What it does |
|---|---|
| 1. Checkout and versions | Records the tag, the commit, whether the clone is clean, the Python version and the package versions. |
| 2. Hardware probe | Records the CPU, the memory, the GPUs and the OS. It compares skellytracker with the OS tools. |
| 3. EP packs: install and verify | Installs each EP pack that your GPU can use. Tests each EP with a probe session. Tests DirectML on each GPU on Windows. |
| 4. Full level of certify() | Downloads the model files of the test pipeline. Then runs `skellytracker.certify("full")` on each EP and each GPU: the probe, the real pipeline on one test image against the CPU EP, the pipeline for 1, 3 and 6 cameras, also on the CPU EP, and the JPEG checks. Records the time and the GPU memory. GPU decode of JPEG frames is for `cuda` and `trt-rtx` only. |

The suite runs each section in its own process. If a section crashes or runs too long, the
suite records that and goes on. If a section wrote its complete result before it crashed or
stopped, the section keeps that result. It then has the extra check `exit` with the result
`record-only` and the reason `crashed`, `timed-out` or `hung-at-exit`. The reason
`hung-at-exit` means that the section did not end 20 seconds after its result, and the suite
stopped it.

## Read the summary table

The report file has the format `skellycertify.report/1.1.0` of the repository `skellycertify`. It
starts with a line that says if the report is valid as evidence. Then it has a table with one row for
each check that failed. A report with no failed check has no such table. A failed section has one row:
the table does not repeat its checks. The JSON block at the end of the file holds each check. The
column `Section` holds the check name:

- `suite:<slug>` is the result of a section of the suite: `suite:checkout` (1), `suite:hardware` (2),
  `suite:packs` (3) and `suite:full` (4). `suite:full` is in the table only when section 4 gave no
  result of `certify("full")`.
- `suite:<slug>:<name>` is one check of a section, for example `suite:packs:cuda`.
- Each other row is a check of `certify("full")`, for example `cuda@10de-2484-0:probe`. A name with no
  `:` is the check of one EP on one GPU.

The result of a check is one of these:

| Result | Meaning |
|---|---|
| `pass` | The test passed. |
| `fail` | The test failed, or the section crashed or ran too long. The reason is a fixed code, for example `timed-out`. |
| `not-run` | The test did not run. The reason says why, for example `not-selected`. |
| `record-only` | The check only recorded facts, for example a time. |

`skellytracker/REASON_CODES.md` gives the meaning of each reason code.

A `fail` is useful to the project. Do not run the suite again to get a `pass`. Send the report
as it is.

A report is valid as evidence only when all of these are true:

- It comes from a clean checkout with a known commit.
- The package has a SemVer version.
- All sections ran.
- Section 1 found the Python version and the package versions of `uv.lock`.

A report from a modified clone, from a run with `--only`, from a run that you stopped, or with other
versions says `not valid as evidence` and gives the reasons. The project keeps such a report as a
record only.

If a cleanup step at the end fails, for example the delete of a downloaded file, the report has a
`Cleanup` table with a `fail` row for that step.

Each EP result counts on each GPU, also DirectML on a GPU that is not an AMD GPU.

## What is normal

- On Windows, the line `Init provider bridge failed.` appears on stderr when ONNX Runtime
  loads. It is a known message of the Windows ML build of ONNX Runtime. It is not an error of the
  suite.
- The first run of `trt-rtx` in section 4 builds an engine. It takes longer than the next runs.
  The report records the start time.
- The suite prints progress lines such as `Section 3: EP packs: install and verify ...` and
  `section 4: cuda@10de-2484-0:pipeline-3` to the terminal. Wait for the line `Report written to`.

## Send the report

1. Open the report file. The suite prints its path at the end.
2. Read the whole file. It must hold no personal data (see [Privacy](#privacy)). If it does, remove
   it and tell the project in the notes of the issue.
3. Open a new issue in the repository `skellycertify`
   (https://github.com/domisjustanumber/skellycertify) and choose the form **Certify report**. Fill
   in your OS and GPU model. Attach the report file.

If GitHub does not accept the `.md` file, rename it to `.txt` and attach that file.

## Privacy

The report holds hardware and software facts only: the model names of the CPU and the GPUs, PCI
and USB ids, driver and package versions, the OS label and the results of the tests.

The report never holds a host name, a user name, a path, a serial number, a bus address or a
camera frame. The suite also removes your user name, your home folder, the clone folder and your
host name from each text before it writes the report. An exception: a user name or a host name
that is also a word of a public fact, for example `ubuntu` in `Ubuntu 24.04 LTS` or `home` in
`Windows 11 Home`, stays in the report fields. The report then gives only the number of such
names. The suite always removes these names from your notes line.

You must still read the report before you send it. The suite cannot find every personal detail.
Your notes line is the one place where you write free text.

## Not in this version

- The cameras. The suite does not test a camera.
- No result on an AMD GPU exists yet. The AMD EPs (MIGraphX on Linux, and the AMD EPs of the
  Windows ML catalog on Windows) are tested only with fakes. Your report is the first test.
- Hosts with two GPUs on a laptop are not a tested case.
