#!/bin/bash

for F in *.m; do
    python3 ../../../m_lexer.py ${F} > ${F}.out
done
