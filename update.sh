#!/bin/bash

pip install wheel

pip install twine
python setup.py check
python setup.py sdist bdist_wheel

pip install twine

VER=$(python loginator/loginator.py --version)
python setup.py bdist_wheel
gpg --detach-sign -a "dist/loginator-$VER.tar.gz"
# twine upload --repository-url https://test.pypi.org/legacy/ "dist/loginator-$ver.tar.gz" "dist/loginator-$ver.tar.gz.asc"
twine upload "dist/loginator-$VER.tar.gz" "dist/loginator-$VER.tar.gz.asc"
