#!/usr/bin/env python3
"""
Test dataset registration
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

print("Testing dataset registration...")

# Import DaSSL registry
from dassl.data.datasets import DATASET_REGISTRY

# Import our datasets - this should register them
import datasets.ni_flags
import datasets.ni_flags_v2

# Check what's registered
print("\n📋 Registered datasets:")
registered = DATASET_REGISTRY.registered_names()
print(f"Total: {len(registered)} datasets")

# Check for our datasets
if 'NIFlags' in registered:
    print("✅ NIFlags is registered")
else:
    print("❌ NIFlags NOT registered")

if 'NIFlagsV2' in registered:
    print("✅ NIFlagsV2 is registered")
else:
    print("❌ NIFlagsV2 NOT registered")

# Show all custom datasets
print("\n📊 Custom datasets available:")
for name in registered:
    if 'NI' in name or 'ni' in name:
        print(f"   - {name}")

print("\n✅ Test complete!")
print("\nTo use NIFlagsV2, run:")
print("python train_minimal_mps.py ... DATASET.NAME NIFlagsV2")
