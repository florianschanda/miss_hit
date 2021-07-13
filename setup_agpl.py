#!/usr/bin/env python3

import sys
import setuptools

import miss_hit_core.version

with open("README.md", "r") as fd:
    long_description = fd.read()

setuptools.setup(
    name="miss_hit",
    version=miss_hit_core.version.VERSION,
    author="Florian Schanda",
    author_email="florian@schanda.org.uk",
    description="Static analysis and other utilities for programs written in the MATLAB/Simulink and Octave languages.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://misshit.org",
    project_urls={
        "Bug Tracker"   : "https://github.com/florianschanda/miss_hit/issues",
        "Documentation" : "https://florianschanda.github.io/miss_hit/",
        "Source Code"   : "https://github.com/florianschanda/miss_hit",
    },
    license="GNU Affero General Public License v3",
    packages=["miss_hit"],
    install_requires=["miss_hit_core==%s" % miss_hit_core.version.VERSION],
    python_requires=">=3.6, <4",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities"
    ],
    entry_points={
        "console_scripts": [
            "mh_lint = miss_hit.mh_lint:main",
            "mh_diff = miss_hit.mh_diff:main",
            "mh_copyright = miss_hit.mh_copyright:main",
        ],
    },
)
