CG3002 Raspberry Pi code

## Setup pip, virtualenv and virtualenvwrapper for Linux and OS X
1. pip install -U pip
2. pip install virtualenv
3. pip install virtualenvwrapper
4. export WORKON_HOME=~/Envs
5. source /usr/local/bin/virtualenvwrapper.sh
6. Create virtualenv: mkvirtualenv reborn
7. Install dependencies: pip install -r requirements.txt
8. To exit virtualenv: deactivate

## Instructions to get matplotlib working with virtualenv (for MAC OS X)
Reference: http://matplotlib.org/faq/virtualenv_faq.html

1.  Copy the following to a file called fpython in the site-packages directory of your virtualenv

```bash
#!/bin/bash
# what real Python executable to use
PYVER=2.7
PATHTOPYTHON=/usr/local/bin/
PYTHON=${PATHTOPYTHON}python${PYVER}

# find the root of the virtualenv, it should be the parent of the dir this script is in
ENV=`$PYTHON -c "import os; print(os.path.abspath(os.path.join(os.path.dirname(\"$0\"), '..')))"`

# now run Python with the virtualenv set as Python's HOME
export PYTHONHOME=$ENV
exec $PYTHON "$@"
```

2. Run framework python when running scripts that require matplotlib - fpython name_of_script.py