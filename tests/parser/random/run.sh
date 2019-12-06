#!/bin/bash

for F in *.m; do
    python3 ../../../m_parser.py ${F} > ${F}.out
done
