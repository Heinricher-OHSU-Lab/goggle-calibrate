# PsychoPy Installation Notes

## Version and Compatibility

This project uses **PsychoPy 2023.2.3** for the following reasons:

- **macOS Monterey Compatibility**: This is the last version that uses PyQt5. PsychoPy 2024.1.0+ requires PyQt6, which only works on macOS 13 (Ventura) or later.
- **Python 3.10 Support**: Version 2023.2.3 fully supports Python 3.10.
- **NumPy 1.x Compatibility**: Must use NumPy <2.0 as PsychoPy 2023.2.3 uses deprecated NumPy APIs removed in 2.0.

## Installation Issue: pypi-search Dependency

PsychoPy 2023.2.3 has a dependency on `pypi-search>=1.2.1`, which has been **removed from PyPI** because PyPI discontinued their search API. This causes normal pip installation to fail with:

```
ERROR: Could not find a version that satisfies the requirement pypi-search>=1.2.1 (from psychopy)
ERROR: No matching distribution found for pypi-search>=1.2.1
```

## Workaround

To work around this issue, we install PsychoPy **without dependencies** first, then manually install all required dependencies:

### Manual Installation Steps

```bash
# 1. Install PsychoPy without dependencies
pip install --no-deps psychopy==2023.2.3

# 2. Install core dependencies
pip install -r requirements-deps.txt

# 3. Install additional PsychoPy dependencies
pip install astunparse cryptography esprima ffpyplayer gitpython \
    'jedi>=0.16' opencv-python pyobjc-core \
    'pyobjc-framework-Quartz<8.0' python-gitlab \
    'python-vlc>=3.0.12118' tables
```

### Using the Install Script

A helper script is provided for convenience:

```bash
./scripts/install_psychopy.sh
```

## Verification

After installation, verify PsychoPy works correctly:

```bash
python -c "import psychopy; from psychopy import visual; import numpy as np; \
    print(f'PsychoPy {psychopy.__version__}'); \
    print(f'NumPy {np.__version__}')"
```

Expected output:
```
PsychoPy 2023.2.3
NumPy 1.26.4
```

## Version Constraints

The following version constraints are critical:

- `psychopy==2023.2.3` - Last PyQt5 version
- `numpy<2.0` - PsychoPy 2023.2.3 incompatible with NumPy 2.x
- `pyqt5` (not `pyqt6`) - Required for macOS Monterey

## Future Considerations

When upgrading to macOS Ventura (13) or later, you can upgrade to:
- PsychoPy 2024.2.5 or later (with PyQt6)
- NumPy 2.x
- No installation workaround needed

However, the current setup is stable and works reliably for research use.

## Troubleshooting

### Error: `np.alltrue` was removed

This indicates NumPy 2.x is installed. Downgrade:
```bash
pip install 'numpy<2.0'
```

### Error: Qt platform plugin not found

This usually means PyQt6 was installed instead of PyQt5:
```bash
pip uninstall pyqt6 PyQt6-Qt6 PyQt6-sip
pip install pyqt5
```

### General Installation Issues

If you encounter other issues, try recreating the virtual environment:
```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
./scripts/install_psychopy.sh
```