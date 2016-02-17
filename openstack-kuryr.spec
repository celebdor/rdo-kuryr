%global service kuryr

Name:           openstack-%{service}-libnetwork
Version:        XXX
Release:        XXX
Epoch:          0
Summary:        Docker libnetwork driver for OpenStack Neutron

License:        ASL 2.0
URL:            http://launchpad.net/%{service}/

Source0:        http://tarballs.openstack.org/%{service}/%{service}-master.tar.gz
Source1:        %{service}.logrotate
Source2:        %{service}-dist.conf
Source2:        %{service}-libnetwork.service
Source3:        launcher.c

BuildArch:      noarch

BuildRequires:  libcap
BuildRequires:  gcc
BuildRequires:  git
BuildRequires:  pkgconfig
BuildRequires:  python2-devel
BuildRequires:  python-oslo-concurrency
BuildRequires:  python-oslo-config
BuildRequires:  python-oslo-db
BuildRequires:  python-oslo-log
BuildRequires:  python-pbr
BuildRequires:  python-setuptools
BuildRequires:  systemd-units

Requires:       openstack-%{service}-common = %{epoch}:%{version}-%{release}

# Docker is not required but it doesn't make sense to run Kuryr libnetwork
# driver without it
Requires: docker

Requires(pre): shadow-utils
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
Kuryr is the OpenStack project that brings the OpenStack virtual network
service, Neutron, to containers. This package provides a driver for Docker's
implementation of the Container Network Model, libnetwork. Thanks to it, one
can have Docker containers easily plugged into Neutron networks and easily
connect them to Virtual Machines under the same networking technology.


%package -n python-%{service}
Summary:        Kuryr Python libraries
Requires:       python-babel >= 1.3
Requires:       python-flask >= 0.10
Requires:       python-jsonschema >= 2.0.0
Requires:       python-netaddr >= 0.7.5
Requires:       python-oslo-concurrency >= 2.3.0
Requires:       python-oslo-config >= 2:2.1.0
Requires:       python-oslo-serialization >= 1.4.0
Requires:       python-oslo-utils >= 2.0.0
Requires:       python-neutronclient >= 2.4.0
Requires:       python-pyroute2 >= 0.3.10
Requires:       python2-os-client-config >= 1.7.5



%description -n python-%{service}
Kuryr provides facilities for plugging containers into OpenStack
Neutron networks.

This package contains the Kuryr Python library.


%package -n python-%{service}-tests
Summary:        Kuryr tests
Requires:       python-%{service} = %{epoch}:%{version}-%{release}


%description -n python-%{service}-tests
Kuryr provides facilities for plugging containers into OpenStack
Neutron networks.

This package contains Kuryr test files.


%package common
Summary:        Kuryr common files
Requires:       python-%{service} = %{epoch}:%{version}-%{release}


%description common
Kuryr provides facilities for plugging containers into OpenStack
Neutron networks.

This package contains Kuryr common files.


%prep
%autosetup -n %{service}-%{upstream_version} -S git

find %{service} -name \*.py -exec sed -i '/\/usr\/bin\/env python/{d;q}' {} +

# Let's handle dependencies ourseleves
rm -f requirements.txt

# Kill egg-info in order to generate new SOURCES.txt
rm -rf kuryr.egg-info


%build
export SKIP_PIP_INSTALL=1
%{__python2} setup.py build

# Generate configuration files
PYTHONPATH=. oslo-config-generator --config-file=etc/kuryr-config-generator.conf
find etc -name *.sample | while read filename
do
    filedir=$(dirname $filename)
    file=$(basename $filename .sample)
    mv ${filename} ${filedir}/${file}
done

# Loop through values in kuryr-dist.conf and make sure that the values
# are substituted into the kuryr.conf as comments. Some of these values
# will have been uncommented as a way of upstream setting defaults outside
# of the code. For notification_driver, there are commented examples
# above uncommented settings, so this specifically skips those comments
# and instead comments out the actual settings and substitutes the
# correct default values.
while read name eq value; do
  test "$name" && test "$value" || continue
  sed -ri "0,/^(#)? *$name *=/{s!^(#)? *$name *=.*!# $name = $value!}" etc/%{service}.conf
done < %{SOURCE2}

%install
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}

# Compile the usermode launcher
%{__cc} `pkg-config -`pkg-config --libs --cflags-only-I python2` launcher.c -o kuryr-libnetwork

# Give CAP_NET_ADMIN to the Kuryr usermode launcher
setcap cap_net_admin+eip kuryr-libnetwork

# Move the Kuryr usermode launcher to bindir
install -d -m 755 kuryr-usermode %{_bindir}/kuryr-libnetwork

# Move config files to proper location
install -d -m 755 %{buildroot}%{_sysconfdir}/%{service}
mv etc/%{service}.conf %{buildroot}%{_sysconfdir}/%{service}/%{service}.conf

# Install logrotate
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-%{service}

# Install systemd units
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_unitdir}/kuryr-libnetwork.service

# Setup directories
install -d -m 755 %{buildroot}%{_libexecdir}/%{service}
install -D usr/libexec/%{service}/* %{_libexecdir}/%{service}
install -d -m 755 %{buildroot}%{_localstatedir}/log/%{service}
install -d -m 755 %{buildroot}%{_sysconfdir}/docker/plugins
install -D -p -m 644 etc/%{service}.json %{buildroot}%{_sysconfdir}/docker/plugins/%{service}.json

%pre common
getent group %{service} >/dev/null || groupadd -r %{service}
getent passwd %{service} >/dev/null || \
    useradd -r -g %{service} -d %{_sharedstatedir}/%{service} -s /sbin/nologin \
    -c "OpenStack Kuryr Daemons" %{service}
exit 0


%post
%systemd_post kuryr-libnetwork.service


%preun
%systemd_preun kuryr-libnetwork.service


%postun
%systemd_postun_with_restart kuryr-libnetwork.service


%files
%license LICENSE
%{_bindir}/kuryr-server
%{_bindir}/kuryr-libnetwork
%{_unitdir}/kuryr-libnetwork.service
%attr(-, root, %{service}) %{_datadir}/%{service}/api-paste.ini
%dir %{_datadir}/%{service}/l3_agent
%dir %{_datadir}/%{service}/server
%{_datadir}/%{service}/l3_agent/*.conf
%dir %{_libexecdir}/%{service}


%files -n python-%{service}-tests
%license LICENSE
%{python2_sitelib}/%{service}/tests


%files -n python-%{service}
%license LICENSE
%{python2_sitelib}/%{service}
%{python2_sitelib}/%{service}-*.egg-info
%exclude %{python2_sitelib}/%{service}/tests


%files common
%license LICENSE
%dir %{_sysconfdir}/%{service}
%config(noreplace) %attr(0640, root, %{service}) %{_sysconfdir}/%{service}/%{service}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/*


%changelog
