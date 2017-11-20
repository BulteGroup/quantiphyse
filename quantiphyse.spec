# -*- mode: python -*-
import sys
import os
import struct
import subprocess
import re
import shutil
import platform

# This is copied from update_version for now until we sort out how to import it...
def get_std_version():
    """ 
    Get standardized version string in form maj.min.patch-release
    """
    v = subprocess.check_output('git describe --dirty', shell=True).strip(" \n")
    p = re.compile("v?(\d+\.\d+\.\d+(-\d+)?).*")
    m = p.match(v)
    if m is not None:
        return  m.group(1)
    else:
        raise RuntimeError("Failed to parse version string %s" % v)

# See if we are 32 bit or 64 bit
bits = struct.calcsize("P") * 8

# Whether to build single-file executable or folder
onefile = False
osx_bundle = False

# Generic configuration
block_cipher = None
bin_files = []
hidden_imports = ['skimage.segmentation', 'sklearn.metrics', 'quantiphyse.analysis.overlay_analysis',
                   'quantiphyse.analysis.feat_pca' ]
added_files = [('quantiphyse/icons', 'icons'), ('quantiphyse/resources', 'resources'), ('src', 'src'),
               ('quantiphyse/packages', 'packages')]
qpdir = os.path.dirname(os.path.abspath(SPEC))
archive_method="zip"

# Update version info from git tags and get standardized version for packages
version_str = get_std_version()

fsldir = os.environ.get("FSLDIR")
sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
hidden_imports.append('fabber')

# Platform-specific configuration
if sys.platform.startswith("win"):
    sysname="win32"
    home_dir = os.environ.get("USERPROFILE", "")
    anaconda_dir='%s/AppData/Local/Continuum/Anaconda2/' % home_dir
    bin_files.append(('%s/Library/bin/mkl_avx2.dll' % anaconda_dir, '.' ))
    #bin_files.append(('%s/Library/bin/mkl_def.dll' % anaconda_dir, '.' ))
    bin_files.append(("%s/bin/fabber*.dll" % fsldir, "fabber/bin"))
    bin_files.append(("%s/bin/fabber.exe" % fsldir, "fabber/bin"))

    if bits == 32:
        # Possible bug in setuptools makes this necessary on 32 bit Anaconda
        hidden_imports += ['appdirs', 'packaging', 'packaging.version',
                           'packaging.specifiers', 'packaging.utils',
                           'packaging.requirements', 'packaging.markers'],
elif sys.platform.startswith("linux"):
    sysname=platform.linux_distribution()[0].split()[0].lower()
    archive_method="gztar"
    hidden_imports.append('FileDialog')
    hidden_imports.append('pywt._extensions._cwt')
    bin_files.append(("%s/lib/libfabber*.so" % fsldir, "fabber/lib"))
    bin_files.append(("%s/bin/fabber" % fsldir, "fabber/bin"))
elif sys.platform.startswith("darwin"):#
    sysname="osx"
    osx_bundle = True
    home_dir = os.environ.get("HOME", "")
    anaconda_dir='%s/anaconda2/' % home_dir
    bin_files.append(('%s/lib/libmkl_mc.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx2.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libpng16.16.dylib' % anaconda_dir, '.' ))
    bin_files.append(("%s/lib/libfabber*.dylib" % fsldir, "fabber/lib"))
    bin_files.append(("%s/bin/fabber" % fsldir, "fabber/bin"))

a = Analysis(['qp.py'],
             pathex=[],
             binaries=bin_files,
             datas=added_files,
             hiddenimports=hidden_imports,
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

if onefile:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name='quantiphyse',
              strip=False,
              debug=False,
              upx=False,
              console=False,
              icon='quantiphyse/icons/main_icon.ico')
else:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='quantiphyse',
              debug=False,
              strip=False,
              upx=False,
              console=False,
              icon='quantiphyse/icons/main_icon.ico')

    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=False,
                   name='quantiphyse')
    if osx_bundle:
        app = BUNDLE(coll,
             name='quantiphyse.app',
             icon='%s/quantiphyse/icons/pk.png' % qpdir,
             bundle_identifier=None)

    # Create versioned packages
    distdir = os.path.join(qpdir, "dist")
    shutil.make_archive("%s/quantiphyse-%s-%s" % (distdir, version_str, sysname), 
                        archive_method, "%s/quantiphyse" % distdir)
