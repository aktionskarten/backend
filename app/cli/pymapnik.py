import click
import sys

from distutils.core import run_setup
from os import environ, getcwd
from os.path import isdir
from path import Path
from platform import release as os_release
from urllib.request import urlretrieve
from shutil import unpack_archive
from sh import patch

@click.group(help="mapnik related commands")
def pymapnik():
    pass


def _mapnik_is_installed():
    try:
        import mapnik
        return mapnik.mapnik_version() > 0
    except ImportError:
        return False


@pymapnik.command()
def is_installed():
    if _mapnik_is_installed():
        click.secho("Mapnik is installed and works!", fg='green')
    else:
        click.secho("Mapnik is missing!", fg='red')
        click.echo("Run 'mapnik install' do fix this")


@pymapnik.command()
def install():
    if _mapnik_is_installed():
        click.secho("Mapnik already installed!", fg='green')
        return

    environ['PYCAIRO'] = "true"

    # Mapnik v3.0.x only works with boost 1.69. ArchLinux uses boost >1.6
    # as system default. As a workaround the mapnik package maintainer provides
    # a boost1.69-libs (without source). For compiling python-mapnik we need
    # the 1.69 header files. Hence, download them manually and hardcode
    # 1.69 lib versions for linking
    if 'arch' in os_release():
        print('ArchLinux detected.')
        boost_dir = 'libs/boost_1_69_0'
        if not isdir(boost_dir):
            print('Downloading boost v1.69...')
            file_name = 'boost_1_69_0.tar.bz2'
            url = 'https://dl.bintray.com/boostorg/release/1.69.0/source/'+file_name
            def progress(chunk_number, maximum_size_chunk, total_size):
                if  chunk_number%round(maximum_size_chunk/10.) == 0:
                    print('*', end='', flush=True)
            archive_name, _ = urlretrieve(url, file_name, progress)
            print('\nDownloaded. Unpacking..')
            unpack_archive(archive_name, 'libs/')

        environ['CFLAGS'] = '-I{}/{}'.format(getcwd(), boost_dir)

        environ['BOOST_PYTHON_LIB'] = ':libboost_python38.so.1.69.0'
        environ['BOOST_THREAD_LIB'] = ':libboost_thread.so.1.69.0'
        environ['BOOST_SYSTEM_LIB'] = ':libboost_system.so.1.69.0'
        environ['BOOST_FILESYSTEM_LIB'] = ':libboost_filesystem.so.1.69.0'
        environ['BOOST_REGEX_LIB'] = ':libboost_regex.so.1.69.0'

        patch_data = """
diff --git a/setup.py b/setup.py
index a19fbb36e..02062312f 100755
--- a/setup.py
+++ b/setup.py
@@ -114,7 +114,18 @@ linkflags = []
 lib_path = os.path.join(check_output([mapnik_config, '--prefix']),'lib')
 linkflags.extend(check_output([mapnik_config, '--libs']).split(' '))
 linkflags.extend(check_output([mapnik_config, '--ldflags']).split(' '))
-linkflags.extend(check_output([mapnik_config, '--dep-libs']).split(' '))
+
+# we want to be able to use certain version of boost dependencies
+# through BOOST_%s_LIB environment variables
+deps = check_output([mapnik_config, '--dep-libs']).split(' ')
+deps_boost = [lib for lib in deps if lib.startswith('-lboost')]
+linkflags.extend([lib for lib in deps if lib not in deps_boost])
+def _adjust_boost_lib(lib):
+    _id = lib[2:]
+    name = os.environ.get("%s_LIB" % _id.upper(), find_boost_library(_id))
+    return '-l{}'.format(name)
+linkflags.extend([_adjust_boost_lib(lib) for lib in deps_boost])
+
 linkflags.extend([
 '-lmapnik-wkt',
"""
    try:
        print("Trying to patch setup.py")
        patch('-dlibs/python-mapnik', '--forward', _in = patch_data)
    except:
        print("Already patched")

    with Path("libs/python-mapnik"):
        import subprocess
        #child = subprocess.call(['python', 'setup.py', 'clean'])
        #if child != 0:
        #    sys.exit(-1)

        import cairo
        include_path = '--include-dirs=' + cairo.get_include()
        child = subprocess.call([sys.executable, 'setup.py', 'build_ext', include_path])
        if child != 0:
            sys.exit(-1)

        child = subprocess.call(['python', 'setup.py', 'install'])
        if child != 0:
            sys.exit(-1)

        # following seems not to work in debian 9
        #dist = run_setup('setup.py')
        #dist.run_command('clean')
        #dist.run_command('install')

    click.secho("Mapnik installed successfully!", fg='green')


if __name__ == '__main__':
    pymapnik()
