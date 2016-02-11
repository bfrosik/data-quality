from setuptools import setup, Extension, find_packages

setup(
    name = 'dquality',
    author = 'Barbara Frosik',
    author_email = 'bfrosik@aps.anl.gov',
    description = 'Data Quality Tools.',
    packages = find_packages(),
    version = open('VERSION').read().strip(),
    zip_safe = False,
    url='http://dquality.readthedocs.org',
    download_url='https://github.com/bfrosik/data-quality.git',
    license='BSD-3',
    platforms='Any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7']
)

