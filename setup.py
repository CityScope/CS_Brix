import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cs-brix",
    version="0.0.1",
    license='GNU GENERAL PUBLIC LICENSE',
    author="CityScience MIT",
    author_email="csadmin@media.mit.edu",
    description="Brix is a python library for CityScope modules which handles communication with City I/O.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CityScope/CS_Brix",
    download_url = 'https://github.com/CityScope/CS_Brix/archive/v_0.0.1.tar.gz',
    packages=setuptools.find_packages(),
    install_requires=[
        'requests>=2.22',
        'pandas>=0.25.3',
        'Geohash>=1.0',
        'python-geohash>=0.8.5',
        'joblib>=0.13.2',
        'shapely>=1.6.2',
        'geopandas>=0.6.2',
        'geopy>=1.20.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        "License :: GNU GENERAL PUBLIC LICENSE",
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.6',
)