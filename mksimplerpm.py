#!/usr/bin/python

from __future__ import print_function
import distutils.spawn
import optparse
import os
import shlex
import shutil
import string
import subprocess
import sys
import tarfile
import tempfile

DEFAULT_DESTINATION = '/usr/bin'

def main(args=None):
    args = args or sys.argv
    parser = optparse.OptionParser()
    parser.add_option('-n', '--name', action='store', dest='rpm_name',
                      default=None, help='name of rpm')
    parser.add_option('-v', '--version', action='store', dest='version',
                      default=None, help='Version of rpm')
    parser.add_option('-r', '--requires', action='store', dest='requires',
                      default='rpm', help='rpms dependencies')
    parser.add_option('-s', '--summary', action='store', dest='summary',
                      default=None, help='short rpm description')
    parser.add_option('-d', '--directory', action='store', dest='directory',
                      default=DEFAULT_DESTINATION,
                      help='Destination directory of scripts')
    parser.add_option('-o', '--only-src', action='store_true', dest='only_src',
                      help='make only source rpm')

    settings, args = parser.parse_args(args[1:])

    if settings.rpm_name is None:
        parser.error('-n or --name is required, can\'t create rpm without a name')
        return 5

    elif settings.version is None:
        parser.error('-v or --version is required')

    args_dict = {}
    if not args:
        print('No files provided', file=sys.stderr)
        return 7

    name = '{}-{}'.format(settings.rpm_name, settings.version)

    tmpdir = tempfile.mkdtemp(suffix='.mksimplerpm-%s' % settings.rpm_name)
    todir = os.path.join(tmpdir, name)
    os.mkdir(todir)

    for filename in args:
        if ':' in filename:
            curr_name, new_name = filename.split(':', 1)

            if new_name.startswith('/'):
                args_dict[curr_name] = new_name
            else:
                args_dict[curr_name] = os.path.join(settings.directory, new_name)

        else:
            args_dict[filename] = os.path.join(settings.directory, filename)

    for curr_name, destination_path in args_dict.items():

        os.makedirs(os.path.dirname(os.path.normpath(todir + destination_path)))
        shutil.copyfile(curr_name, os.path.normpath(todir + destination_path))

    spec_path = os.path.join(todir, '%s.spec' % settings.rpm_name)
    spec_templ = string.Template(spec_template)

    fp = open(spec_path, 'w')
    try:
        fp.write(
            spec_templ.substitute(
                name=settings.rpm_name,
                version=settings.version,
                summary=settings.summary or "rpm summary",
                files='\n'.join(args_dict.values()),
                requires=settings.requires,
                directory=settings.directory
                )
            )
    finally:
        fp.close()

    here = os.getcwd()
    try:
        os.chdir(tmpdir)
        tar = tarfile.open('%s.tar.gz' % name, 'w:gz')
        try:
            tar.add(name)
        finally:
            tar.close()

        if not distutils.spawn.find_executable('rpmbuild'):
            print('`rpmbuild` is not installed: yum install rpm-build', file=sys.stderr)
            return 9

        retcode = subprocess.call(
            'rpmbuild -bs --nodeps --define "_sourcedir ."'
            ' --define "_srcrpmdir ." %s/%s.spec' % (name, settings.rpm_name),
            shell=True
            )

        if settings.only_src or retcode != 0:
            return retcode

        for dname in ('RPMS', 'SRPMS', 'SOURCES', 'SPECS', 'BUILD'):
            os.mkdir(os.path.join(tmpdir, dname))

        src_rpm, = set(find(tmpdir, ext='.src.rpm'))
        return subprocess.call(
            'rpmbuild --rebuild'
            ' --define "%%_topdir %s" %s' % (tmpdir, src_rpm),
            shell=True
            )

    finally:
        for fname in find(tmpdir, ext='.rpm'):
            shutil.move(fname, here)
        os.chdir(here)


def find(topdir, ext=None):
    for root, _, filelist in os.walk(topdir):
        for filename in filelist:
            if ext is not None:
                if filename.endswith(ext):
                    yield os.path.join(root, filename)
            else:
                yield os.path.join(root, filename)


spec_template = '''\
Summary: ${summary}
Name: ${name}
Version: ${version}
release: 1
license: Proprietary
BuildArch: noarch
Group: System Environment/System
AutoReqProv: no
Source: %{name}-%{version}.tar.gz
BuildRoot: /var/tmp/%{name}-%{version}-root
Requires: ${requires}

%description
${summary}

%prep
%setup

%build
printf "No build\\n"

%install
test -d $$RPM_BUILD_ROOT && rm -rf $$RPM_BUILD_ROOT
mkdir -p $$RPM_BUILD_ROOT
rm ${name}.spec
find usr/bin -type f -exec chmod 755 {} \;
find etc -type f -exec chmod 644 {} \;
mv * "$$RPM_BUILD_ROOT"

%pre
printf "no much here\\n"

%clean
rm -rf %RPM_BUILD_ROOT

%files
%defattr(-, root, root, -)
${files}

%changelog
* Tue Aug 09 2018 mrsipan
- Created by mksimplerpm
'''

if __name__ == '__main__':
    sys.exit(main())
