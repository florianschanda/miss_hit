#!/bin/bash

python3 ../miss_hit/goto_ast.py

symtab2gb sanity.json_symtab --out sanity.gb
cbmc sanity.gb --function main --show-goto-functions
