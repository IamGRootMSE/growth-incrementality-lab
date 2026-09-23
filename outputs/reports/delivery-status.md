# Delivery status

## Completed locally

- Acquired the official Criteo v2.1 file and verified its published SHA-256 and 13,979,592 rows.
- Ran the full 10% analysis twice with identical core numerical results and validation selection; final sample 1,399,703, final holdout 279,824.
- Ran real-data smoke mode on 55,696 source rows, with separate results and caches.
- Passed 16 automated tests for estimators, leakage controls, pipeline integration, aggregate integrity and internal site links.
- Independently reconciled overall and policy effects through DuckDB against local held-out prediction rows.
- Built the static site and passed browser checks on seven routes at 1440px and 390px, 20 scenario reconciliations, keyboard controls, zero-cost and budget boundaries, invalid-input handling and no JavaScript exceptions.
- Visually reviewed desktop and mobile presentation and the rendered one-page decision memo PDF.
- Included CI and GitHub Pages workflows, setup documentation, data provenance/dictionary, analysis walkthrough, interview guide and three evidence-based resume bullets.

## Branch, commit and publication

**Intended project branch:** `project/growth-incrementality-lab`.

Local `git init -b project/growth-incrementality-lab` succeeded; `.git/HEAD` points to that unborn branch. **No commit exists. No project branch has been pushed. No live deployment is verified.** No force-push was performed, no existing remote content was replaced, and no pull request was created.

The provided repository is `https://github.com/IamGRootMSE/growth-incrementality-lab`. Read-only inspection reported an empty repository with `main` as default branch. The GitHub integration reported repository-level admin/push metadata, but the actual authorized write failed:

```
GitHub API error 403
Resource not accessible by integration
https://docs.github.com/rest/repos/contents#create-or-update-file-contents
```

The failed request attempted to initialize the empty repository with a minimal README so a project branch could be created. It did not succeed. No GitHub write succeeded.

Local Git is also blocked at metadata writes:

```
error: could not lock config file .git/config: Permission denied
fatal: could not set 'remote.origin.url'
fatal: Unable to create '.git/index.lock': Permission denied
```

The Windows sandbox applies explicit deny ACLs to `.git`. A filesystem permission request for this directory returned granted, but subsequent writes still failed, including an actual `git add README.md` attempt. `git rev-parse --verify HEAD` confirms no commit exists. The local Git executable is bundled with Codex, not on this shell's PATH. Its HTTPS helper required `GIT_EXEC_PATH`; its default Windows TLS backend also failed with `SEC_E_NO_CREDENTIALS`. Setting `http.sslBackend=openssl` as a per-command option allowed public `ls-remote`, confirming the empty remote. This fixes public transport, not authorization or local ACLs.

## Exact remaining steps

Use an ordinary authenticated terminal outside the restricted agent sandbox, with Git installed/on PATH. In this project directory, inspect the status first. The raw datasets and secrets are ignored. Then:

```bash
git status
git remote add origin https://github.com/IamGRootMSE/growth-incrementality-lab.git
git add .gitignore LICENSE README.md requirements.txt requirements.lock requirements-browser.txt requirements-pdf.txt pytest.ini lab sql site scripts tests docs outputs/analysis outputs/reports outputs/screenshots outputs/site .github
git commit -m "Build Growth Incrementality and Targeting Lab with empirical Criteo analysis"
git push -u origin project/growth-incrementality-lab
```

If `origin` already exists by then, inspect `git remote -v` rather than replacing it blindly. If `git status` reports ownership mismatch, trust only this specific project path with `git config --global --add safe.directory <absolute-project-path>`. If the local sandbox-created `.git` remains unwritable to your normal account, extract the supplied source ZIP to a fresh directory and use `git init -b project/growth-incrementality-lab` there; do not modify security rules from inside the restricted agent.

Alternatively reconnect the GitHub app with **Contents: read/write** and **Workflows: write** access for this repository, plus any organization approval it requires, then retry remote publication. Repository permission metadata alone did not establish integration permission.

Because the remote was empty, the first pushed branch may become its default. To keep a separate default branch, create `main` from the reviewed project commit after the push, then set it as the repository default. Do not force-update an existing `main` if another person has added work meanwhile.

For Pages, enable **Settings → Pages → Build and deployment → Source: GitHub Actions**. Run the **Deploy GitHub Pages** workflow manually on an allowed branch, or push/merge the reviewed work to `main`. Allow that branch in the `github-pages` environment. Verify a green deployment and the exact reported URL before advertising a live site.

## Checks that could not run

Remote CI, GitHub Pages deployment, live URL verification and committed-tree verification could not run because no remote commit was authorized and local `.git` writes remained blocked. Local tests, numerical validation, browser checks, PDF rendering and full/smoke pipelines did run successfully. This status distinguishes local validation from remote execution.
