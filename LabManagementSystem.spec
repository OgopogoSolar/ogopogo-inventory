# LabManagementSystem.spec

# -- imports omitted --

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('modules/ui/*.ui', 'modules/ui'),     # your .ui files
        ('modules/**/templates/*.xml', './'),   # any license/email templates
    ],
    hiddenimports=['wmi'],  # if PyInstaller misses WMI
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LabManagementSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LabManagementSystem'
)
