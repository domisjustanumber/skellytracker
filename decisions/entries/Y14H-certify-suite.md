# Y14H — The certify suite: one command, seven sections, one report

**Status:** accepted, 2026-11-18 (user).

## Decision

1. **Command.** A volunteer clones this repository at a certification tag and runs one tool:
   `tools/certify_platform.py`.
2. **Sections.** (1) Checkout and versions. (2) Hardware probe. (3) EPs: install, verify and certify
   each EP that the platform can use. (4) The real pipeline on each EP against the CPU EP, with
   timings and peak VRAM for 1, 3 and 6 cameras. (5) JPEG decode and preprocess. (6) Cameras: a quick
   pass early and the long pass last. (7) JPEG encode and decode speed and Quick Sync, on synthetic
   images. Not in this version: hosts with two GPUs, Smart App Control, the frozen application and
   the skellycam ring buffer.
3. **Report.** One Markdown file: a summary table (section, result, one-line reason), the details of
   each section, and last the same data as one fenced JSON block. It holds a schema id and the suite
   version. The suite writes no second file and no image.
4. **Results.** Each section and each check has `pass`, `fail`, `not-run` or `record-only`, a fixed
   reason code and numbers. A report holds no error text and no traceback. Certification is per
   section. The platform gets no single verdict.
5. **Child processes.** Each section runs in its own child process with a time limit. A crash, a
   non-zero exit, an output that is not one JSON object and a timeout are findings with the exit code
   and the seconds. On a timeout the suite kills the whole process tree. The suite then continues and
   writes the report.
6. **Consent.** Before a run, the suite shows the time of each section, the total and each download
   with its size. It asks one time. `--yes` skips the question. With no terminal and no `--yes`, it
   stops. At the end, only at a terminal, it asks the yes/no questions of the sections and one
   optional note. The note prompt tells the user not to write personal details. The report has no
   name or contact field.
7. **Work folder.** The suite keeps each download and its own EP store in `.certify-work/` of the
   clone. It deletes that folder at the end, also after a failure or Ctrl+C. It keeps the report. It
   installs or changes no system software and needs no administrator rights. Items 11 and 12 are
   the exceptions.
8. **Privacy.** The report holds no hostname, no user name, no absolute path, no serial number, no bus
   address and no camera frame. It holds hardware and software facts only: model names, PCI and USB
   ids, driver and package versions and the OS label. Text from an OS tool goes through an allowlist
   of fields. A scrub also removes the user name, the home folder and the hostname from each string.
9. **Section 2.** It records the values of skellytracker and of each OS tool side by side and flags
   each difference. A difference does not fail it: the result is `record-only`. It fails only when
   `probe_host()` raises.
10. **skellycam.** skellycam stays out of the normal install. The suite fetches it at a pinned public
    commit and runs the skellycam runner.
11. **AMD EPs.** Section 3 includes the AMD EPs: the suite is the test that certifies them. On
    Windows it tests DirectML and each AMD GPU EP that the Windows ML catalog offers for the GPU. On
    Linux it uses the `onnxruntime-ep-migraphx` build for the installed ROCm version (10.0, 10.1 or
    10.2). If that EP does not load on ONNX Runtime 1.30.0, the suite records the failure and runs
    the MIGraphX parts in a second environment on ONNX Runtime 1.29. The report gives the ORT version
    of each result. An AMD EP is in a field-test state until one reviewed report for the OS passes
    sections 3 and 4. Until then, only the suite or an explicit install option installs it, and the
    app never offers it. The app offers DirectML for AMD GPUs only. The suite records the DirectML
    result on each GPU. The Windows AMD EP package is the one system change of the suite. The consent
    text names it. The suite removes it at the end if the suite installed it.
12. **Model files.** The suite downloads them into the git-ignored model folder from a list (file, URL,
    sha256) in the `certification` block of the EP catalog. It deletes its downloads at the end. The
    sidecars do not change. The files go in a public Hugging Face repository of freemocap.
13. **Evidence.** A report is evidence only from a clean checkout of a certification tag with all
    sections run. Else the report has a top-level field and a line that say so. The suite is complete
    before its first tag: no tag before each section exists.
14. **Hand-in.** The volunteer attaches the report to a GitHub issue of this repository (issue
    template) or sends it by email. An accepted report is committed whole in a folder of this
    repository. It is the evidence for the sections that are not EPs. A person still writes the EP
    rows of `ep_evidence.yaml`.
15. **New run.** A platform needs a new run when the version set or the tests of a section change, not
    for each tag. A full run takes about 30 to 40 minutes.
16. **Linux gate.** The suite run on Linux replaces `decisions/scripts/n6e8_ort_1_30/linux_ep_gate.sh`
    as the gate of [ADR-N6E8](N6E8-onnxruntime-1-30-on-each-os.md) item 9. The host rules of that
    item stay.

## Reason

- The maintainer has one Windows host with one NVIDIA GPU. Volunteers give the evidence for other
  hardware ([ADR-MF2R](MF2R-ep-store-install-and-certification.md)).
- A child process for each section keeps the report when an EP ends a process.

## Evidence

Code facts: `tools/certify_platform.py` and `tools/certify_hardware.py`. `.gitignore` ignores
`.certify-work/` and `/certify-report-*.md`. One run on Windows 11, 2026-11-18: section 2 flagged
the VRAM of an Intel UHD Graphics 770: 128 MiB in `probe_host()`, 2047 MiB in `AdapterRAM`.

## Alternatives rejected

- **One process for all sections.** A crash loses the report.

## Open work

See [open-work.md](../open-work.md).
