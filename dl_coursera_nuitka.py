import subprocess
import platform
import os
import shutil

from dl_coursera import app_name, app_version


def main():
    outdir = f'{app_name}-{app_version}-nuitka-{platform.system()}-{platform.machine()}'
    exe = app_name
    if platform.system() == 'Windows':
        exe += '.exe'

    env = dict(os.environ)
    env['PYTHONPATH'] = os.getcwd()
    subprocess.run(
        f"""python -m nuitka
            --follow-imports --standalone --onefile --assume-yes-for-downloads
            --include-module=lxml.etree
            --include-package-data=dl_coursera.resource
            --output-dir=__data/{outdir}
            --output-filename={exe}
            dl_coursera_run.py""".split(),
        check=True,
        env=env,
    )

    os.chdir('__data')

    subprocess.run([os.path.join(outdir, exe), '--version'], check=True)
    subprocess.run([os.path.join(outdir, exe), '--help'], check=True)

    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.build'))
    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.dist'))
    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.onefile-build'))
    shutil.make_archive(
        base_name=outdir, format="zip", root_dir='.', base_dir=outdir, verbose=True
    )


if __name__ == '__main__':
    main()
