# Contributing

We highly appreciate feedback and contributions from the community! If you'd like to contribute to this project, please make sure to review and follow the guidelines below.

## What we accept right now

| Branch | Version | Issues                                 | Pull requests                              |
| ------ | ------- | -------------------------------------- | ------------------------------------------ |
| `main` | v3      | Not accepted                           | Not accepted                               |
| `v2`   | v2      | Critical bugs and security issues only | Critical bug fixes and security fixes only |

### v3 (`main`)

v3 is in early development and its APIs are still changing. We are not accepting external contributions or issues for v3 at this point. Issues and pull requests that target `main` from outside the maintainer team will be closed.

### v2 (`v2`)

v2 is the current stable release. We accept critical bug fixes and security fixes for it. Open these pull requests against the [`v2`](https://github.com/supabase/supabase-py/tree/v2) branch. New features and non-critical changes for v2 will not be merged.

Do not report security vulnerabilities in public issues. Follow the [Supabase security policy](https://supabase.com/.well-known/security.txt) instead.

## Code of conduct

In the interest of fostering an open and welcoming environment, please review and follow our [code of conduct](https://github.com/supabase/.github/blob/main/CODE_OF_CONDUCT.md).

## Code and copy reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. GitHub requests review from the [code owners](./.github/CODEOWNERS) automatically when you open a pull request. You do not need to request a review yourself.

## Report an issue/File a feature request

Before opening a new issue or request, please take a moment to check the existing issues and discussions to see if your topic has already been addressed. This helps us avoid duplicate issues and keeps the conversation focused.

Report critical v2 bugs through [GitHub Issues](https://github.com/supabase/supabase-py/issues) and state that the issue is about v2. Feature requests are not accepted at this point.

## Create a pull request

When making pull requests against the `v2` branch, make sure to follow these guidelines:

- Before creating a pull request, file a GitHub Issue so that maintainers and the community can discuss the problem and potential solutions before you spend time on an implementation.
- In your PR's description, link to any related issues or pull requests to give reviewers the full context of your change. To link to an existing issue or pull request in your PR, use the # symbol followed by the issue or PR number. For example, to link to issue number 123, you would write #123 in your PR's description. GitHub will automatically create a link to the issue.
- For commit messages, follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format.
  - For example, if you update documentation for a specific extension, your commit message might be: `docs(extension-name) updated installation documentation`.
