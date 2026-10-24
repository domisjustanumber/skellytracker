# 0030 — No private data in tracked files, commits or PR text

**Status:** accepted, 2026-10-24 (user).

## Decision

1. **The rule.** Do not write these in a tracked file, a commit message or a PR body:
   - a credential, a token, a password or a private key;
   - an absolute path in a user folder, for example `C:\Users\<name>\...` or `/home/<name>/...`;
   - a hostname or a user name in prose;
   - an email address, except an address on the allowlist of `tools/check_private_data.py`;
   - a private URL or a private IP address;
   - a raw dump of `env`, `pip list`, `nvidia-smi` or `docker inspect`.

   Use paths relative to the repo, for example `../OpenMMLab-Exporter/notes/`. Give a measurement
   as a summary with its tool and its version. Report fields and test fakes can contain a hostname:
   the user accepted the hostname in the OpenMMLab-Exporter run IDs on 2026-10-24.
2. **`plans/`.** Text that comes from `plans/` into a tracked file must obey the rule. Git ignores
   `plans/`, but a plan can still be committed by mistake, and its text can be copied.
3. **A found leak.** Remove the data from the current file with the redaction edit of
   [0028](0028-entry-edits-and-citations.md). Then tell the user, because git history keeps the
   data. A credential must also be revoked.
4. **Tools.**
   - [`tools/check_private_data.py`](../../tools/check_private_data.py) checks each tracked or new
     text file for user paths, email addresses, private IP addresses, tokens and the terms of the
     untracked file `.private-terms`. The doc tests run it.
   - `gitleaks` scans for secrets. The pre-commit hook scans the staged changes. The workflow
     [`secrets.yml`](../../.github/workflows/secrets.yml) scans the history on each push and PR.
     [`.gitleaks.toml`](../../.gitleaks.toml) holds the reviewed false positives.
   - Run `uv run pre-commit install` once in each clone. The hook runs `gitleaks` and the private-data
     check before each commit.
5. **GitHub.** Secret scanning and push protection are on for the fork. Turn them on for a private
   repo on the day it becomes public.

Mirror: OpenMMLab-Exporter 0041 (planned).

## Reason

- The repos are public, and git history is permanent. A force-push does not remove a commit from
  forks, clones or caches.
- On 2026-10-24, `plans/` files are in the history of both repos: in skellytracker on a pushed
  branch, and in OpenMMLab-Exporter on `main` before it stopped tracking `plans/`. They hold
  absolute paths in a user folder. The rule that git ignores `plans/` came later.
- Agents copy evidence into entries. A pasted command output can hold paths, user names and
  environment values.
- The tools find a leak before the push. A written rule alone does not stop a paste.

## Consequences

- The first `pre-commit` run on a new clone downloads Go to build `gitleaks`.
- A new public email address in a tracked file needs an allowlist change in the tool.
- `.private-terms` is local. Each clone has its own list, or none.

## Evidence

- `gitleaks` 8.30.1 on all refs, 2026-10-24: OpenMMLab-Exporter 150 commits, no findings.
  skellytracker 733 commits, 2 findings. Both are `generic-api-key` false positives: model registry
  keys (`pose_key: "rtmw-..."`) in the Rust port on `upstream/development-rust`.
- The `plans/` blobs of both histories (50 and 28 versions) hold absolute paths in a user folder.
  They hold no tokens, email addresses, private IP addresses or hostnames.
- The published OpenMMLab-Exporter Docker image: its own layers have `ENV TZ=UTC`, pinned `pip`
  installs, the manifest weights and hash labels. They have no credentials.

## Alternatives rejected

- **`gitleaks-action` in CI.** It needs a license key for an organization repo such as
  `freemocap/skellytracker`. The workflow runs the pinned binary and checks its SHA-256.
- **A tracked list of private terms.** The list would publish the terms.
- **Rewrite the history to remove the `plans/` paths.** The paths hold only a user name that the
  commit metadata already shows. A rewrite changes the cited SHAs of the PR stack.
