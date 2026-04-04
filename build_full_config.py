import yaml
import re

# 加载测速后的 proxies.yaml（仅 proxies 列表）
with open('proxies.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

# ==================== 辅助函数：按关键词筛选节点 ====================
def filter_proxies(keyword_list):
    return [p['name'] for p in proxies if any(kw in p.get('name', '') for kw in keyword_list)]

# ==================== 构建超级强大配置 ====================
config = {
    'mixed-port': 7890,
    'allow-lan': True,
    'mode': 'rule',
    'log-level': 'info',
    'unified-delay': True,
    'tcp-concurrent': True,
    'ipv6': False,

    # ==================== DNS（更稳定更快） ====================
    'dns': {
        'enable': True,
        'ipv6': False,
        'use-system-hosts': False,
        'enhanced-mode': 'fake-ip',
        'fake-ip-range': '198.18.0.1/16',
        'nameserver': [
            'https://dns.alidns.com/dns-query',
            'https://doh.pub/dns-query',
            '8.8.8.8',
            '1.1.1.1'
        ],
        'fallback': ['8.8.8.8', '1.1.1.1'],
        'fallback-filter': {'geoip': True, 'ipcidr': ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']}
    },

    'proxies': proxies,

    # ==================== 超级详细策略组 ====================
    'proxy-groups': [
        # 自动选择（最低延迟）
        {'name': '自动选择', 'type': 'url-test', 'proxies': [p['name'] for p in proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50},
        
        # 低延迟优先（更激进）
        {'name': '低延迟', 'type': 'url-test', 'proxies': [p['name'] for p in proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180, 'tolerance': 30},
        
        # 负载均衡（多节点轮询）
        {'name': '负载均衡', 'type': 'load-balance', 'strategy': 'consistent-hashing', 'proxies': [p['name'] for p in proxies]},
        
        # 手动选择（全节点）
        {'name': '手动选择', 'type': 'select', 'proxies': [p['name'] for p in proxies]},
        
        # ==================== 区域精细分组（自动过滤） ====================
        {'name': '香港', 'type': 'select', 'proxies': filter_proxies(['香港', 'HK', 'Hong Kong']) or ['DIRECT']},
        {'name': '日本', 'type': 'select', 'proxies': filter_proxies(['日本', 'JP', 'Japan']) or ['DIRECT']},
        {'name': '美国', 'type': 'select', 'proxies': filter_proxies(['美国', 'US', 'USA', 'United States']) or ['DIRECT']},
        {'name': '新加坡', 'type': 'select', 'proxies': filter_proxies(['新加坡', 'SG', 'Singapore']) or ['DIRECT']},
        {'name': '台湾', 'type': 'select', 'proxies': filter_proxies(['台湾', 'TW', 'Taiwan']) or ['DIRECT']},
        {'name': '韩国', 'type': 'select', 'proxies': filter_proxies(['韩国', 'KR', 'Korea']) or ['DIRECT']},
        
        # ==================== 色情专用组 ====================
        {'name': '色情', 'type': 'select', 'proxies': ['自动选择', '低延迟', '手动选择']},
        
        # 主代理入口（推荐使用「自动选择」）
        {'name': 'PROXY', 'type': 'select', 'proxies': ['自动选择', '低延迟', '负载均衡', '手动选择', 'DIRECT']}
    ],

    # ==================== Loyalsoldier 全网最强规则集 + 色情专用 ====================
    'rule-providers': {
        'reject': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt', 'path': './ruleset/reject.yaml', 'interval': 86400},
        'private': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt', 'path': './ruleset/private.yaml', 'interval': 86400},
        'cncidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt', 'path': './ruleset/cncidr.yaml', 'interval': 86400},
        'lancidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt', 'path': './ruleset/lancidr.yaml', 'interval': 86400},
        'applications': {'type': 'http', 'behavior': 'classical', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt', 'path': './ruleset/applications.yaml', 'interval': 86400},
        'apple': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt', 'path': './ruleset/apple.yaml', 'interval': 86400},
        'icloud': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt', 'path': './ruleset/icloud.yaml', 'interval': 86400},
        'gfw': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/gfw.txt', 'path': './ruleset/gfw.yaml', 'interval': 86400},
        'proxy': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt', 'path': './ruleset/proxy.yaml', 'interval': 86400},
        'direct': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt', 'path': './ruleset/direct.yaml', 'interval': 86400},
        'tld-not-cn': {'type': 'http', 'behavior': 'domain', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/tld-not-cn.txt', 'path': './ruleset/tld-not-cn.yaml', 'interval': 86400},
        'telegramcidr': {'type': 'http', 'behavior': 'ipcidr', 'url': 'https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt', 'path': './ruleset/telegramcidr.yaml', 'interval': 86400},
        
        # 新增：色情专用规则集（包含所有主流porn + motv）
        'porn': {'type': 'http', 'behavior': 'domain', 'url': 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/NSFW/NSFW.txt', 'path': './ruleset/porn.yaml', 'interval': 86400},
    },

    'rules': [
        'RULE-SET,reject,REJECT',
        'RULE-SET,private,DIRECT',
        'RULE-SET,cncidr,DIRECT',
        'RULE-SET,lancidr,DIRECT',
        'RULE-SET,applications,DIRECT',
        'RULE-SET,apple,DIRECT',
        'RULE-SET,icloud,DIRECT',
        
        # 色情全部走代理（包含 motv）
        'RULE-SET,porn,色情',
        
        'RULE-SET,gfw,PROXY',
        'RULE-SET,proxy,PROXY',
        'RULE-SET,direct,DIRECT',
        'RULE-SET,tld-not-cn,PROXY',
        'GEOIP,CN,DIRECT',
        'MATCH,PROXY'
    ]
}

with open('proxies.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print(f"🎉 超级强大配置生成完成！节点数量: {len(proxies)} | 策略组: 自动选择+负载均衡+区域分组+色情专用 | 规则: Loyalsoldier + NSFW全覆盖")
