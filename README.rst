Make a simple RPM file
======================

This python script makes a simple RPM file from a list of 
files passed as positional parameters.

For example, make an RPM file named ``mksimplerpm`` out of this script::

    ./mksimplerpm.py -s 'Make an rpm' -d /bin -n makesimplerpm -v 0.1 mksimplerpm.py:mksimplerpm

This will make an RPM file ``mksimplerpm-0.1`` add a summary/description *Make
an rpm*, and add the ``mksimplerpm.py`` file which will be renamed
``mksimplerpm`` and installed in ``/bin``.

Usage::

    -n RPM_NAME, --name=RPM_NAME
                          name of rpm
    -v VERSION, --version=VERSION
                          Version of rpm
    -r REQUIRES, --requires=REQUIRES
                          rpms dependencies
    -s SUMMARY, --summary=SUMMARY
                          short rpm description
    -d DIRECTORY, --directory=DIRECTORY
                          Destination directory of scripts
    -o, --only-src        make only source rpm


