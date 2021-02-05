import supabase_py

import setuptools


def get_package_description() -> str:
    """Returns a description of this package from the markdown files."""
    with open("README.md", "r") as stream:
        readme: str = stream.read()
    return readme


setuptools.setup(
    name="mitto",
    version=supabase_py.__version__,
    author="Joel Lee, Leon Fedden",
    author_email="joel@joellee.org",
    description="Supabase client for Python.",
    long_description=get_package_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/supabase/supabase-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
