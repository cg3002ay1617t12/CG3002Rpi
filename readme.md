CG3002 Raspberry Pi code

## Setup pip, virtualenv and virtualenvwrapper for Linux and OS X
1. pip install -U pip
2. pip install virtualenv
3. pip install virtualenvwrapper
4. export WORKON_HOME=~/Envs
5. source /usr/local/bin/virtualenvwrapper.sh
6. Create virtualenv: mkvirtualenv reborn
7. Install dependencies: pip install -r requirements.txt
8. To enter virtualenv: workon name-of-virtualenv
9. To exit virtualenv: deactivate

## Instructions to get matplotlib working with virtualenv (for MAC OS X)
Reference: http://matplotlib.org/faq/virtualenv_faq.html

1.  Copy the following to a file called fpython in the site-packages directory of your virtualenv
(Normally its /Users/YOU/.virtualenvs/name-of-virtualenv/lib/python2.7/site-packages/)

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

Make sure that fpython is an executable, if not, ```sudo chmod +x fpython``` on the command line

2. Run framework python when running scripts that require matplotlib - fpython name_of_script.py

3. Running step_detection:

Connect arduino with IMU chip to serial port, find address of your serial port. Easiest way is to open arduino IDE,
tools -> port, or another way is to go to /dev (for MAC users) and trial and error from all the file descriptors listed there

Open serial_input, change SERIAL to your own serial address, DO NOT COMMIT this change

Open 2 terminal window - first: fpython step_dection.py (this is the master process, hence must run first)
						 second: fpython serial_input.py

How to terminate: fpython will run forever and is not well behaved to CTRL-C signals from keyboard, surest way is to kill process from activity monitor or commmand line

2 files will be created in local folder - pid contains pid of the master process, so client can send signal interrupts to master,
pipe is the named pipe created to transfer data between 2 processes
