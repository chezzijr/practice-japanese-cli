# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for japanese-cli

This file configures how PyInstaller bundles the Japanese Learning CLI
into a standalone executable for distribution.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from dependencies that might need them
datas = []
datas += collect_data_files('rich')
datas += collect_data_files('typer')
datas += collect_data_files('fsrs')

# Collect hidden imports that PyInstaller might miss
hiddenimports = []
hiddenimports += collect_submodules('rich')
hiddenimports += collect_submodules('typer')
hiddenimports += collect_submodules('fsrs')
hiddenimports += collect_submodules('lxml')
hiddenimports += collect_submodules('pydantic')
hiddenimports += collect_submodules('platformdirs')
hiddenimports += collect_submodules('wanakana')
hiddenimports += collect_submodules('strands_agents')

# Additional hidden imports
hiddenimports += [
    'japanese_cli.main',
    'japanese_cli.cli.import_data',
    'japanese_cli.cli.flashcard',
    'japanese_cli.cli.progress',
    'japanese_cli.cli.grammar',
    'japanese_cli.cli.mcq',
    'japanese_cli.cli.chat_command',
    # Fix for pkg_resources/jaraco issue
    'jaraco.text',
    'jaraco.functools',
    'jaraco.context',
]

a = Analysis(
    ['src/japanese_cli/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest-cov',
        'coverage',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='japanese-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Single file executable
    onefile=True,
)
