import setuptools

import dl_coursera


def _read(filename):
    with open(filename, encoding='UTF-8') as ifs:
        return ifs.read()


def _readlines(filename):
    return [_ for _ in _read(filename).split('\n') if len(_) > 0]


setuptools.setup(
    name=dl_coursera.app_name,
    version=dl_coursera.app_version,
    author='fengleizZZ',
    author_email='fenglei4518@hotmail.com',
    description='A simple, fast, and reliable Coursera crawling & downloading tool',
    long_description=_read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/feng-lei/dl_coursera',
    keywords=['dl_coursera', 'coursera', 'coursera-dl', 'download', 'education', 'MOOC'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Education'
    ],
    python_requires='>=3.5',
    install_requires=_readlines('requirements.txt'),
    extras_require={'dev': _readlines('requirements-dev.txt')},
    py_modules=['dl_coursera_run'],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            '%s=dl_coursera_run:main' % dl_coursera.app_name
        ]
    },
    include_package_data=True,
    package_data={
        'dl_coursera.resource': ['*.zip', 'template/*']
    },
    platforms=['any']
)
