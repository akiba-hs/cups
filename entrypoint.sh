#!/bin/bash
set -e

if [ "$(grep -ci "$CUPSADMIN" /etc/shadow)" -eq 0 ]; then
    useradd -r -G lpadmin -M "$CUPSADMIN"
    echo "$CUPSADMIN:$CUPSPASSWORD" | chpasswd
    ln -fs "/usr/share/zoneinfo/$TZ" /etc/localtime
    dpkg-reconfigure --frontend noninteractive tzdata
fi

if [ ! -f /etc/cups/cupsd.conf ]; then
    cp -rpn /etc/cups-bak/* /etc/cups/
fi

# The Coolify bind mount can be owned by the host deploy user. CUPS filters
# run as lp, so keep the mounted PPD tree traversable and readable.
if [ -d /etc/cups/ppd ]; then
    chmod 755 /etc/cups /etc/cups/ppd
    find /etc/cups/ppd -maxdepth 1 -type f -name '*.ppd' -exec chmod 644 {} +
fi

# saned needs the same USB access as the CUPS backend.
if id saned >/dev/null 2>&1 && getent group lp >/dev/null 2>&1; then
    usermod -a -G lp saned
fi

# Start SANE's standalone TCP server when the image has sane-utils installed.
# It is deliberately separate from CUPS: CUPS provides printing, saned provides
# scanner access on port 6566.
if command -v saned >/dev/null 2>&1; then
    saned -l -D -u saned -b 0.0.0.0 -p 6566
fi

exec /usr/sbin/cupsd -f
