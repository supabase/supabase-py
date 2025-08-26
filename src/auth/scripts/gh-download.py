# /// script
# dependencies = [
#   "pygithub >=1.57,<3.0",
# ]
# ///

# This code was copied from
# https://gist.github.com/pdashford/2e4bcd4fc2343e2fd03efe4da17f577d
# and modified to work with Python 3, type hints, correct format and
# simplified the code to our needs.

"""
Downloads folders from github repo
Requires PyGithub
pip install PyGithub
"""

import base64
import getopt
import os
import shutil
import sys
from typing import Optional

from github import Github, GithubException
from github.ContentFile import ContentFile
from github.Repository import Repository


def get_sha_for_tag(repository: Repository, tag: str) -> str:
    """
    Returns a commit PyGithub object for the specified repository and tag.
    """
    branches = repository.get_branches()
    matched_branches = [match for match in branches if match.name == tag]
    if matched_branches:
        return matched_branches[0].commit.sha

    tags = repository.get_tags()
    matched_tags = [match for match in tags if match.name == tag]
    if not matched_tags:
        raise ValueError("No Tag or Branch exists with that name")
    return matched_tags[0].commit.sha


def download_directory(repository: Repository, sha: str, server_path: str) -> None:
    """
    Download all contents at server_path with commit tag sha in
    the repository.
    """
    if os.path.exists(server_path):
        shutil.rmtree(server_path)

    os.makedirs(server_path)
    contents = repository.get_dir_contents(server_path, ref=sha)

    for content in contents:
        print(f"Processing {content.path}")
        if content.type == "dir":
            os.makedirs(content.path)
            download_directory(repository, sha, content.path)
        else:
            try:
                path = content.path
                file_content = repository.get_contents(path, ref=sha)
                if not isinstance(file_content, ContentFile):
                    raise ValueError("Expected ContentFile")
                with open(content.path, "w+") as file_out:
                    if file_content.content:
                        file_data = base64.b64decode(file_content.content)
                        file_out.write(file_data.decode("utf-8"))
            except (GithubException, OSError, ValueError) as exc:
                print("Error processing %s: %s", content.path, exc)


def usage():
    """
    Prints the usage command lines
    """
    print("usage: gh-download --repo=repo --branch=branch --folder=folder")


def main(argv):
    """
    Main function block
    """
    try:
        opts, _ = getopt.getopt(argv, "r:b:f:", ["repo=", "branch=", "folder="])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    repo: Optional[str] = None
    branch: Optional[str] = None
    folder: Optional[str] = None
    for opt, arg in opts:
        if opt in ("-r", "--repo"):
            repo = arg
        elif opt in ("-b", "--branch"):
            branch = arg
        elif opt in ("-f", "--folder"):
            folder = arg

    if not repo:
        print("Repo is required")
        usage()
        sys.exit(2)
    if not branch:
        print("Branch is required")
        usage()
        sys.exit(2)
    if not folder:
        print("Folder is required")
        usage()
        sys.exit(2)

    github = Github(None)
    repository = github.get_repo(repo)
    sha = get_sha_for_tag(repository, branch)
    download_directory(repository, sha, folder)


if __name__ == "__main__":
    """
    Entry point
    """
    main(sys.argv[1:])
