from setuptools import setup, find_namespace_packages
from setuptools.command.install import install
from setuptools.command.develop import develop

import subprocess
import sys
import pathlib
import shutil
###from pytom import __version__

def find_executables():
    bin_folder = pathlib.Path('pytom/bin')
    # exclude entry points as well
    executables = [str(path) for path in bin_folder.iterdir() if path.is_file() and '__' not in path.name and path.name != "coords2PL.py"]
    return executables + [str(bin_folder.joinpath(f)) for f in ['pytom', 'ipytom', 'pytomGUI']]


def compile_pytom(miniconda_dir):
    install_command = f'{sys.executable} compile.py --target all --includeDir /usr/include/boost $CONDA_PREFIX/lib/python3.7/site-packages/numpy/core/include/numpy $CONDA_PREFIX/include/python3.7m'
    if miniconda_dir.exists():
        install_command += f' --minicondaEnvDir {miniconda_dir}'
    process = subprocess.Popen(install_command, shell=True, cwd="pytom/pytomc")
    process.wait()


class PyTomInstaller(install):
    def run(self):
        prefix = self.prefix if self.prefix is not None else sys.prefix
        compile_pytom(pathlib.Path(prefix))
        ###compile_pytom(pathlib.Path(sys.prefix))
        install.run(self)


class PyTomDeveloper(develop):
    def run(self):
        prefix = self.prefix if self.prefix is not None else sys.prefix
        compile_pytom(pathlib.Path(prefix))
        ###compile_pytom(pathlib.Path(sys.prefix))
        develop.run(self)

        """Hacky solution, but we cannot rely on the script linking of pip in develop-mode. Pip will put scripts in the 
        miniconda bin that have a different shebang than the original ones. However, we need the pytom shebang for GPU 
        scripts to execute. Only then is the GPU environment variable properly set. Updating gpu code to the cupy 
        advised agnostic setup (as put in PyTomPrivate issue #117) should also solve this."""
        prefix = self.prefix if self.prefix is not None else sys.prefix
        miniconda_bin = pathlib.Path(prefix)
        ###miniconda_bin = pathlib.Path(self.prefix)
        scripts = find_executables()
        prefix_path = pathlib.Path(self.prefix if self.prefix is not None else sys.prefix)
        for script in scripts:
            src = pathlib.Path("pytom/bin") / pathlib.Path(script).name  # just the file name
            dst = prefix_path / "bin" / src.name
            shutil.copy(src, dst)

version = {}
exec(
    (pathlib.Path(__file__).parent / "pytom" / "version.py").read_text(),
    version
)

setup(
    name='pytom',
    version=version["__version__"],
    packages=find_namespace_packages(include=['pytom*']),
    package_dir={'pytom': 'pytom'},
    package_data={
        'pytom.angles.angleLists': ['*.em'],
        'pytom.simulation.detectors': ['*.csv'],
        'pytom.simulation.membrane_models': ['*.pdb']
    },
    data_files=[("pytom_data", ["./LICENSE.txt"])],  # This is a relative dir to sys.prefix
    include_package_data=True,
    author='`FridoF',
    author_email='strubi.pytom@uu.nl',
    url='https://github.com/SBC-Utrecht/PyTom.git',
    install_requires=['lxml', 'scipy', 'boost', 'numpy>=1.18,<2'],
    extras_require={
        'gpu': ['cupy'],
        'gui': ['PyQt5', 'pyqtgraph', 'mrcfile'],
        'all': ['cupy', 'PyQt5', 'pyqtgraph', 'mrcfile']},
    cmdclass={'install': PyTomInstaller,
              'develop': PyTomDeveloper},
    #entry_points={
        #'console_scripts': [
            #'coords2PL = pytom.convert.coords2PL:entry_point',
            #'pytom = pytom.cli:main',
            #'ipytom = pytom.cli:ipytom_main',
            #'mcoACJob = pytom.bin.mcoACJob:main',  # define main() in that file
        #],
    #}
    entry_points={'console_scripts': ['coords2PL.py = pytom.convert.coords2PL:entry_point']}
    )
