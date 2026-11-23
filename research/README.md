# Research notes

This folder holds research notes. A research note records what is known about a subject that the
project examined and did not build, so that a later worker can continue the work.

A research note is not a decision. It changes no rule.

- A measured fact is in a [decision entry](../decisions/README.md). A note cites the entry. It does
  not copy a measured number without the entry ID.
- A note marks each statement as measured by this project, as documented by a vendor with the URL,
  or as a guess.
- A note gives the date of its research. A vendor page can change after that date.
- A note ends with the next step: the measurement to make before a build, and the result that means
  "do not build".
- When the work of a note is built or is refused, write a decision entry. Then change the status
  line of the note to name that entry.

| Note | Subject |
|---|---|
| [gpu-jpeg-decode-intel-qsv.md](gpu-jpeg-decode-intel-qsv.md) | The JPEG decode on an Intel GPU with Quick Sync Video |
| [gpu-jpeg-decode-amd-rocjpeg.md](gpu-jpeg-decode-amd-rocjpeg.md) | The JPEG decode on an AMD GPU with rocJPEG |
