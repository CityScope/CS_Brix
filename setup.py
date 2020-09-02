import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cs-brix", # Replace with your own username
    version="0.0.1",
    author="CityScience MIT",
    author_email="csadmin@media.mit.edu",
    description="Set of tools to deploy CityScope indicators.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CityScope/CS_Brix",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)