import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Projet-deploiement",
    version="0.0.3",
    author="Guillaume VANEL",
    author_email="guillaume.vanel@insa-lyon.fr",
    description="Un projet de création d'un package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/draguar/ProjetSergio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)