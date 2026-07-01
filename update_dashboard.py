#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 dashboard-data.json 生成政策通知看板 index.html。"""

import json
from pathlib import Path
import html


def build_html(data: dict) -> str:
    """根据数据构建完整的 HTML 页面。"""

    recent_items = data.get("recentItems", [])
    all_items = data.get("allItems", [])
    official_items = data.get("officialItems", [])
    chunyu_items = data.get("chunyuItems", [])
    monitored_sites = data.get("monitoredSites", [])

    total_count = len(all_items)
    recent_count = len(recent_items)
    official_count = len(official_items)
    province_count = len(chunyu_items)

    recent_html = build_recent_section(recent_items, data)
    all_html = build_timeline_section(all_items)
    official_html = build_timeline_section(official_items)
    chunyu_html = build_chunyu_section(chunyu_items)
    sites_html = build_sites_section(monitored_sites)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>政策通知看板 - smoon</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #f6f7fb;
      --card-bg: #ffffff;
      --text: #1f2937;
      --text-secondary: #6b7280;
      --primary: #2563eb;
      --primary-light: #eff6ff;
      --accent: #059669;
      --accent-light: #ecfdf5;
      --warning: #d97706;
      --warning-light: #fffbeb;
      --danger: #dc2626;
      --border: #e5e7eb;
      --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
      --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 0;
      margin: 0;
    }}
    header {{
      background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
      color: white;
      padding: 48px 24px 64px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    header::after {{
      content: "";
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 48px;
      background: var(--bg);
      border-radius: 48px 48px 0 0;
    }}
    header h1 {{
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 8px;
      letter-spacing: -0.5px;
    }}
    header p {{
      opacity: 0.9;
      font-size: 1rem;
      max-width: 600px;
      margin: 0 auto;
    }}
    .container {{
      max-width: 1100px;
      margin: -32px auto 48px;
      padding: 0 16px;
      position: relative;
      z-index: 1;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border-radius: 16px;
      padding: 20px;
      box-shadow: var(--shadow);
      text-align: center;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .stat-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
    }}
    .stat-card .number {{
      font-size: 2rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 4px;
    }}
    .stat-card .label {{
      font-size: 0.875rem;
      color: var(--text-secondary);
    }}
    .card {{
      background: var(--card-bg);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 24px;
      margin-bottom: 24px;
    }}
    .card h2 {{
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}
    .badge-blue {{ background: var(--primary-light); color: var(--primary); }}
    .badge-green {{ background: var(--accent-light); color: var(--accent); }}
    .badge-yellow {{ background: var(--warning-light); color: var(--warning); }}
    .empty-state {{
      background: #f9fafb;
      border: 1px dashed var(--border);
      border-radius: 12px;
      padding: 32px;
      text-align: center;
      color: var(--text-secondary);
    }}
    .timeline {{
      position: relative;
      padding-left: 24px;
    }}
    .timeline::before {{
      content: "";
      position: absolute;
      left: 8px;
      top: 8px;
      bottom: 8px;
      width: 2px;
      background: var(--border);
    }}
    .timeline-item {{
      position: relative;
      padding-bottom: 24px;
    }}
    .timeline-item:last-child {{ padding-bottom: 0; }}
    .timeline-item::before {{
      content: "";
      position: absolute;
      left: -20px;
      top: 6px;
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--primary);
      border: 2px solid var(--card-bg);
      box-shadow: 0 0 0 2px var(--primary-light);
    }}
    .timeline-item .date {{
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .timeline-item .title {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
      line-height: 1.5;
    }}
    .timeline-item .meta {{
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }}
    .timeline-item .summary {{
      font-size: 0.875rem;
      color: #4b5563;
      margin-bottom: 10px;
    }}
    .timeline-item .link {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.875rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
    }}
    .timeline-item .link:hover {{ text-decoration: underline; }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }}
    .tag {{
      background: #f3f4f6;
      color: #4b5563;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
    }}
    .province-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px;
    }}
    .province-card {{
      background: #f9fafb;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .province-card:hover {{
      transform: translateY(-2px);
      box-shadow: var(--shadow);
      background: white;
    }}
    .province-card .province-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .province-card .province-name {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text);
    }}
    .province-card .province-status {{
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--primary-light);
      color: var(--primary);
      font-weight: 500;
    }}
    .province-card .province-date {{
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 8px;
    }}
    .province-card .province-summary {{
      font-size: 0.875rem;
      color: #4b5563;
      margin-bottom: 10px;
      line-height: 1.5;
    }}
    .province-card .link {{
      font-size: 0.875rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
    }}
    .province-card .link:hover {{ text-decoration: underline; }}
    .footer {{
      text-align: center;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 0.875rem;
    }}
    .last-updated {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--primary-light);
      color: var(--primary);
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 16px;
    }}
    .section-intro {{
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    @media (max-width: 640px) {{
      header {{ padding: 32px 16px 48px; }}
      header h1 {{ font-size: 1.5rem; }}
      .container {{ margin-top: -24px; padding: 0 12px; }}
      .card {{ padding: 20px; }}
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      .province-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>政策通知看板</h1>
    <p>春雨行动 · 国家重点研发计划 · 国家科技重大专项</p>
  </header>

  <div class="container">
    <div class="last-updated">
      <span>🕐</span>
      <span>最后更新：{data.get('lastUpdated', '')}</span>
    </div>

    <div class="stats">
      <div class="stat-card">
        <div class="number">{recent_count}</div>
        <div class="label">过去12小时新消息</div>
      </div>
      <div class="stat-card">
        <div class="number">{total_count}</div>
        <div class="label">累积通知</div>
      </div>
      <div class="stat-card">
        <div class="number">{official_count}</div>
        <div class="label">精选汇总</div>
      </div>
      <div class="stat-card">
        <div class="number">{province_count}</div>
        <div class="label">春雨行动库</div>
      </div>
    </div>

    <div class="card">
      <h2>
        <span>⚡</span>
        <span>过去 12 小时新消息</span>
        <span class="badge badge-green">实时</span>
      </h2>
      <div class="section-intro">每日 8:00 / 20:00 自动检查，只展示过去 12 小时内发布的新通知。</div>
      {recent_html}
    </div>

    <div class="card">
      <h2>
        <span>📚</span>
        <span>累积通知</span>
        <span class="badge badge-blue">全部</span>
      </h2>
      <div class="section-intro">按发布时间倒序排列，收录与关键词相关的所有历史信息。</div>
      {all_html}
    </div>

    <div class="card">
      <h2>
        <span>🏛️</span>
        <span>精选汇总</span>
        <span class="badge badge-yellow">官网</span>
      </h2>
      <div class="section-intro">汇总国家或地方卫健委、工信部、科技部、药监局等官方网站发布的政策通知。</div>
      {official_html}
    </div>

    <div class="card">
      <h2>
        <span>🌧️</span>
        <span>春雨行动库</span>
        <span class="badge badge-green">省份</span>
      </h2>
      <div class="section-intro">收录已发布“春雨行动”实施方案或相关工作进展的省份。</div>
      {chunyu_html}
    </div>

    <div class="card">
      <h2>
        <span>🔭</span>
        <span>重点监控官网</span>
      </h2>
      {sites_html}
    </div>
  </div>

  <div class="footer">
    <p>由多多维护 · 每日 8:00 / 20:00 自动更新</p>
  </div>
</body>
</html>
"""


def build_recent_section(items: list, data: dict) -> str:
    """构建过去 12 小时新消息区域。"""
    if items:
        html = '<div class="timeline">'
        for item in items:
            html += build_timeline_item(item)
        html += '</div>'
        return html
    start = data.get("recentWindow", {}).get("start", "")
    end = data.get("recentWindow", {}).get("end", "")
    next_check = data.get("nextCheck", "")
    return f"""
    <div class="empty-state">
      <p>过去 12 小时内（{start} - {end}）未发现相关新政策通知。</p>
      <p style="font-size: 0.875rem; margin-top: 8px;">下次自动检查：{next_check}</p>
    </div>
    """


def build_timeline_section(items: list) -> str:
    """构建时间线区域。"""
    if not items:
        return '<div class="empty-state">暂无内容</div>'
    html = '<div class="timeline">'
    for item in items:
        html += build_timeline_item(item)
    html += '</div>'
    return html


def build_timeline_item(item: dict) -> str:
    """构建单个时间线条目。"""
    tags = ''.join(f'<span class="tag">{html.escape(tag)}</span>' for tag in item.get("tags", []))
    return f"""
    <div class="timeline-item">
      <div class="date">{html.escape(item.get('date', ''))}</div>
      <div class="title">{html.escape(item.get('title', ''))}</div>
      <div class="meta">来源：{html.escape(item.get('source', ''))}</div>
      <div class="summary">{html.escape(item.get('summary', ''))}</div>
      <a class="link" href="{html.escape(item.get('link', ''), quote=True)}" target="_blank" rel="noopener">查看原文 →</a>
      <div class="tags">{tags}</div>
    </div>
    """


def build_chunyu_section(items: list) -> str:
    """构建春雨行动省份卡片网格。"""
    if not items:
        return '<div class="empty-state">暂无省份入库</div>'
    cards = []
    for item in items:
        cards.append(f"""
        <div class="province-card">
          <div class="province-header">
            <span class="province-name">{html.escape(item.get('province', ''))}</span>
            <span class="province-status">{html.escape(item.get('status', ''))}</span>
          </div>
          <div class="province-date">{html.escape(item.get('date', ''))}</div>
          <div class="province-summary">{html.escape(item.get('summary', ''))}</div>
          <a class="link" href="{html.escape(item.get('link', ''), quote=True)}" target="_blank" rel="noopener">查看原文 →</a>
        </div>
        """)
    return '<div class="province-grid">' + ''.join(cards) + '</div>'


def build_sites_section(sites: list) -> str:
    """构建监控官网标签云。"""
    tags = ''.join(f'<span class="tag">{html.escape(site)}</span>' for site in sites)
    return f'<div class="tags">{tags}</div>'


def main():
    base_dir = Path(__file__).parent
    data_path = base_dir / "dashboard-data.json"
    output_path = base_dir / "index.html"

    data = json.loads(data_path.read_text(encoding="utf-8"))
    html_content = build_html(data)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"看板已生成：{output_path}")


if __name__ == "__main__":
    main()
