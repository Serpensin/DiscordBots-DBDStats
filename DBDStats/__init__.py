import os
import glob



# Import all modules in the CustomModules folder
modules = glob.glob(os.path.join(os.path.dirname(__file__), "CustomModules", "*.py"))
__all__ = [os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

for module in __all__:
    exec(f"from .CustomModules import {module}")
