# Akiba CUPS
Provides Docker image for CUPS with pre-installed Canon LBP-810 driver (https://github.com/caxapyk/capt_lbp810-1120).

## Installation
1. Copy compose.yml to server with attached printer
2. `docker compose up -d`
3. Add printer: `docker compose exec cups-lbp810 lpadmin -p Canon-LBP-810 -P /usr/share/cups/model/Canon-LBP-810-capt.ppd -E`
3. Go to `http://<host>:631` -> Printers -> Canon-LBP-810 -> setup default parameters -> Miscellaneous -> Reset printer before printing -> AlwaysReset
4. Add network printer to your favourite OS by protocol LPD and host `<host>:631`

## Avahi Setup
Install avahi:
```bash
apt install avahi-daemon
```

To enable printer discovery on the network, add file `/etc/avahi/services/cups-lbp810.service` with following contents:
```xml
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">Canon LBP-810 on %h</name>

  <service>
    <type>_ipp._tcp</type>
    <subtype>_universal._sub._ipp._tcp</subtype>
    <port>631</port>

    <txt-record>txtvers=1</txt-record>
    <txt-record>qtotal=1</txt-record>
    <txt-record>rp=printers/Canon-LBP-810</txt-record>
    <txt-record>ty=Canon LBP-810</txt-record>
    <txt-record>product=(Canon LBP-810 via CUPS)</txt-record>
    <txt-record>note=AirPrint via CUPS</txt-record>
    <txt-record>adminurl=http://%h:631/printers/Canon-LBP-810</txt-record>
    <txt-record>URF=none</txt-record>
    <txt-record>pdl=application/pdf,application/postscript,image/urf</txt-record>
    <txt-record>Color=F</txt-record>
    <txt-record>Duplex=F</txt-record>
  </service>
</service-group>
```

Restart Avahi:
```bash
systemctl restart avahi-daemon
```
