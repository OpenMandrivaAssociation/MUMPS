%define _pkgdocdir %{_docdir}/%{name}

## Define libraries' destination
%define _incmpidir %{_includedir}/openmpi-%{_arch}
%define _libmpidir %{_libdir}/openmpi/lib

## Define if use openmpi or not
%define with_openmpi 1

Name: MUMPS
Version: 4.10.0
Release: 14%{?dist}
Summary: A MUltifrontal Massively Parallel sparse direct Solver
License: Public Domain

URL: http://mumps.enseeiht.fr/
Source0: http://mumps.enseeiht.fr/%{name}_%{version}.tar.gz

# Custom Makefile changed for Fedora and built from Make.inc/Makefile.gfortran.PAR in the source.
Source1: %{name}-Makefile.par.inc
Source2: %{name}.rpmlintrc

# These patches create static and shared versions of pord, sequential and mumps libraries
# They are changed for Fedora and  derive from patches for Debian on 
# http://bazaar.launchpad.net/~ubuntu-branches/ubuntu/raring/mumps/raring/files/head:/debian/patches/
Patch0: %{name}-examples-mpilibs.patch
Patch1: %{name}-shared-pord.patch
Patch2: %{name}-shared.patch

BuildRequires: openmpi-devel >= 1.7.2
BuildRequires: blacs-openmpi-devel
BuildRequires: gcc-gfortran, blas-devel, lapack-devel
BuildRequires: scalapack-openmpi-devel

BuildRequires: openssh-clients
Requires:      %{name}-common = %{version}-%{release}
Requires:      environment-modules 

Obsoletes:     %{name}-doc < 4.10.0-12
Obsoletes:     %{name}-examples < 4.10.0-11

%description
MUMPS implements a direct solver for large sparse linear systems, with a
particular focus on symmetric positive definite matrices.  It can
operate on distributed matrices e.g. over a cluster.  It has Fortran and
C interfaces, and can interface with ordering tools such as Scotch.

%package devel
Summary: The MUMPS headers and development-related files

Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}
%description devel
Shared links, header files for MUMPS.

%package examples
Summary: The MUMPS common illustrative test programs

Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{name}-common = %{version}-%{release}
%description examples
This package contains common illustrative 
test programs about how MUMPS can be used.

%package common
Summary: Documentation files for MUMPS

BuildArch: noarch
%description common
This package contains common documentation files for MUMPS.

########################################################
%if %{with_openmpi}
%package openmpi
Summary: MUMPS libraries compiled against openmpi

BuildRequires: openmpi-devel
Requires: %{name}-common = %{version}-%{release}
%description openmpi
MUMPS libraries compiled against openmpi

%package openmpi-devel
Summary: The MUMPS headers and development-related files

BuildRequires: openmpi-devel
Requires: %{name}-common = %{version}-%{release}
Requires: %{name}-openmpi%{?_isa} = %{version}-%{release}
%description openmpi-devel
Shared links, header files for MUMPS.
%endif
##########################################################

%prep
%setup -q -n %{name}_%{version}

%patch0 -p1
%patch1 -p1
%patch2 -p1

mv examples/README examples/README-examples

%build

# Build parallel version.
rm -f Makefile.inc
cp -f %{SOURCE1} Makefile.inc

# Set build flags macro
sed -e 's|@@CFLAGS@@|%{optflags}|g' -i Makefile.inc
sed -e 's|@@-O@@|-Wl,--as-needed|g' -i Makefile.inc

sed -e 's|@@MPIFORTRANLIB@@|-lmpi_mpifh|g' -i Makefile.inc

MUMPS_MPI=openmpi
MUMPS_INCDIR=-I/usr/include/openmpi-%{_arch}

MUMPS_LIBF77="\
-L%{_libdir}/openmpi -L%{_libdir}/openmpi/lib -lmpi \
 -lmpi_mpifh -lscalapack -lmpiblacs \
 -lmpiblacsF77init -lmpiblacsCinit -llapack"

#######################################################
## Build MPI version
%if %{with_openmpi}
%{_openmpi_load}
make MUMPS_MPI="$MUMPS_MPI" \
     MUMPS_INCDIR="$MUMPS_INCDIR" \
     MUMPS_LIBF77="$MUMPS_LIBF77" \
     all
%{_openmpi_unload}

%else

## Build serial version
make MUMPS_MPI="$MUMPS_MPI" \
     MUMPS_INCDIR="$MUMPS_INCDIR" \
     MUMPS_LIBF77="$MUMPS_LIBF77" \
     all
%endif
#######################################################

# Make sure documentation is using Unicode.
iconv -f iso8859-1 -t utf-8 README > README-t && mv README-t README

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%check
# Running test programs showing how MUMPS can be used
cd examples

%{_openmpi_load}
LD_LIBRARY_PATH=$PWD:../lib:$LD_LIBRARY_PATH ./ssimpletest < input_simpletest_real
LD_LIBRARY_PATH=$PWD:../lib:$LD_LIBRARY_PATH ./csimpletest < input_simpletest_cmplx
%{_openmpi_unload}
cd ../

%install

mkdir -p $RPM_BUILD_ROOT%{_pkgdocdir}
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}/%{name}-%{version}/examples
mkdir -p $RPM_BUILD_ROOT%{_libdir}
mkdir -p $RPM_BUILD_ROOT%{_includedir}/%{name}

#########################################################
%if %{with_openmpi}
mkdir -p $RPM_BUILD_ROOT%{_libmpidir}
mkdir -p $RPM_BUILD_ROOT%{_libmpidir}/%{name}-%{version}/examples
mkdir -p $RPM_BUILD_ROOT%{_incmpidir}

%{_openmpi_load}
# Install libraries.
install -cpm 755 lib/lib*-*.so $RPM_BUILD_ROOT%{_libmpidir}

# Install development files.
install -cpm 755 lib/libmumps_common.so $RPM_BUILD_ROOT%{_libmpidir}
install -cpm 755 lib/lib*mumps.so $RPM_BUILD_ROOT%{_libmpidir}
install -cpm 755 lib/lib*mumps-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}
install -cpm 755 lib/libpord-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}
install -cpm 755 lib/libpord.so $RPM_BUILD_ROOT%{_libmpidir}

# Make symbolic links instead hard-link 
ln -sf %{_libmpidir}/libsmumps-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libsmumps.so
ln -sf %{_libmpidir}/libcmumps-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libcmumps.so
ln -sf %{_libmpidir}/libzmumps-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libzmumps.so
ln -sf %{_libmpidir}/libdmumps-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libdmumps.so
ln -sf %{_libmpidir}/libmumps_common-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libmumps_common.so
ln -sf %{_libmpidir}/libpord-%{version}.so $RPM_BUILD_ROOT%{_libmpidir}/libpord.so

install -cpm 644 include/*.h $RPM_BUILD_ROOT%{_incmpidir}
%{_openmpi_load}
%endif
##########################################################

# Install libraries.
install -cpm 755 lib/lib*-*.so $RPM_BUILD_ROOT%{_libdir}

# Install development files.
install -cpm 755 lib/libmumps_common.so $RPM_BUILD_ROOT%{_libdir}
install -cpm 755 lib/lib*mumps.so $RPM_BUILD_ROOT%{_libdir}
install -cpm 755 lib/lib*mumps-%{version}.so $RPM_BUILD_ROOT%{_libdir}
install -cpm 755 lib/libpord-%{version}.so $RPM_BUILD_ROOT%{_libdir}
install -cpm 755 lib/libpord.so $RPM_BUILD_ROOT%{_libdir}

# Make symbolic links instead hard-link 
ln -sf %{_libdir}/libsmumps-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libsmumps.so
ln -sf %{_libdir}/libcmumps-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libcmumps.so
ln -sf %{_libdir}/libzmumps-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libzmumps.so
ln -sf %{_libdir}/libdmumps-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libdmumps.so
ln -sf %{_libdir}/libmumps_common-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libmumps_common.so
ln -sf %{_libdir}/libpord-%{version}.so $RPM_BUILD_ROOT%{_libdir}/libpord.so

install -cpm 644 include/*.h $RPM_BUILD_ROOT%{_includedir}/%{name}

install -cpm 755 examples/?simpletest $RPM_BUILD_ROOT%{_libexecdir}/%{name}-%{version}/examples
install -cpm 755 examples/input_* $RPM_BUILD_ROOT%{_libexecdir}/%{name}-%{version}/examples
install -cpm 644 examples/README-examples $RPM_BUILD_ROOT%{_pkgdocdir}
install -cpm 644 doc/*.pdf $RPM_BUILD_ROOT%{_pkgdocdir}
install -cpm 644 ChangeLog LICENSE README $RPM_BUILD_ROOT%{_pkgdocdir}

#######################################################
%if %{with_openmpi}
%files openmpi
%{_libmpidir}/libpord-%{version}.so
%{_libmpidir}/lib?mumps-%{version}.so
%{_libmpidir}/libmumps_common-%{version}.so

%files openmpi-devel
%{_incmpidir}/*.h
%{_libmpidir}/lib?mumps.so
%{_libmpidir}/libmumps_common.so
%{_libmpidir}/libpord.so
%endif
#######################################################

%files
%{_libdir}/libpord-%{version}.so
%{_libdir}/lib?mumps-%{version}.so
%{_libdir}/libmumps_common-%{version}.so

%files devel
%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.h
%{_libdir}/lib?mumps.so
%{_libdir}/libmumps_common.so
%{_libdir}/libpord.so

%files common
## This directory contains README*, LICENSE, ChangeLog, UserGuide files
%{_pkgdocdir}/

%files examples
%dir %{_libexecdir}/%{name}-%{version}
%{_libexecdir}/%{name}-%{version}/examples/

%changelog
* Wed Aug 28 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-14
- 'blacs-openmpi-devel' request unversioned
- Defined which version of MUMPS-doc package is obsolete

* Wed Aug 07 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-13
- Obsolete packages are now versioned (bz#993574)
- Adding redefined _pkgdocdir macro for earlier Fedora versions to conform
  this spec with 'F-20 unversioned docdir' change (bz#993984)

* Mon Jul 29 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-12
- Old MUMPS subpackages are now obsoletes

* Sat Jul 27 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-11
- Added new macros for 'openmpi' destination directories
- Done some package modifications according to MPI guidelines
- This .spec file now produces '-openmpi', '-openmpi-devel', '-common' packages
- Added MUMPS packaging in "serial mode"
- %%{name}-common package is a noarch
- Added an '-examples' subpackage that contains all test programs

* Tue Jul 23 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-10
- 'openmpi-devel' BR changed to 'openmpi-devel>=1.7'
- 'blacs-openmpi-devel' BR changed to 'blacs-openmpi-devel>=1.1-50'
- Removed '-lmpi_f77' library link, deprecated starting from 'openmpi-1.7.2'

* Sat Mar 23 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-9
- Removed '-Wuninitialized -Wno-maybe-uninitialized' flags because unrecognized
  in EPEL6
- Added condition to load MPI module properly

* Sat Mar 02 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-8
- Removed %%post/%%postun commands for devel sub-package

* Thu Feb 28 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-7
- Exchanged versioned/unversioned libs between main and devel packages
- Set up a doc subpackage that cointains PDF documentation
- Erased .ps documentation
- ChangeLog even in devel package
- SourceX/PatchY prefixed with %%{name}
- Added 'openssh-clients' to BuildRequires

* Wed Feb 27 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-6
- Removed 'libopen-pal.so.4' and 'libopen-rte.so.4' private libraries exclusion
- Imposed '-Wl,--as-needed' flags to the libopen-pal/-rte libs in shared-mumps.patch
- Added '-Wuninitialized -Wno-maybe-uninitialized' in shared-mumps.patch 
  to silence '-Wmaybe-uninizialized' warnings 

* Tue Feb 26 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-5
- Removed sequential version building
- Removed Make.seq.inc file from sources
- Set up of OPT* entries in the Make.par.inc file

* Mon Feb 25 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-4
- Added %%check section

* Mon Feb 25 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-3
- Sequential version's Make command  pointed to openmpi header/lib files
- Set optflags macros

* Fri Feb 22 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-2
- Add '_includedir/MUMPS' directory, header files moved into
- 'Buildroot:' line removed
- Manuals pdf/ps included as %%doc files
- Add a new sub-package 'examples', it contains test files and relative README
- LICENSE and README files in %%doc
- '%%clean section' removed
- 'rm -rf %%{buildroot}' and '%%defattr' lines removed
- Compiler flags included in custom Makefile.par.inc/Makefile.seq.inc files

* Wed Feb 20 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-1
- 'libopen-pal.so.4' and 'libopen-rte.so.4' private libraries exclusion

* Wed Feb 20 2013 Antonio Trande <sagitter@fedoraproject.org> - 4.10.0-0
- Remove exec permissions to remove 'script-without-shebang' errors
- Make symbolic links instead hard-link 
- Make sure documentation is using Unicode.
- Add Package patches and custom Makefiles changed for Fedora.
- Initial package.
