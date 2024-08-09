"use strict";

const fs = require("fs");

const TITLE_PATTERN =
  /^(?<prefix>[^:!(]+)(?<package>\([^)]+\))?(?<breaking>[!])?:.+$/;
const RELEASE_AS_DIRECTIVE = /^\s*Release-As:/im;
const BREAKING_CHANGE_DIRECTIVE = /^\s*BREAKING[ \t]+CHANGE:/im;

const ALLOWED_CONVENTIONAL_COMMIT_PREFIXES = [
  "revert",
  "feat",
  "fix",
  "ci",
  "docs",
  "chore",
  "style",
  "test",
  "refactor",
];

const object = process.argv[2];
const payload = JSON.parse(fs.readFileSync(process.stdin.fd, "utf-8"));

let validate = [];

if (object === "pr") {
  validate.push({
    title: payload.pull_request.title,
    content: payload.pull_request.body,
  });
} else if (object === "push") {
  validate.push(
    ...payload.commits
      .map((commit) => ({
        title: commit.message.split("\n")[0],
        content: commit.message,
      }))
      .filter(({ title }) => !title.startsWith("Merge branch ") && !title.startsWith("Revert ")),
  );
} else {
  console.error(
    `Unknown object for first argument "${object}", use 'pr' or 'push'.`,
  );
  process.exit(0);
}

let failed = false;

validate.forEach((payload) => {
  if (payload.title) {
    const match = payload.title.match(TITLE_PATTERN);
    if (!match) {
      return
    }

    const { groups } = match

    if (groups) {
      if (
        !ALLOWED_CONVENTIONAL_COMMIT_PREFIXES.find(
          (prefix) => prefix === groups.prefix,
        )
      ) {
        console.error(
          `PR (or a commit in it) is using a disallowed conventional commit prefix ("${groups.prefix}"). Only ${ALLOWED_CONVENTIONAL_COMMIT_PREFIXES.join(", ")} are allowed. Make sure the prefix is lowercase!`,
        );
        failed = true;
      }
    } else {
      console.error(
        "PR or commit title must match conventional commit structure.",
      );
      failed = true;
    }
  }

  if (payload.content) {
    if (payload.content.match(RELEASE_AS_DIRECTIVE)) {
      console.error(
        "PR descriptions or commit messages must not contain Release-As conventional commit directives.",
      );
      failed = true;
    }
  }
});

if (failed) {
  process.exit(1);
}

process.exit(0);