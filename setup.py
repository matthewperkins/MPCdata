import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="MPCdata",
    version="0.0.2.7",
    author="Matthew Perkins",
    author_email="matthew.perkins@mssm.edu",
    description="Package to read Med Associates Files MedPCIV",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matthewperkins/MPCdata",
    packages=setuptools.find_packages(),
    install_requires=['pandas',
                      'numpy',
                      'xlsxwriter'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
