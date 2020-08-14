#!/usr/bin/env python3

# This helper script tags a release using the GitHub API.
#
# https://docs.github.com/en/rest/reference/repos#create-a-release

import os
import sys
import json

import requests

from miss_hit_core.version import VERSION
import util.changelog

def main():
    username = os.environ.get("GITHUB_USERNAME", None)
    if username is None:
        print("Please set the GITHUB_USERNAME environment variable")

    token = os.environ.get("GITHUB_MISS_HIT_TOKEN", None)
    if token is None:
        print("Please set the GITHUB_MITT_HIT_TOKEN environment variable")

    if username is None or token is None:
        sys.exit(1)

    auth = requests.auth.HTTPBasicAuth(username, token)

    api_endpoint = "https://api.github.com/repos/%s/%s/releases" % \
        ("florianschanda", "miss_hit")

    tag_name = "release-%s" % VERSION
    rel_name = "Release %s" % VERSION
    rel_body = "### %s\n\n%s" % (VERSION, util.changelog.current_section())

    data = {"tag_name" : tag_name,
            "name"     : rel_name,
            "body"     : rel_body}

    r = requests.post(API_ENDPOINT, auth=auth, data=json.dumps(data))
    print(r)

if __name__ == "__main__":
    main()
