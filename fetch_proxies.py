#!/usr/bin/env python3
import os
import sys
import yaml
import base64
import json
import requests
from urllib.parse import urlparse

def decode_base64(content: str) -> str | None:
    s = content.strip()
    try:
        missing = len(s) % 4
        if missing:
            s += "=" * (4 - missing)
        decoded = base64.b64decode(s, validate=False)
        return decoded.decode("utf-8")
    except Exception:
        return None

def fetch_single_subscription(url: str, index: int) -> list:
    print(f"📥 下载第 {index+1} 个订阅: {url[:70]}...")
    
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        content = resp.text
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return []

    # 1. 直接尝试 YAML
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict) and isinstance(data.get("proxies"), list):
            proxies = data["proxies"]
            print(f"  ✓ Clash YAML 格式，获取 {len(proxies)} 个节点")
            return proxies
        elif isinstance(data, list):
            print(f"  ✓ 纯 proxies 列表格式，获取 {len(data)} 个节点")
            return data
    except Exception:
        pass

    # 2. Base64 解码后再尝试
    decoded = decode_base64(content)
    if decoded:
        try:
            data = yaml.safe_load(decoded)
            if isinstance(data, dict) and isinstance(data.get("proxies"), list):
                proxies = data["proxies"]
                print(f"  ✓ Base64 编码的 Clash YAML，获取 {len(proxies)} 个节点")
                return proxies
            elif isinstance(data, list):
                print(f"  ✓ Base64 编码的 proxies 列表，获取 {len(data)} 个节点")
                return data
        except Exception:
            pass

    print("  ⚠️ 未知订阅格式，已跳过")
    return []

if __name__ == "__main__":
    proxies_urls = os.getenv("PROXIES_URLS", "")
    if not proxies_urls.strip():
        print("❌ 未设置 PROXIES_URLS Secret")
        sys.exit(1)

    urls = [line.strip() for line in proxies_urls.splitlines() if line.strip()]
    all_proxies = []
    
    for i, url in enumerate(urls):
        proxies = fetch_single_subscription(url, i)
        all_proxies.extend(proxies)

    if not all_proxies:
        print("❌ 所有订阅均无有效节点！")
        sys.exit(1)

    # 写入 raw_proxies.yaml
    with open("raw_proxies.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"proxies": all_proxies}, f, allow_unicode=True, sort_keys=False)

    print(f"🎉 多订阅全格式合并完成！共 {len(all_proxies)} 个原始节点 → raw_proxies.yaml")
