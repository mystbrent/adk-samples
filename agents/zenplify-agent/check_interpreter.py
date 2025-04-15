import sys
import os
import site

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Path: {sys.path}")
print(f"Site packages: {site.getsitepackages()}") 