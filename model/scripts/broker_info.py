import json
import shutil
import socket
import subprocess

IGNORED_INTERFACE_PREFIXES = ("lo", "docker", "br-", "veth", "virbr")
PORT = {1883: "MQTT ThingsBoard", 8080: "UI/REST ThingsBoard"}


def jalankan(cmd, batas=3):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=batas).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def ipv4_lan():
    data = json.loads(jalankan(["ip", "-j", "-4", "addr", "show"]) or "[]")
    return [(i["ifname"], a["local"]) for i in data
            if not i["ifname"].startswith(IGNORED_INTERFACE_PREFIXES)
            for a in i.get("addr_info", []) if a.get("family") == "inet"]


def ssid_aktif():
    if shutil.which("nmcli"):
        for baris in jalankan(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]).splitlines():
            active, _, ssid = baris.partition(":")
            if active in ("yes", "ya") and ssid:
                return ssid.replace("\\:", ":")
    if shutil.which("iwgetid"):
        return jalankan(["iwgetid", "-r"]).strip()
    return ""


def port_is_open(port):
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    lan = ipv4_lan()
    ssid = ssid_aktif()

    print(f"Hostname : {socket.gethostname()}")
    if ssid:
        print(f"SSID     : {ssid}  -> the board must connect to the same SSID")
    else:
        print("SSID     : not detected (laptop is wired, or nmcli/iwgetid is missing);"
              " the board must connect to the same network as the laptop")

    print("IPv4 LAN :", end="")
    print("".join(f"\n  {nama:<12} {ip}" for nama, ip in lan) or " none (laptop is not connected to a network)")

    print("Port localhost:")
    for p, port_service in PORT.items():
        print(f"  {p:<5} {'open' if port_is_open(p) else 'CLOSED'}  ({port_service})")
    if not port_is_open(1883):
        print("  -> run: cd dashboard && docker compose up -d")

    print("\nSuggested entries (firmware/include/wifi_secrets.h):")
    print("  WIFI_DAFTAR:")
    print(f'    {{"{ssid or "<ssid>"}", "<password>"}},')
    print("  BROKER_DAFTAR:")
    for nama, ip in lan or [("-", "<IP>")]:
        print(f'    {{"laptop", "{ip}", 1883, "<token>"}},   // {nama}, valid while this IP stays')
    print("Token: cd dashboard && python3 smoke_test.py")
    print("Laptop IP changed (DHCP)? Run this again, update the entries, reflash.")


if __name__ == "__main__":
    main()
