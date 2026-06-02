# Contributor Onboarding Notes for supabase-py
 
This document proposes a small set of **repository-specific** contributor onboarding notes for the `supabase-py` codebase. It is written from the perspective of a new contributor navigating the repository for the first time, and intentionally avoids restating general Python knowledge (virtual environments, `async`/`await` syntax, etc.) that contributors are expected to bring with them.
 
The goal is to surface things that are non-obvious *because of how this project is structured*, not because of how the language works.
 
---
 
## Scope
 
This is a documentation-only proposal aimed at reducing repository-specific friction for new contributors. It assumes the reader is already a working Python developer and focuses on what is unique to `supabase-py` — the dual sync/async architecture, the submodule layout, the relationship to sister repositories, and the v3.0 migration context.
 
**Out of scope:**
 
- General Python language concepts
- Virtual environment or `uv` tutorials
- Generic `asyncio` instruction
---
 
## 1. The Dual Sync/Async Client Architecture
 
**Location:** `CONTRIBUTING.md`, new "Repository Architecture" section
 
`supabase-py` ships two parallel client implementations — synchronous and asynchronous — that mirror each other across the codebase. This is the single biggest source of confusion for new contributors, because a change made in one path often needs a corresponding change in the other.
 
### Proposed addition
 
> `supabase-py` maintains two parallel client implementations:
>
> - `Client` / `create_client()` — synchronous
> - `AsyncClient` / `acreate_client()` — asynchronous
>
> Both are first-class and supported. When contributing a bug fix or feature, check whether the change applies to both paths. In most cases it does, and a PR that only updates one side will be asked to update the other before merging.
>
> The two implementations are kept structurally aligned on purpose — this makes the codebase easier to reason about, but it does mean changes are often duplicated by design rather than abstracted away.
 
### Why this helps
 
A new contributor opening their first PR is likely to fix the sync path, miss the async one (or vice versa), and get bounced back during review. Documenting the expectation up front saves both the contributor and the maintainer a review cycle.
 
---
 
## 2. The Submodule Layout and Sister Repositories
 
**Location:** `CONTRIBUTING.md`, "Repository Architecture" section
 
`supabase-py` is not a single monolithic SDK. It is a thin top-level client that composes several smaller, independently maintained sub-libraries:
 
- `postgrest-py` — Postgres / PostgREST query interface
- `gotrue-py` — authentication
- `storage3` — file storage
- `realtime-py` — realtime subscriptions
- `supabase_functions` — edge function invocation
### Proposed addition
 
> Before opening an issue or PR against `supabase-py`, check whether the behavior actually lives in one of the underlying client libraries. For example, a bug in a database query is usually a `postgrest-py` issue; an auth token refresh bug is usually a `gotrue-py` issue. Filing it in the right repository gets it in front of the right maintainers faster.
>
> The top-level `supabase-py` client mostly wires these together — most contributions that change behavior end up in the relevant sub-library rather than here.
 
### Why this helps
 
New contributors routinely file issues in the wrong repository because the top-level package is the only one they know about. A short pointer up front routes work to the right place and reduces triage burden for maintainers.
 
---
 
## 3. v3.0 Migration Context
 
**Location:** `CONTRIBUTING.md`, "Before You Contribute" section, or as a short callout in `README.md`
 
There is an active v3.0 tracking discussion that affects what's worth contributing to right now. New contributors who don't know about it can spend time on areas that are already slated for refactor.
 
### Proposed addition
 
> `supabase-py` has an active v3.0 tracking discussion outlining planned architectural changes. Before starting a substantial contribution, it's worth reviewing the tracking issue to check whether the area you're touching is stable, mid-refactor, or already planned for removal.
>
> For first-time contributors, the safest starting points are typically:
>
> - Bug fixes against currently stable code paths
> - Documentation improvements
> - Test coverage additions
>
> Larger feature work is best discussed in an issue or in the v3.0 tracking thread first.
 
### Why this helps
 
This protects both sides: the contributor doesn't sink hours into work that will be discarded, and the maintainer doesn't have to redirect them mid-review.
 
---
 
## 4. Where Questions Actually Get Answered
 
**Location:** `CONTRIBUTING.md`, "Getting Help" subsection
 
Different parts of the Supabase community use different channels. Knowing which one to use saves time for both the contributor and the maintainers.
 
### Proposed addition
 
> - **Bug reports and feature proposals:** open an issue on the relevant repository
> - **Open-ended technical questions:** GitHub Discussions on the main `supabase` repository
> - **Real-time community questions:** the official Supabase Discord, in the language-specific Python channel
> - **Security issues:** follow the security policy linked in the repository — do not open a public issue
>
> Maintainers generally watch issues and PRs more closely than Discord, so anything that needs to be tracked or referenced later should live on GitHub.
 
### Why this helps
 
A first-time contributor often defaults to opening an issue for anything that isn't a confirmed bug, which clutters the issue tracker. Pointing toward Discussions and Discord for open-ended questions keeps the issue queue focused on actionable work.
 
---
 
## 5. Running Tests Against a Real Supabase Instance
 
**Location:** `CONTRIBUTING.md`, "Testing" section
 
Some of the test suite hits a live Supabase instance, which is a friction point new contributors don't expect when they first run `pytest` and see unexpected failures.
 
### Proposed addition
 
> Some tests in this repository require a running Supabase instance to execute fully. Tests that hit live endpoints will fail or be skipped when no instance is configured locally.
>
> If you are submitting a bug fix or a small feature, it is generally enough to:
>
> - Run the test suite locally and confirm no *new* failures are introduced
> - Note in your PR description if any failures appear to be pre-existing or environment-related
>
> Setting up a local Supabase instance (via the Supabase CLI or Docker) is only necessary if your change directly affects the code paths covered by the live tests.
 
### Why this helps
 
New contributors often interpret pre-existing test failures as something they broke, panic, and either over-investigate or abandon the PR. A short note about which failures matter saves them that loop.
 
---
 
## Suggested Placement Summary
 
| Section | File | Placement |
| --- | --- | --- |
| Dual sync/async architecture | `CONTRIBUTING.md` | New "Repository Architecture" section near the top |
| Submodule layout and sister repos | `CONTRIBUTING.md` | Same "Repository Architecture" section |
| v3.0 migration context | `CONTRIBUTING.md` | New "Before You Contribute" callout |
| Where to ask questions | `CONTRIBUTING.md` | "Getting Help" subsection |
| Test suite expectations | `CONTRIBUTING.md` | Existing testing section, as a short note |
 
---
 
## Next Steps
 
If this revised scope is well-received, follow-up iterations could add:
 
- A short visual map of the sub-library relationships
- A "first issues to look at" pointer in `CONTRIBUTING.md`
- A glossary of project-specific terms used in issues and PR reviews
---
 
## A Note on the Previous Revision
 
An earlier version of this proposal included general Python onboarding material (virtual environments, sync vs async basics, common Python errors). That content has been removed in response to maintainer feedback that such guidance falls outside the scope of this repository and would create ongoing maintenance burden without commensurate gain. The revised proposal focuses exclusively on `supabase-py`-specific concerns that a working Python developer would still need to learn when entering this codebase for the first time.
 
