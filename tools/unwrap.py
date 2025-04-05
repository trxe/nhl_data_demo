from pathlib import Path
import json

filename = input("filename: ")
outfile = input("outfile: ") or filename
key = input("_key: ")
output = []
with open(filename, 'r') as file:
    data = json.load(file)
    output.extend(data.get(key))
with open(outfile, '+w') as file:
    json.dumps(output)