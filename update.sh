#!/bin/bash

pip install wheel
pip install twine
pip install delocate

python setup.py check
python setup.py sdist
python setup.py bdist_wheel --universal

VER=$(python loginator/loginator.py --version)
gpg --detach-sign -a "dist/loginator-$VER.tar.gz"

delocate-wheel "dist/loginator-$VER*.whl"
# twine upload --repository-url https://test.pypi.org/legacy/ "dist/loginator-$ver.tar.gz" "dist/loginator-$ver.tar.gz.asc"
twine upload "dist/loginator-$VER*"
