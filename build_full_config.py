#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_full_config.py - 生成最终 clash.yaml（2026 优化版）
✅ 自动填充测速后的节点 | ✅ 智能策略组 | ✅ Loyalsoldier 规则集
✅ DNS 防泄露 | ✅ 兼容 Mihomo/Clash Meta
"""

import yaml
import os
from datetime import datetime

def load_proxies():
    """加载测速后的节点"""
    with open("proxies.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("proxies", [])

def build_proxy_groups(proxies):
    """构建智能策略组"""
    # 按地区分类节点
    regions = {
        "🇭🇰 香港节点": ["香港", "HK", "Hong Kong"],
        "🇯🇵 日本节点": ["日本", "JP", "Japan", "Tokyo"],
        "🇺🇸 美国节点": ["美国", "US", "United States"],
        "🇸🇬 新加坡节点": ["新加坡", "SG", "Singapore"],
        "🇹🇼 台湾节点": ["台湾", "TW", "Taiwan"],
        "🇰🇷 韩国节点": ["韩国", "KR", "Korea"],
        "🇬🇧 英国节点": ["英国", "GB", "United Kingdom"],
        "🇩🇪 德国节点": ["德国", "DE", "Germany"],
        "🇫🇷 法国节点": ["法国", "FR", "France"],
        "🇨🇦 加拿大节点": ["加拿大", "CA", "Canada"],
        "🇦🇺 澳洲节点": ["澳洲", "AU", "Australia"],
    }
    
    region_proxies = {name: [] for name in regions}
    other_proxies = []
    
    for p in proxies:
        name = p.get("name", "").lower()
        matched = False
        for region, keywords in regions.items():
            if any(kw.lower() in name for kw in keywords):
                region_proxies[region].append(p["name"])
                matched = True
                break
        if not matched:
            other_proxies.append(p["name"])
    
    groups = [
        {
            "name": "🚀 自动选择",
            "type": "url-test",
            "proxies": [p["name"] for p in proxies],
            "url": "https://cp.cloudflare.com/generate_204",
            "interval": 300,
            "tolerance": 50,
        },
        {
            "name": "⚡ 低延迟优选",
            "type": "url-test",
            "proxies": [p["name"] for p in proxies],
            "url": "https://cp.cloudflare.com/generate_204",
            "interval": 180,
            "tolerance": 30,
        },
        {
            "name": "⚖️ 负载均衡",
            "type": "load-balance",
            "strategy": "consistent-hashing",
            "proxies": [p["name"] for p in proxies],
        },
        {
            "name": "🔄 故障转移",
            "type": "fallback",
            "proxies": ["🚀 自动选择", "⚡ 低延迟优选", "⚖️ 负载均衡"],
        },
        {
            "name": "🎮 手动选择",
            "type": "select",
            "proxies": [p["name"] for p in proxies],
        },
    ]
    
    # 添加地区分组（只包含有节点的）
    for region, nodes in region_proxies.items():
        if nodes:
            groups.append({
                "name": region,
                "type": "select",
                "proxies": nodes,
            })
    
    # 添加其他节点到手动选择
    if other_proxies:
        groups[4]["proxies"].extend(other_proxies)
    
    # 特殊用途组
    groups.extend([
        {
            "name": "🔞 成人内容",
            "type": "select",
            "proxies": ["🚀 自动选择", "🎮 手动选择", "DIRECT"],
        },
        {
            "name": "🌐 全局代理",
            "type": "select",
            "proxies": ["🚀 自动选择", "⚡ 低延迟优选", "⚖️ 负载均衡", "🔄 故障转移", "🎮 手动选择", "DIRECT"],
        },
    ])
    
    return groups

def build_rules():
    """构建分流规则"""
    return [
        # 本地直连
        "DOMAIN-SUFFIX,local,DIRECT",
        "IP-CIDR,127.0.0.0/8,DIRECT",
        "IP-CIDR,192.168.0.0/16,DIRECT",
        "IP-CIDR,10.0.0.0/8,DIRECT",
        "IP-CIDR,172.16.0.0/12,DIRECT",
        
        # 广告拦截
        "RULE-SET,reject,REJECT",
        
        # 国内直连
        "RULE-SET,private,DIRECT",
        "RULE-SET,cncidr,DIRECT",
        "RULE-SET,lancidr,DIRECT",
        "RULE-SET,direct,DIRECT",
        "RULE-SET,apple,DIRECT",
        "RULE-SET,icloud,DIRECT",
        
        # 特殊内容
        "RULE-SET,porn,🔞 成人内容",
        
        # 代理规则
        "RULE-SET,gfw,🌐 全局代理",
        "RULE-SET,proxy,🌐 全局代理",
        "RULE-SET,tld-not-cn,🌐 全局代理",
        "RULE-SET,telegramcidr,🌐 全局代理",
        
        # GEOIP
        "GEOIP,CN,DIRECT",
        
        # 默认
        "MATCH,🌐 全局代理",
    ]

def main():
    proxies = load_proxies()
    print(f"[INFO] 加载 {len(proxies)} 个测速后节点")
    
    config = {
        # 基础设置
        "mixed-port": 7890,
        "allow-lan": False,
        "bind-address": "*",
        "mode": "rule",
        "log-level": "info",
        "ipv6": False,
        "unified-delay": True,
        "tcp-concurrent": True,
        "external-controller": "127.0.0.1:9090",
        "secret": "",
        
        # DNS 防泄露
        "dns": {
            "enable": True,
            "listen": "0.0.0.0:1053",
            "enhanced-mode": "fake-ip",
            "fake-ip-range": "198.18.0.1/16",
            "fake-ip-filter": [
                "*.lan", "*.local", "localhost.ptlogin2.qq.com",
                "time.*.com", "ntp.*.org",
            ],
            "default-nameserver": ["223.5.5.5", "119.29.29.29"],
            "nameserver": [
                "https://dns.alidns.com/dns-query",
                "https://doh.pub/dns-query",
            ],
            "fallback": [
                "https://dns.google/dns-query",
                "https://1.1.1.1/dns-query",
                "https://dns.cloudflare.com/dns-query",
            ],
            "fallback-filter": {
                "geoip": True,
                "geoip-code": "CN",
                "ipcidr": [
                    "240.0.0.0/4", "0.0.0.0/8", "10.0.0.0/8",
                    "172.16.0.0/12", "192.168.0.0/16",
                ],
                "domain": ["+.google.com", "+.facebook.com", "+.twitter.com"],
            },
        },
        
        # 代理组
        "proxy-groups": build_proxy_groups(proxies),
        
        # 规则提供者（自动更新）
        "rule-providers": {
            "reject": {
                "type": "http", "behavior": "domain",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt",
                "path": "./rules/reject.yaml", "interval": 86400,
            },
            "private": {
                "type": "http", "behavior": "domain",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt",
                "path": "./rules/private.yaml", "interval": 86400,
            },
            "cncidr": {
                "type": "http", "behavior": "ipcidr",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt",
                "path": "./rules/cncidr.yaml", "interval": 86400,
            },
            "lancidr": {
                "type": "http", "behavior": "ipcidr",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt",
                "path": "./rules/lancidr.yaml", "interval": 86400,
            },
            "gfw": {
                "type": "http", "behavior": "domain",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/gfw.txt",
                "path": "./rules/gfw.yaml", "interval": 86400,
            },
            "proxy": {
                "type": "http", "behavior": "domain",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt",
                "path": "./rules/proxy.yaml", "interval": 86400,
            },
            "direct": {
                "type": "http", "behavior": "domain",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt",
                "path": "./rules/direct.yaml", "interval": 86400,
            },
            "telegramcidr": {
                "type": "http", "behavior": "ipcidr",
                "url": "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt",
                "path": "./rules/telegramcidr.yaml", "interval": 86400,
            },
            "porn": {
                "type": "http", "behavior": "domain",
                "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/NSFW/NSFW.txt",
                "path": "./rules/porn.yaml", "interval": 86400,
            },
        },
        
        # 分流规则
        "rules": build_rules(),
    }
    
    # 添加元信息
    config["#"] = f"Generated by 2026Clash @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    config["#-total_proxies"] = len(proxies)
    
    # 输出
    with open("clash.yaml", "w", encoding="utf-8") as f:
        # 先写注释
        f.write(f"# 2026Clash 自动配置 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 节点总数: {len(proxies)}\n")
        f.write("# 内核兼容: Mihomo / Clash Meta / Clash Verge Rev\n")
        f.write("# 使用说明: 导入此文件到客户端，或放在内核同级目录运行\n\n")
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    print(f"[✅] 生成完成！clash.yaml 包含 {len(proxies)} 个节点")

if __name__ == "__main__":
    main()
