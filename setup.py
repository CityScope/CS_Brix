import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

try:
    with open("requirements.txt") as f:
        INSTALL_REQUIRES = [line.strip() for line in f.readlines()]
except:
    INSTALL_REQUIRES = [
        "requests>=2.24",
        "pandas>=0.25.3",
        "pygeohash>=1.2.0",
        "joblib>=0.13.2",
        "shapely>=1.6.2",
        "geopandas>=0.6.2",
        "geopy>=1.20.0",
        "networkx>=2.4"
    ]


setuptools.setup(
    name="cs-brix",
    version="0.0.8",
    license='GNU General Public License v3.0 only (GPL-3.0-only)',
    author="CityScience MIT",
    author_email="csadmin@media.mit.edu",
    description="Brix is a python library for CityScope modules which handles communication with City I/O.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CityScope/CS_Brix",
    download_url = 'https://github.com/CityScope/CS_Brix/archive/v_0.0.8.tar.gz',
    packages=setuptools.find_packages(),
    install_requires=INSTALL_REQUIRES,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6',
)