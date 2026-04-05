import yaml

with open('raw_proxies.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}
proxies = data.get('proxies', [])

print(f"原始节点数量: {len(proxies)}")

# 严格去重
seen = {}
deduped = []
for p in proxies:
    key = (p.get('name'), p.get('server'), p.get('port'))
    if key not in seen:
        seen[key] = True
        deduped.append(p)

print(f"基础去重后: {len(deduped)} 个节点")

# 防重名 + 限制最大节点数（防止测速太慢）
name_count = {}
final_proxies = []
MAX_NODES = 300   # ← 可自行修改
for p in deduped:
    if len(final_proxies) >= MAX_NODES:
        print(f"⚠️ 已达最大节点限制 {MAX_NODES}，停止添加")
        break
    original_name = p.get('name', '未知节点')
    if original_name in name_count:
        name_count[original_name] += 1
        new_name = f"{original_name} #{name_count[original_name]}"
        p['name'] = new_name
    else:
        name_count[original_name] = 1
    final_proxies.append(p)

with open('proxies_dedup.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'proxies': final_proxies}, f, allow_unicode=True, sort_keys=False)

print(f"✅ 最终去重 + 限流完成！共 {len(final_proxies)} 个节点 → proxies_dedup.yaml")
