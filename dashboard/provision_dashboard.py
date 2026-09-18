#!/usr/bin/env python3
"""Bikin dashboard ThingsBoard untuk device EKG, lalu simpan export-nya.

    python3 provision_dashboard.py          # bikin/replace dashboard + tulis JSON

Dashboard dibangun lewat REST, bukan diklik di UI, supaya bisa diulang setelah
`docker compose down -v` dan supaya diff-nya kelihatan di git. Hasil export
ditulis ke dashboard_ekg.json -- itu artefak yang dijanjikan folder ini.

Widget diambil dari bundle bawaan; yang diubah cuma datasource (diarahkan ke
entity alias device kita) dan dataKeys (nama field dari payload). Tidak ada
widget custom, tidak ada JS yang ditulis tangan.
"""
import json
import random
import sys
import urllib.error
import urllib.parse
import uuid

from smoke_test import DEVICE, provision, rest

TITLE = "Pemantauan EKG"
OUT = "dashboard_ekg.json"

# Widget diambil dari bundle bawaan ThingsBoard. defaultConfig-nya berisi contoh
# suhu ruangan, jadi units/ikon/label wajib ditimpa -- kalau tidak, BPM tampil
# sebagai "76 degC" dengan ikon termostat.
WIDGETS = [
    dict(fqn="cards.value_card", type="latest", title="Detak jantung",
         keys=[("bpm", "BPM", "#e91e63")], col=0, row=0, sx=4, sy=3,
         units="bpm", decimals=0,
         settings={"showIcon": True, "icon": "favorite", "layout": "square",
                   "iconColor": {"type": "constant", "color": "#e91e63"},
                   "labelColor": {"type": "constant", "color": "rgba(0,0,0,0.87)"},
                   "valueColor": {"type": "constant", "color": "rgba(0,0,0,0.87)"}}),
    dict(fqn="label_value_card", type="latest", title="Hasil inferensi",
         keys=[("label_str", "Klasifikasi", "#f57c00")], col=4, row=0, sx=4, sy=2,
         units="", decimals=0, show_title=False,
         settings={"label": "Klasifikasi", "showLabel": True, "autoScale": True,
                   "icon": "monitor_heart", "iconColor": {"type": "constant", "color": "#f57c00"}}),
    dict(fqn="label_value_card", type="latest", title="Kualitas sinyal",
         keys=[("signal_quality", "Sinyal", "#607d8b")], col=4, row=2, sx=4, sy=2,
         units="", decimals=0, show_title=False,
         settings={"label": "Kualitas sinyal", "showLabel": True, "autoScale": True,
                   "icon": "sensors", "iconColor": {"type": "constant", "color": "#607d8b"}}),
    dict(fqn="cards.value_card", type="latest", title="Keyakinan",
         keys=[("confidence", "Confidence", "#3f51b5")], col=8, row=0, sx=4, sy=3,
         units="", decimals=2,
         settings={"showIcon": True, "icon": "verified", "layout": "square",
                   "iconColor": {"type": "constant", "color": "#3f51b5"},
                   "labelColor": {"type": "constant", "color": "rgba(0,0,0,0.87)"},
                   "valueColor": {"type": "constant", "color": "rgba(0,0,0,0.87)"}}),
    # Sengaja dua chart, bukan satu chart dua sumbu: BPM (60-100) dan RR
    # (600-1000) di satu sumbu bikin garis BPM gepeng menempel di dasar, dan
    # yAxisId sumbu-kanan tidak menempel lewat REST (kedua sumbu tetap 0-1000).
    # Dua chart auto-scale sendiri, nol konfigurasi yang bisa salah.
    dict(fqn="time_series_chart", type="timeseries", title="Detak jantung (BPM)",
         keys=[("bpm", "BPM", "#e91e63")],
         col=0, row=4, sx=6, sy=6, units="bpm", decimals=1),
    dict(fqn="time_series_chart", type="timeseries", title="Interval R-R (ms)",
         keys=[("rr_interval_ms", "RR", "#009688")],
         col=6, row=4, sx=6, sy=6, units="ms", decimals=0),
    dict(fqn="cards.timeseries_table", type="timeseries", title="Riwayat rekaman",
         keys=[("bpm", "BPM", "#e91e63"), ("label_str", "Klasifikasi", "#f57c00"),
               ("confidence", "Confidence", "#3f51b5")],
         col=0, row=10, sx=12, sy=6, units="", decimals=2),
]


def widget_defaults(jwt):
    """Ambil defaultConfig tiap fqn sekali, cache per fqn."""
    page = rest("/api/widgetTypes?pageSize=1000&page=0", token=jwt)
    by_fqn = {w["fqn"]: w["id"]["id"] for w in page["data"]}
    cache = {}
    for w in WIDGETS:
        fqn = w["fqn"]
        if fqn in cache:
            continue
        wt = rest(f"/api/widgetType/{by_fqn[fqn]}", token=jwt)
        cache[fqn] = json.loads(wt["descriptor"]["defaultConfig"])
    return cache


def build(dev_id, defaults):
    alias_id = str(uuid.uuid4())
    widgets, layout = {}, {}

    for w in WIDGETS:
        wid = str(uuid.uuid4())
        fqn, wtype = w["fqn"], w["type"]
        cfg = json.loads(json.dumps(defaults[fqn]))     # salin, jangan bagi state
        cfg["title"] = w["title"]
        cfg["showTitle"] = w.get("show_title", True)
        cfg["units"] = w["units"]
        cfg["decimals"] = w["decimals"]
        for k, v in w.get("settings", {}).items():
            if isinstance(v, dict) and isinstance(cfg.get("settings", {}).get(k), dict):
                cfg["settings"][k].update(v)     # jangan buang yAxes "default"
            else:
                cfg.setdefault("settings", {})[k] = v
        cfg["datasources"] = [{
            "type": "entity",
            "name": None,
            "entityAliasId": alias_id,
            "filterId": None,
            "dataKeys": [{
                "name": name,
                "type": "timeseries",
                "label": label,
                "color": color,
                "units": w["units"],
                "decimals": w["decimals"],
                "settings": w.get("key_settings", {}).get(name, {}),
                "_hash": random.random(),
            } for name, label, color in w["keys"]],
        }]
        # widget latest tidak boleh ikut timewindow dashboard; timeseries harus ikut
        cfg["useDashboardTimewindow"] = (wtype == "timeseries")
        widgets[wid] = {
            # WAJIB di-prefix scope. "label_value_card" polos bikin UI 400 dan tiap
            # widget tampil "Problem loading widget configuration" -- dashboard
            # tersimpan rapi lewat REST tapi kosong total di layar.
            "typeFullFqn": "system." + fqn, "type": wtype,
            "sizeX": w["sx"], "sizeY": w["sy"], "config": cfg,
            "row": 0, "col": 0, "id": wid,
        }
        layout[wid] = {"sizeX": w["sx"], "sizeY": w["sy"], "row": w["row"], "col": w["col"]}

    return {
        "title": TITLE,
        "configuration": {
            "description": f"Dashboard PA -- telemetri {DEVICE}",
            "widgets": widgets,
            "states": {
                "default": {
                    "name": TITLE, "root": True,
                    "layouts": {"main": {
                        "widgets": layout,
                        "gridSettings": {"backgroundColor": "#eeeeee", "columns": 24,
                                         "margin": 10, "backgroundSizeMode": "100%"},
                    }},
                }
            },
            "entityAliases": {
                alias_id: {
                    "id": alias_id, "alias": "device",
                    "filter": {"type": "singleEntity", "resolveMultiple": False,
                               "singleEntity": {"entityType": "DEVICE", "id": dev_id}},
                }
            },
            "timewindow": {
                "displayValue": "", "selectedTab": 0, "hideInterval": False,
                "hideAggregation": False, "hideAggInterval": False,
                "realtime": {"interval": 1000, "timewindowMs": 600000},
                "aggregation": {"type": "NONE", "limit": 5000},
            },
            "settings": {"stateControllerId": "entity", "showTitle": False,
                         "showDashboardsSelect": True, "showEntitiesSelect": True,
                         "showDashboardTimewindow": True, "showDashboardExport": True,
                         "toolbarAlwaysOpen": True},
        },
    }


def main():
    jwt, dev_id, _ = provision()
    body = build(dev_id, widget_defaults(jwt))

    # Replace kalau sudah ada, supaya skrip idempoten.
    existing = rest(f"/api/tenant/dashboards?pageSize=100&page=0&textSearch={urllib.parse.quote(TITLE)}",
                    token=jwt)["data"]
    for d in existing:
        if d["title"] == TITLE:
            rest(f"/api/dashboard/{d['id']['id']}", token=jwt, method="DELETE")

    saved = rest("/api/dashboard", body, token=jwt)
    dash_id = saved["id"]["id"]

    full = rest(f"/api/dashboard/{dash_id}", token=jwt)
    for k in ("id", "createdTime", "tenantId"):
        full.pop(k, None)
    with open(OUT, "w") as f:
        json.dump(full, f, indent=2)

    assert len(full["configuration"]["widgets"]) == len(WIDGETS), "widget hilang saat disimpan"
    # REST menyimpan fqn apa pun tanpa protes; yang menolak cuma UI saat render.
    # Jadi resolusi tiap fqn diuji di sini, bukan dengan membuka browser.
    for w in full["configuration"]["widgets"].values():
        rest("/api/widgetType?fqn=" + urllib.parse.quote(w["typeFullFqn"]), token=jwt)
    print(f"dashboard {TITLE!r} -> http://localhost:8080/dashboards/{dash_id}")
    print(f"export    {OUT} ({len(WIDGETS)} widget)")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as e:
        sys.exit(f"REST {e.code}: {e.read().decode()[:400]}")
