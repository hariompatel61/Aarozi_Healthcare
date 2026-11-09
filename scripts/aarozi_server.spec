# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

repo_root = Path(os.path.abspath('.')).resolve()
api_dir = repo_root / 'apps' / 'api'
web_output = repo_root / 'apps' / 'web' / '.output' / 'public'

datas = [
    (str(api_dir / 'dev_aarozi.db'), '.') if (api_dir / 'dev_aarozi.db').exists() else (str(api_dir / 'app'), 'app'),
]

if web_output.exists():
    datas.append((str(web_output), 'apps/web/.output/public'))

hidden_imports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.on',
    'fastapi',
    'fastapi.staticfiles',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.asyncio',
    'cryptography',
    'cryptography.hazmat.primitives.asymmetric.ed25519',
    'passlib',
    'passlib.handlers.pbkdf2',
    'pydantic',
    'pydantic_settings',
    'app',
    'app.main',
    'app.db',
    'app.settings',
    'app.licensing',
    'app.licensing.signing',
    'app.licensing.service',
    'app.routers.auth',
    'app.routers.backup',
    'app.routers.billing',
    'app.routers.blood_bank',
    'app.routers.health',
    'app.routers.integrations',
    'app.routers.licensing',
    'app.routers.meta',
    'app.routers.pathology',
    'app.routers.patients',
    'app.routers.reports',
    'app.routers.sync',
    'app.routers.commercial',
    'app.routers.customer_portal',
    'app.routers.google_drive',
    'app.routers.migration',
    'app.services.google_drive_service',
    'app.services.migration_service',
]

a = Analysis(
    ['apps/api/run_server.py'],
    pathex=[str(repo_root), str(api_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AaroziHealthcareServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AaroziHealthcare',
)

