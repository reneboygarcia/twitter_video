---
title: Security and Dependency Auditing best practices
date: 2026-06-06
category: docs/solutions/best-practices/
module: Security & Dependency Auditing
problem_type: best_practice
component: development_workflow
severity: low
applies_when:
  - Performing repository security scans
  - Verifying virtual environment dependencies for bad actors
  - Reviewing transient dependencies from developer tooling
tags:
  - security
  - dependency-auditing
  - safety-scan
  - bad-actor-scan
---

# Security and Dependency Auditing best practices

## Context
During a repository safety scan and bad actor review, three undocumented packages (`ast_serialize`, `librt`, `pytokens`) were discovered installed in the local virtual environment (`venv`). To ensure that no malicious supply-chain injection or bad actor compromise had occurred, a thorough security audit of the repository, workflows, and venv packages was performed.

## Guidance
1. **Differentiate Transient Dependencies**: Before assuming an undocumented package in `pip list` is a malicious dependency, inspect its details using `pip show <package_name>` to trace its requirements and origin.
   - `ast_serialize` and `librt` are legitimate runtime/AST bindings used by `mypy`.
   - `pytokens` is a fast Python tokenizer used by `black`.
2. **Utilize GitHub Actions Security Triggers**: Enable and maintain CodeQL static analysis and container/filesystem dependency scanning (such as Trivy or pip-audit) with least-privilege token permissions (`contents: read`).
3. **Avoid Shell-Based Execution for Downloader API**: Ensure external downloaders or CLI integrations (such as `yt-dlp` or `ffmpeg`) are invoked through their native Python API rather than shell string construction (e.g. `subprocess.Popen` with `shell=True`) to prevent argument/command injection.

## Why This Matters
Supply chain attacks often involve typosquatting or shadow dependencies. Performing regular audits and documenting the rationale for transient packages prevents unnecessary concern, maintains development velocity, and guarantees that security issues are identified proactively before code is merged.

## When to Apply
- When running local security audits.
- When new undocumented packages are found in local virtual environments.
- When configuring or upgrading CLI-based download libraries like `yt-dlp`.

## Examples

### Checking Undocumented Packages
Use pip show to inspect package metadata and trace its requirements:
```bash
venv/bin/pip show ast_serialize librt pytokens
```
Output shows the `Required-by:` field:
```
Name: ast_serialize
Required-by: mypy
---
Name: pytokens
Required-by: black
```

### Safe API Integration (No Shell Injection)
Avoid:
```python
# Unsafe shell command execution
subprocess.run(f"yt-dlp {url} -o {output_path}", shell=True)
```

Prefer:
```python
# Safe Python API invocation
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([url])
```

## Related
- [SECURITY.md](file:///Users/reneboygarcia/Documents/Github%20Projects/Twitter%20Video%20Downloader/SECURITY.md)
- [security_audit_report.md](file:///Users/reneboygarcia/.gemini/antigravity-ide/brain/4e17056d-9318-4bed-bb77-32d936214dad/security_audit_report.md)
