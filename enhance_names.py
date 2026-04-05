import yaml
import re

with open('proxies.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])

for p in proxies:
    if not isinstance(p, dict):
        continue
    old_name = p.get('name', '')
    latency = p.get('latency') or p.get('ping') or 0
    latency_str = f" | ⚡ {int(latency)}ms" if isinstance(latency, (int, float)) and latency > 0 else ""
    new_name = re.sub(r'\s*\|\s*\|', ' |', old_name + latency_str).strip()
    p['name'] = new_name

data['proxies'] = proxies

with open('proxies.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print(f"✅ 节点名称增强完成（加入延迟显示），共 {len(proxies)} 个节点")
