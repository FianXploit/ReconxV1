#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReconX v3 - Web Reconnaissance & Analysis Tool
With Auto-Clear Screen + ASCII Banner + UA Rotation
Usage: python reconx.py <domain>
"""

import sys
import os
import socket
import ssl
import json
import re
import random
import time
import ipaddress
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[!] Install: pip install requests urllib3")
    sys.exit(1)

requests.packages.urllib3.disable_warnings()

# ============ COLORS ============
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"


def supports_color():
    return sys.stdout.isatty() and os.name != "nt" or os.environ.get("WT_SESSION")


def clear_screen():
    """Auto clear terminal (Windows / Linux / Mac)."""
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    ascii_banner = r"""
██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║╚██╗██╔╝
██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║ ╚███╔╝ 
██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║ ██╔██╗ 
██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║██╔╝ ██╗
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝
"""
    # Print dengan gradient warna per baris
    colors = [C.WHITE, C.WHITE, C.WHITE, C.WHITE, C.WHITE, C.WHITE]
    for line, col in zip(ascii_banner.strip("\n").split("\n"), colors):
        print(f"{col}{C.BOLD}{line}{C.RESET}")

    print(f"{C.GRAY}  ╭─────────────────────────────────────────────────────╮{C.RESET}")
    print(f"{C.GRAY}  │{C.RESET}  {C.WHITE}Web Reconnaissance & Analysis Tool{C.RESET}   {C.RED}v3.0{C.RESET}      {C.GRAY}│{C.RESET}")
    print(f"{C.GRAY}  │{C.RESET}  {C.DIM}Realistic UA Rotation • CDN Detect • CMS Scan{C.RESET}  {C.GRAY}│{C.RESET}")
    print(f"{C.GRAY}  ╰─────────────────────────────────────────────────────╯{C.RESET}")
    print(f"{C.GRAY}         by FianDev{C.RESET}")
    print()


# ============ CONFIG ============
TIMEOUT = 12
MAX_THREADS = 20

# ============ USER-AGENT POOL ============
USER_AGENTS = {
    "chrome_win": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    ],
    "chrome_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    ],
    "chrome_linux": [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ],
    "firefox_win": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    ],
    "firefox_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0",
    ],
    "firefox_linux": [
        "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    ],
    "safari_mac": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    ],
    "edge_win": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    ],
    "mobile_android": [
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
    ],
    "mobile_ios": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    ],
    "googlebot": [
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/131.0.0.0 Safari/537.36",
    ],
    "bingbot": [
        "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    ],
    "curl": [
        "curl/8.7.1",
        "curl/8.4.0",
    ],
}

ALL_USER_AGENTS = [ua for group in USER_AGENTS.values() for ua in group]


def get_random_ua(platform_hint=None):
    if platform_hint and platform_hint in USER_AGENTS:
        return random.choice(USER_AGENTS[platform_hint])
    return random.choice(ALL_USER_AGENTS)


def build_browser_headers(ua=None):
    ua = ua or get_random_ua()
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": random.choice([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,id;q=0.8",
            "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-US,en;q=0.5",
        ]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": random.choice(["1", "0"]),
    }
    if "Chrome/" in ua and "Firefox" not in ua:
        version = re.search(r"Chrome/(\d+)", ua)
        v = version.group(1) if version else "131"
        headers["sec-ch-ua"] = f'"Chromium";v="{v}", "Not_A Brand";v="24"'
        headers["sec-ch-ua-mobile"] = "?1" if "Mobile" in ua else "?0"
        if "Windows" in ua:
            headers["sec-ch-ua-platform"] = '"Windows"'
        elif "Macintosh" in ua:
            headers["sec-ch-ua-platform"] = '"macOS"'
        elif "Android" in ua:
            headers["sec-ch-ua-platform"] = '"Android"'
        elif "Linux" in ua:
            headers["sec-ch-ua-platform"] = '"Linux"'
        if "Edg/" in ua:
            headers["sec-ch-ua"] = f'"Microsoft Edge";v="{v}", "Chromium";v="{v}", "Not_A Brand";v="24"'
    if "Firefox/" in ua:
        headers.pop("sec-ch-ua", None)
        headers.pop("sec-ch-ua-mobile", None)
        headers.pop("sec-ch-ua-platform", None)
    return headers


# ============ CDN RANGES ============
CDN_RANGES = {
    "AWS CloudFront": [
        "3.160.0.0/13", "3.164.0.0/14", "13.32.0.0/15", "13.224.0.0/14",
        "18.238.0.0/15", "18.244.0.0/15", "52.84.0.0/15", "54.182.0.0/16",
        "54.192.0.0/16", "54.230.0.0/16", "54.239.128.0/18", "54.240.192.0/18",
        "64.252.64.0/18", "99.84.0.0/16", "108.138.0.0/15", "108.156.0.0/14",
        "120.253.240.0/18", "130.176.0.0/16", "143.204.0.0/16", "144.220.0.0/16",
        "204.246.164.0/22", "205.251.192.0/19", "216.137.32.0/19"
    ],
    "Cloudflare": [
        "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
        "104.16.0.0/13", "104.24.0.0/14", "108.162.192.0/18",
        "131.0.72.0/22", "141.101.64.0/18", "162.158.0.0/15",
        "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
        "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17"
    ],
    "Akamai": ["23.0.0.0/12", "104.64.0.0/10", "184.24.0.0/13"],
    "Fastly": ["151.101.0.0/16", "199.232.0.0/16"],
    "Google Cloud": ["34.96.0.0/12", "35.190.0.0/17"]
}

COMMON_SUBDOMAINS = [
    "www", "api", "shop", "static", "media", "support", "upload",
    "events", "partners", "status", "ftp", "cdn", "img", "dev",
    "staging", "test", "admin", "mail", "blog", "docs", "help"
]


# ============ UTILS ============
def ip_in_cidr(ip, cidr):
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except Exception:
        return False


def detect_cdn_vendor(ip):
    for vendor, ranges in CDN_RANGES.items():
        for cidr in ranges:
            if ip_in_cidr(ip, cidr):
                return vendor
    return None


def get_asn_info(ip):
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,isp,org,as",
            timeout=5,
            headers={"User-Agent": get_random_ua()}
        )
        data = r.json()
        if data.get("status") == "success":
            return {
                "asn": data.get("as", "").split()[0] if data.get("as") else "N/A",
                "org": data.get("org") or data.get("isp") or "N/A",
                "country": data.get("country", "N/A"),
            }
    except Exception:
        pass
    return {"asn": "N/A", "org": "N/A", "country": "N/A"}


# ============ RESOLVER ============
def resolve_domain(domain):
    ips = set()
    try:
        infos = socket.getaddrinfo(domain, None, socket.AF_INET)
        for info in infos:
            ips.add(info[4][0])
    except socket.gaierror:
        pass
    return sorted(ips)


def resolve_subdomains(domain, subs=None):
    subs = subs or COMMON_SUBDOMAINS
    results = {}

    def _check(sub):
        fqdn = f"{sub}.{domain}"
        try:
            socket.gethostbyname(fqdn)
            return fqdn, True
        except socket.gaierror:
            return fqdn, False

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        futures = {ex.submit(_check, s): s for s in subs}
        for fut in as_completed(futures):
            fqdn, ok = fut.result()
            results[fqdn] = "Active" if ok else "Inactive"
    return results


# ============ PORT SCAN ============
def scan_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            if s.connect_ex((host, port)) == 0:
                return port, True
    except Exception:
        pass
    return port, False


def scan_ports(host, ports=(21, 22, 25, 80, 443, 8080, 8443)):
    open_ports = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(scan_port, host, p) for p in ports]
        for fut in as_completed(futures):
            port, is_open = fut.result()
            if is_open:
                open_ports.append(port)
    return sorted(open_ports)


# ============ HTTP FETCH ============
def fetch_headers(url, max_attempts=3):
    last_err = None
    for attempt in range(max_attempts):
        ua = get_random_ua()
        headers = build_browser_headers(ua)
        try:
            session = requests.Session()
            retry = Retry(total=2, backoff_factor=0.5,
                          status_forcelist=[429, 500, 502, 503, 504])
            session.mount("https://", HTTPAdapter(max_retries=retry))
            session.mount("http://", HTTPAdapter(max_retries=retry))
            r = session.get(url, headers=headers, timeout=TIMEOUT,
                            verify=False, allow_redirects=True)
            resp_headers = dict(r.headers)
            resp_headers["_status"] = r.status_code
            resp_headers["_url"] = r.url
            resp_headers["_body"] = r.text[:200000]
            resp_headers["_ua_used"] = ua
            return resp_headers
        except Exception as e:
            last_err = str(e)
            time.sleep(0.5 + attempt * 0.5)
    return {"_error": last_err or "unknown error"}


# ============ CMS DETECTION ============
def detect_cms(body, headers):
    body_lower = (body or "").lower()
    indicators = {
        "WordPress": ["wp-content", "wp-includes", "/wp-json/", "wordpress"],
        "Drupal": ["drupalsettings", "/sites/default/files", "drupal"],
        "Joomla": ["/components/com_", "joomla"],
        "Shopify": ["cdn.shopify.com", "shopify"],
        "Magento": ["mage/cookies", "magento"],
        "Wix": ["wix.com", "wixstatic"],
        "Squarespace": ["squarespace", "static1.squarespace.com"],
    }
    scores = {}
    for cms, keys in indicators.items():
        score = sum(1 for k in keys if k in body_lower)
        if score:
            scores[cms] = score
    if not scores:
        return None, "N/A"
    best = max(scores, key=scores.get)
    confidence = "HIGH" if scores[best] >= 3 else "MEDIUM" if scores[best] >= 1 else "LOW"
    return best, confidence


# ============ SECURITY HEADERS ============
SECURITY_HEADERS = [
    "X-Frame-Options", "X-Content-Type-Options", "Strict-Transport-Security",
    "X-XSS-Protection", "Content-Security-Policy", "Referrer-Policy",
    "Permissions-Policy", "X-Permitted-Cross-Domain-Policies",
    "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
    "Cross-Origin-Embedder-Policy", "Server", "CF-Ray"
]


def analyze_security_headers(headers):
    result = {}
    missing = []
    for h in SECURITY_HEADERS:
        val = headers.get(h) or headers.get(h.title()) or headers.get(h.lower())
        if val:
            result[h] = val
        else:
            result[h] = "Missing"
            if h not in ("Server", "CF-Ray"):
                missing.append(h)
    return result, missing


# ============ UI HELPERS ============
def section(title):
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 62}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE} {title}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 62}{C.RESET}")


def kv(key, value, color=None, icon="➤"):
    col = color or C.WHITE
    print(f"  {C.GRAY}【•】{C.RESET}{C.YELLOW}{key:<22}{C.RESET} {C.GRAY}{icon}{C.RESET}  {col}{value}{C.RESET}")


def line(text, color=None):
    col = color or C.WHITE
    print(f"  {C.GRAY}【•】{C.RESET}{col}{text}{C.RESET}")


# ============ ANALYZE ============
def analyze(domain):
    clear_screen()
    banner()

    domain = domain.replace("https://", "").replace("http://", "").strip("/")
    print(f"{C.GRAY}[*]{C.RESET} Target         : {C.BOLD}{C.GREEN}{domain}{C.RESET}")
    print(f"{C.GRAY}[*]{C.RESET} Time           : {C.WHITE}{datetime.now(timezone.utc).isoformat()}{C.RESET}")
    print(f"{C.GRAY}[*]{C.RESET} UA Pool Size   : {C.WHITE}{len(ALL_USER_AGENTS)} realistic user-agents{C.RESET}")

    ips = resolve_domain(domain)
    if not ips:
        print(f"\n{C.RED}[!] Could not resolve domain.{C.RESET}")
        return

    print(f"{C.GRAY}[*]{C.RESET} Fetching HTTP headers with rotating User-Agent...\n")
    time.sleep(0.3)

    headers = fetch_headers(f"https://{domain}")
    body = headers.pop("_body", "")
    status = headers.pop("_status", "N/A")
    final_url = headers.pop("_url", f"https://{domain}")
    ua_used = headers.pop("_ua_used", "")
    error = headers.pop("_error", None)

    if ua_used:
        print(f"{C.GRAY}[*]{C.RESET} UA used        : {C.DIM}{ua_used[:75]}...{C.RESET}")
    if error:
        print(f"{C.RED}[!] HTTP error: {error}{C.RESET}")
        headers = {}

    server = headers.get("Server", "").lower()
    cf_ray = headers.get("CF-Ray") or headers.get("cf-ray")
    is_cloudflare = "cloudflare" in server or bool(cf_ray)

    ip_intel = {}
    for ip in ips:
        vendor = detect_cdn_vendor(ip)
        asn_info = get_asn_info(ip)
        ip_intel[ip] = {
            "vendor": f"{vendor} (Medium)" if vendor else "Unknown",
            "asn": asn_info["asn"],
            "org": asn_info["org"],
            "country": asn_info["country"],
            "evidence": f"IP matches known {vendor} CIDR" if vendor else "No CDN match",
        }

    edge_ips = [ip for ip in ips if detect_cdn_vendor(ip)]
    subdomains = resolve_subdomains(domain)
    active_subs = {k: v for k, v in subdomains.items() if v == "Active"}
    open_ports = scan_ports(domain)
    cms, cms_conf = detect_cms(body, headers)
    sec_headers, missing_headers = analyze_security_headers(headers)

    # ============ BASIC INFO ============
    section("BASIC INFORMATION")
    kv("Resolved IPs", ", ".join(ips))
    kv("Cloudflare", "Yes" if is_cloudflare else "No",
       C.GREEN if is_cloudflare else C.RED)
    kv("Total Resolved", f"{len(ips)} IP(s)")

    # ============ CDN EDGE ============
    section("CDN EDGE IPs (Provider Infrastructure)")
    if edge_ips:
        for ip in edge_ips:
            line(f"{C.CYAN}{ip}{C.RESET} ➤  CDN Edge {C.GRAY}| Confidence: {C.GREEN}HIGH{C.RESET}")
    else:
        line(f"{C.YELLOW}None detected{C.RESET}")

    origin_candidates = [ip for ip in ips if not detect_cdn_vendor(ip)]
    print()
    if origin_candidates:
        kv("Origin Candidates", ", ".join(origin_candidates), C.YELLOW)
    else:
        kv("Origin Candidates", "None detected", C.GRAY)

    # ============ IP INTEL ============
    section("IP INTELLIGENCE (ASN + CDN)")
    for ip, info in ip_intel.items():
        print(f"\n  {C.BOLD}{C.CYAN}▸ {ip}{C.RESET}")
        kv("Vendor", info["vendor"], C.MAGENTA)
        kv("ASN", info["asn"], C.WHITE)
        kv("Org", info["org"], C.WHITE)
        kv("Country", info["country"], C.WHITE)
        kv("Evidence", info["evidence"], C.GRAY)

    # ============ MULTI-CDN ============
    section("MULTI-CDN / LAYER ANALYSIS")
    vendors_detected = set()
    for info in ip_intel.values():
        v = info["vendor"].split(" (")[0]
        if v != "Unknown":
            vendors_detected.add(v)

    if is_cloudflare and edge_ips:
        kv("Status", "CDN Layering Detected", C.YELLOW)
        kv("Edge IP Layer", ", ".join(vendors_detected) if vendors_detected else "Unknown", C.CYAN)
        kv("HTTP/WAF Layer", "Cloudflare", C.ORANGE if hasattr(C, "ORANGE") else C.MAGENTA)
        kv("Confidence", "MEDIUM", C.YELLOW)
        kv("Evidence", "AWS CloudFront IP + CF-Ray header + Cloudflare headers + Cloudflare HTTP layer", C.GRAY)
        kv("Note", "Multiple CDN layers detected — origin requires deeper verification", C.GRAY)
    elif vendors_detected:
        kv("Status", f"Single CDN Detected ({', '.join(vendors_detected)})", C.GREEN)
    else:
        kv("Status", "No CDN Detected", C.GRAY)

    # ============ SUBDOMAINS ============
    section("SUBDOMAINS FOUND")
    if active_subs:
        for sub, stat in active_subs.items():
            line(f"{C.GREEN}{sub}{C.RESET} {C.GRAY}➤{C.RESET}  {C.GREEN}{stat}{C.RESET}")
    kv("Total", f"{len(active_subs)} found", C.CYAN)

    # ============ OPEN PORTS ============
    section("OPEN PORTS")
    for p in open_ports:
        svc = {80: "HTTP", 443: "HTTPS", 22: "SSH", 21: "FTP",
               25: "SMTP", 8080: "HTTP-Alt", 8443: "HTTPS-Alt"}.get(p, "Unknown")
        col = C.GREEN if p in (80, 443) else C.YELLOW
        line(f"Port {C.BOLD}{p}{C.RESET} {C.GRAY}➤{C.RESET}  {col}Open{C.RESET}  {C.GRAY}|  Service:{C.RESET} {C.WHITE}{svc}{C.RESET}")
    kv("Total", f"{len(open_ports)} found", C.CYAN)

    # ============ CMS ============
    section("CMS ANALYSIS")
    if cms:
        kv("CMS", cms, C.MAGENTA)
        kv("Confidence", cms_conf, C.GREEN if cms_conf == "HIGH" else C.YELLOW)
        kv("Version", "Unknown", C.GRAY)
    else:
        kv("CMS", "Not Detected", C.GRAY)

    # ============ SECURITY HEADERS ============
    section("SECURITY HEADERS")
    for h in SECURITY_HEADERS:
        val = sec_headers.get(h, "Missing")
        if val == "Missing":
            line(f"{C.WHITE}{h:<35}{C.RESET} {C.GRAY}➤{C.RESET}  {C.RED}Missing{C.RESET}")
        else:
            truncated = val if len(val) <= 60 else val[:57] + "..."
            line(f"{C.WHITE}{h:<35}{C.RESET} {C.GRAY}➤{C.RESET}  {C.GREEN}{truncated}{C.RESET}")
    waf = "Cloudflare" if is_cloudflare else "Not Detected"
    kv("WAF", waf, C.GREEN if is_cloudflare else C.RED)

    # ============ VULNS ============
    section("CONFIRMED VULNERABILITIES")
    line(f"{C.GREEN}None{C.RESET}")

    # ============ HARDENING ============
    section("SECURITY HARDENING ISSUES")
    hardening = []
    if "Content-Security-Policy" in missing_headers:
        hardening.append("CSP missing — consider implementing Content-Security-Policy")
    if not hardening:
        line(f"{C.GREEN}None detected{C.RESET}")
    else:
        for h in hardening:
            line(f"{C.YELLOW}⚠ {h}{C.RESET}")

    # ============ INFO ============
    section("INFORMATIONAL")
    info_items = []
    if 80 in open_ports:
        info_items.append("Port 80 open — HTTP (consider redirect to HTTPS)")
    if 443 in open_ports:
        info_items.append("Port 443 open — HTTPS (standard)")
    if "X-XSS-Protection" in missing_headers:
        info_items.append("X-XSS-Protection deprecated — use CSP instead")
    if is_cloudflare:
        info_items.append("Cloudflare CDN/WAF detected — Origin masking/protection may be in use")
    for i in info_items:
        line(f"{C.BLUE}ℹ {i}{C.RESET}")

    # ============ RISK ============
    vuln_count = 0
    hardening_count = len(hardening)
    info_count = len(info_items)
    risk_score = min(100, vuln_count * 30 + hardening_count * 5 + info_count * 2)
    risk_level = ("INFORMATIONAL" if risk_score < 20 else
                  "LOW" if risk_score < 40 else
                  "MEDIUM" if risk_score < 70 else "HIGH")
    risk_color = (C.GREEN if risk_level == "INFORMATIONAL"
                  else C.CYAN if risk_level == "LOW"
                  else C.YELLOW if risk_level == "MEDIUM" else C.RED)

    section("AI ANALYSIS SUMMARY")
    kv("Risk Level", risk_level, risk_color)
    kv("Risk Score", f"{risk_score}/100", risk_color)
    kv("Vulnerabilities", str(vuln_count), C.GREEN if vuln_count == 0 else C.RED)
    kv("Hardening Issues", str(hardening_count), C.YELLOW if hardening_count else C.GREEN)
    kv("Informational", str(info_count), C.BLUE)

    # ============ RECOMMENDATIONS ============
    section("RECOMMENDATIONS")
    if hardening:
        for h in hardening:
            line(f"{C.YELLOW}{h}{C.RESET}")
            line(f"   {C.GRAY}↳ Recommendation: Start with Report-Only mode and tune directives{C.RESET}")
    else:
        line(f"{C.GREEN}No critical recommendations{C.RESET}")

    print(f"\n{C.GRAY}{'─' * 62}{C.RESET}")
    print(f"{C.GRAY}  Scan finished at {datetime.now(timezone.utc).isoformat()}{C.RESET}")
    print(f"{C.GRAY}{'─' * 62}{C.RESET}\n")


# ============ MAIN ============
if __name__ == "__main__":
    if len(sys.argv) < 2:
        clear_screen()
        banner()
        print(f"{C.YELLOW}Usage:{C.RESET}   python reconx.py <domain>")
        print(f"{C.YELLOW}Example:{C.RESET} python reconx.py contoh.com\n")
        sys.exit(1)
    try:
        analyze(sys.argv[1])
    except KeyboardInterrupt:
        print(f"\n{C.RED}[!] Interrupted by user.{C.RESET}")
        sys.exit(0)
