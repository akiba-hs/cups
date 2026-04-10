# Akiba CUPS
Provides a Docker image for CUPS with:

- Canon LBP-810 CAPT driver (`capt_lbp810-1120`)
- official Linux TSPL filters from iDPRT (`raster-tspl`, `raster-esc`)
- `TDP-245-fixed-tspl.ppd`, a single-purpose queue profile generated from the filter-compatible iDPRT `sp410.tspl.ppd` with hard-wired media, `PaperType=1`, `203dpi`, and no `CustomPageSize`

## Installation
1. Copy `compose.yml` to the server with the attached printer.
2. Build the image. It hard-codes the fixed `30 x 20 mm`, `gap 2 mm` label profile in `Dockerfile`:
   ```bash
   docker compose build
   docker compose up -d
   ```
3. Discover the stable USB URI:
   ```bash
   docker compose exec cups lpinfo -v
   ```
4. Add Canon LBP-810:
   ```bash
   docker compose exec cups lpadmin -p Canon-LBP-810 -E -v 'usb://...' -P /usr/share/cups/model/Canon-LBP-810-capt.ppd
   ```
5. Add the fixed TSPL/XPrinter queue:
   ```bash
   docker compose exec cups lpadmin -p XPrinter-30x20 -E -v 'usb://...' -P /usr/share/cups/model/tspl/TDP-245-fixed-tspl.ppd
   ```
6. Add the network printer to the client OS by IPP/LPD using host `<host>:631`.

## Manual PPD Generation
You can generate another fixed PPD manually if you need a different hard-coded size:

```bash
python3 /usr/local/bin/generate_tdp245_ppd.py \
  /usr/share/cups/model/tspl/sp410.tspl.ppd \
  /usr/share/cups/model/tspl/TDP-245-fixed-tspl.ppd \
  30 20 2
```

The generator interface is:

```bash
generate_tdp245_ppd.py SOURCE_PPD DEST_PPD WIDTH_MM HEIGHT_MM GAP_MM
```

Important limitation: with the current official `raster-tspl` filter path, only `GAP 2 mm` is confirmed to propagate correctly. The generator accepts `gap_mm` as an explicit parameter, but currently rejects values other than `2` so the queue does not claim unsupported behavior.

This fixed-profile approach is the safer option for browser/GUI printing because the client only sees one paper size and cannot pick `20 x 30`, `4x6`, or arbitrary `CustomPageSize` values from printer capabilities. It does not fully prevent browser-side scaling or orientation overrides, but it removes the main server-side media mismatch.

With the current compose setup, CUPS sees the real USB bus and can return stable `usb://...` URIs that usually include device identity data such as vendor, model, and serial. Prefer that URI over `/dev/usb/lp*`, because it survives cable replugging and port changes much better.

## Avahi Setup
Install avahi:
```bash
apt install avahi-daemon
```

To enable printer discovery on the network, add files:

`/etc/avahi/services/cups-lbp810.service`:
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

`/etc/avahi/services/cups-xprinter.service`:
```xml
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">XPrinter 30x20mm</name>
  <service>
    <type>_ipp._tcp</type>
    <subtype>_universal._sub._ipp._tcp</subtype>
    <port>631</port>
    <txt-record>txtvers=1</txt-record>
    <txt-record>qtotal=1</txt-record>
    <txt-record>rp=printers/XPrinter-30x20</txt-record>
    <txt-record>ty=XPrinter 30x20mm</txt-record>
    <txt-record>product=(TSPL printer via CUPS)</txt-record>
    <txt-record>adminurl=http://%h:631/printers/XPrinter-30x20</txt-record>
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
