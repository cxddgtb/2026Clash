import yaml
from collections import Counter
import re
from datetime import datetime

with open('proxies.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

total = len(proxies)
types = Counter(p.get('type', 'unknown') for p in proxies)

# 提取国旗统计
country = Counter()
for p in proxies:
    name = p.get('name', '')
    match = re.search(r'([🇦-🇿]{2})', name)
    if match:
        country[match.group(1)] += 1

with open('nodes_stats.md', 'w', encoding='utf-8') as f:
    f.write(f"# 🚀 节点统计报告\n\n")
    f.write(f"**更新时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)\n\n")
    f.write(f"**总节点**：{total}\n")
    f.write(f"**类型分布**：\n")
    for t, cnt in types.most_common():
        f.write(f"- {t}: {cnt}\n")
    f.write(f"\n**国家/地区分布**（前10）:\n")
    for flag, cnt in country.most_common(10):
        f.write(f"- {flag}: {cnt}\n")
    f.write(f"\n**原始去重节点**：详见 `proxies_dedup.yaml`\n")
    print("✅ nodes_stats.md 生成完成")
