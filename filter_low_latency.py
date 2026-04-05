import yaml
import os
import time

start = time.time()

if os.path.exists('proxies_tested.yaml'):
    with open('proxies_tested.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
else:
    print("⚠️ proxies_tested.yaml 不存在，使用 proxies_dedup.yaml")
    with open('proxies_dedup.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

proxies = data.get('proxies', [])

MAX_LATENCY_MS = 5000
filtered = [p for p in proxies if isinstance(p.get('latency'), (int, float)) and p.get('latency') <= MAX_LATENCY_MS]

print(f"第一阶段 fast 测速完成 → 低延迟节点 (<{MAX_LATENCY_MS}ms): {len(filtered)} / {len(proxies)}")

if len(filtered) == 0:
    print("⚠️ 没有 <5000ms 节点，使用第一阶段全部节点作为 fallback")
    filtered = proxies

with open('low_latency.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': filtered}, f, allow_unicode=True, sort_keys=False)

print(f"✅ low_latency.yaml 生成完成（{len(filtered)} 个节点）")
print(f"过滤耗时: {time.time() - start:.1f} 秒")
