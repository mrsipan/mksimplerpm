#!/usr/bin/python

import os
import sys
import tarfile
import tempfile
import string
import optparse
import shutil
import subprocess
import shlex


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
                      default='/usr/local/bin', help='Destination directory of scripts')
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
        print >> sys.stderr, "No files provided"
        return 7
    else:
        for arg in args:
            if ':' in arg:
                k, v = arg.split(':', 1)
                args_dict[k] = v
            else:
                args_dict[arg] = arg

    name = '%s-%s' % (settings.rpm_name, settings.version)

    tmpdir = tempfile.mkdtemp(suffix='.mksimplerpm-%s' % settings.rpm_name)
    todir = os.path.join(tmpdir, name)
    os.mkdir(todir)

    for old_name, new_name in args_dict.items():
        shutil.copyfile(old_name, os.path.join(todir, new_name))

    spec_path = os.path.join(todir, '%s.spec' % settings.rpm_name)
    spec_templ = string.Template(spec_template)

    fp = open(spec_path, 'w')
    try:
        fp.write(
            spec_templ.substitute(
                name=settings.rpm_name,
                version=settings.version,
                summary=settings.summary or "rpm summary",
                files=' '.join([os.path.basename(arg) for arg in args_dict.values()]),
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

        if not os.path.exists('/usr/bin/rpmbuild'):
            print >> sys.stderr, '`rpmbuild` is not installed: yum install rpm-build'
            return 9

        retcode = subprocess.call(
            shlex.split(
                '/usr/bin/rpmbuild -bs --nodeps --define "_sourcedir ."'
                ' --define "_srcrpmdir ." %s/%s.spec' % (name, settings.rpm_name)
                )
            )

        if settings.only_src or retcode != 0:
            return retcode

        for dname in ('RPMS', 'SRPMS', 'SOURCES', 'SPECS', 'BUILD'):
            os.mkdir(os.path.join(tmpdir, dname))

        src_rpm, = set(find(tmpdir, ext='.src.rpm'))
        return subprocess.call(
            shlex.split(
                '/usr/bin/rpmbuild --rebuild'
                ' --define "%%_topdir %s" %s' % (tmpdir, src_rpm))
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
mkdir -p $$RPM_BUILD_ROOT/${directory}
files="${files}"
for file in $$files; do
  mv $$file "$$RPM_BUILD_ROOT/${directory}/$$file"
done

%pre
printf "no much here\\n"

%clean
rm -rf %RPM_BUILD_ROOT

%files
%defattr(755, root, root, -)
${directory}/*


%changelog
* Tue Aug 09 2011 Ben Sanchez
- Created by mksimplerpm
'''

if __name__ == '__main__':
    sys.exit(main())