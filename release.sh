echo "Prepare and upload a new Tokenizer version"
python setup.py bdist_wheel --universal
python setup.py sdist
twine upload dist/tokenizer-$1*

