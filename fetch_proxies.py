#!/usr/bin/env python3
import os
import sys
import yaml
import base64
import json
import requests
from urllib.parse import urlparse, unquote, parse_qs

def decode_base64(s: str) -> str | None:
    s = s.strip()
    try:
        missing = len(s) % 4
        if missing:
            s += "=" * (4 - missing)
        decoded = base64.b64decode(s, validate=False)
        return decoded.decode("utf-8")
    except Exception:
        return None

def parse_proxy_line(line: str) -> dict | None:
    """解析单行代理链接 → Clash 格式（全协议支持版）"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # ss://
    if line.startswith('ss://'):
        try:
            if '#' in line:
                url_part, name = line.split('#', 1)
                name = unquote(name)
            else:
                url_part, name = line, "SS"
            b64 = url_part[5:]
            decoded = base64.urlsafe_b64decode(b64 + '===').decode('utf-8')
            method, rest = decoded.split(':', 1)
            password, server_port = rest.split('@')
            server, port = server_port.rsplit(':', 1)
            return {
                'name': name or f"SS-{server}",
                'type': 'ss',
                'server': server,
                'port': int(port),
                'cipher': method,
                'password': password
            }
        except:
            return None

    # vmess://
    if line.startswith('vmess://'):
        try:
            b64 = line[8:]
            decoded = base64.urlsafe_b64decode(b64 + '===').decode('utf-8')
            data = json.loads(decoded)
            return {
                'name': data.get('ps') or data.get('name') or "VMess",
                'type': 'vmess',
                'server': data.get('add'),
                'port': int(data.get('port')),
                'uuid': data.get('id'),
                'alterId': int(data.get('aid', 0)),
                'cipher': 'auto',
                'udp': True
            }
        except:
            return None

    # trojan://
    if line.startswith('trojan://'):
        try:
            if '#' in line:
                url_part, name = line.split('#', 1)
                name = unquote(name)
            else:
                url_part, name = line, "Trojan"
            parsed = urlparse(url_part)
            password = parsed.username or parsed.path.strip('/')
            server = parsed.hostname
            port = parsed.port or 443
            return {
                'name': name or f"Trojan-{server}",
                'type': 'trojan',
                'server': server,
                'port': int(port),
                'password': password
            }
        except:
            return None

    # vless://
    if line.startswith('vless://'):
        try:
            if '#' in line:
                url_part, name = line.split('#', 1)
                name = unquote(name)
            else:
                url_part, name = line, "VLESS"
            parsed = urlparse(url_part)
            uuid = parsed.username or parsed.path.strip('/')
            server = parsed.hostname
            port = parsed.port or 443
            return {
                'name': name or f"VLESS-{server}",
                'type': 'vless',
                'server': server,
                'port': int(port),
                'uuid': uuid,
                'tls': True,
                'skip-cert-verify': True,
                'network': 'tcp'
            }
        except:
            return None

    # hysteria2:// 和 hy2://
    if line.startswith(('hysteria2://', 'hy2://')):
        try:
            if '#' in line:
                url_part, name_part = line.split('#', 1)
                name = unquote(name_part)
            else:
                url_part, name = line, "HY2"
            auth_part = url_part.split('://', 1)[1]
            if '@' in auth_part:
                password, server_port = auth_part.split('@', 1)
            else:
                password = ''
                server_port = auth_part
            if ':' in server_port:
                server, port_str = server_port.split(':', 1)
                port = int(port_str.split('?')[0])
            else:
                server = server_port.split('?')[0]
                port = 443
            return {
                'name': name or f"HY2-{server}",
                'type': 'hysteria2',
                'server': server,
                'port': port,
                'password': password,
                'tls': True,
                'skip-cert-verify': True
            }
        except Exception:
            return None

    # tuic:// (Tuic v5)
    if line.startswith('tuic://'):
        try:
            if '#' in line:
                url_part, name_part = line.split('#', 1)
                name = unquote(name_part)
            else:
                url_part, name = line, "TUIC"
            parsed = urlparse(url_part)
            uuid = parsed.username or parsed.path.strip('/')
            server = parsed.hostname
            port = parsed.port or 443
            return {
                'name': name or f"TUIC-{server}",
                'type': 'tuic',
                'server': server,
                'port': int(port),
                'uuid': uuid,
                'password': parsed.password or '',
                'tls': True,
                'skip-cert-verify': True
            }
        except:
            return None

    # ssr:// (ShadowsocksR)
    if line.startswith('ssr://'):
        try:
            b64 = line[6:]
            decoded = decode_base64(b64)
            if not decoded:
                return None
            # ssr 格式较复杂，这里做基础解析
            parts = decoded.split(':')
            if len(parts) < 6:
                return None
            server = parts[0]
            port = int(parts[1])
            protocol = parts[2]
            method = parts[3]
            obfs = parts[4]
            password = base64.urlsafe_b64decode(parts[5].split('/')[0] + '===').decode('utf-8')
            name = "SSR" if len(parts) > 6 else "SSR"
            return {
                'name': name,
                'type': 'ssr',
                'server': server,
                'port': port,
                'cipher': method,
                'password': password
            }
        except:
            return None

    return None

def fetch_single_subscription(url: str, index: int) -> list:
    print(f"下载第 {index+1} 个订阅: {url[:70]}...")
    try:
        resp = requests.get(url, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        content = resp.text
    except Exception as e:
        print(f"下载失败: {e}")
        return []

    proxies = []

    # 1. 直接尝试 YAML / 纯 proxies 列表（已支持任意协议）
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict) and isinstance(data.get("proxies"), list):
            proxies = data["proxies"]
            print(f"  Clash YAML 格式，获取 {len(proxies)} 个节点（含全协议）")
            return proxies
        elif isinstance(data, list):
            print(f"  纯 proxies 列表格式，获取 {len(data)} 个节点")
            return data
    except:
        pass

    # 2. Base64 解码后尝试
    decoded = decode_base64(content)
    content_to_parse = decoded if decoded else content

    # 3. 尝试作为代理链接列表（每行各种协议）
    lines = [l.strip() for l in content_to_parse.splitlines() if l.strip() and not l.startswith('#')]
    for line in lines:
        proxy = parse_proxy_line(line)
        if proxy:
            proxies.append(proxy)

    if proxies:
        print(f"  Base64/纯文本 代理链接列表，获取 {len(proxies)} 个节点")
        return proxies

    print("  未知订阅格式，已跳过")
    return []

if __name__ == "__main__":
    proxies_urls = os.getenv("PROXIES_URLS", "")
    if not proxies_urls.strip():
        print("未设置 PROXIES_URLS Secret")
        sys.exit(1)

    urls = [line.strip() for line in proxies_urls.splitlines() if line.strip()]
    all_proxies = []

    for i, url in enumerate(urls):
        proxies = fetch_single_subscription(url, i)
        all_proxies.extend(proxies)

    if not all_proxies:
        print("所有订阅均无有效节点！")
        sys.exit(1)

    with open("raw_proxies.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"proxies": all_proxies}, f, allow_unicode=True, sort_keys=False)

    print(f"多订阅全协议合并完成！共 {len(all_proxies)} 个原始节点 → raw_proxies.yaml")
