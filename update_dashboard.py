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

    recent_html = build_timeline_section(recent_items)
    all_html = build_timeline_section(all_items)
    official_html = build_timeline_section(official_items)
    chunyu_html = build_chunyu_section(chunyu_items)
    sites_html = build_sites_section(monitored_sites)

    # 预计算模板变量
    rw = data.get("recentWindow", {})
    rw_start = rw.get("start", "")
    rw_end = rw.get("end", "")
    next_check = data.get("nextCheck", "")

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
      --primary-dark: #1d4ed8;
      --accent: #059669;
      --accent-light: #ecfdf5;
      --warning: #d97706;
      --warning-light: #fffbeb;
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
    }}
    header {{
      background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
      color: white;
      padding: 40px 24px 56px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    header::after {{
      content: "";
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 40px;
      background: var(--bg);
      border-radius: 40px 40px 0 0;
    }}
    header h1 {{
      font-size: 2rem;
      font-weight: 700;
      margin-bottom: 6px;
      letter-spacing: -0.5px;
    }}
    header p {{
      opacity: 0.85;
      font-size: 0.95rem;
    }}

    .container {{
      max-width: 1100px;
      margin: -28px auto 40px;
      padding: 0 16px;
      position: relative;
      z-index: 1;
    }}

    /* ── 更新时间 ── */
    .last-updated {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--primary-light);
      color: var(--primary);
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 500;
      margin-bottom: 20px;
    }}

    /* ── 顶部四个卡片标签 ── */
    .tab-bar {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 20px;
    }}
    .tab-card {{
      background: var(--card-bg);
      border: 2px solid var(--border);
      border-radius: 16px;
      padding: 20px 16px 18px;
      text-align: center;
      cursor: pointer;
      transition: all 0.25s ease;
      user-select: none;
      box-shadow: var(--shadow);
      position: relative;
    }}
    .tab-card:hover {{
      transform: translateY(-3px);
      box-shadow: var(--shadow-lg);
      border-color: #93c5fd;
    }}
    .tab-card.active {{
      border-color: var(--primary);
      background: var(--primary-light);
      box-shadow: 0 0 0 3px rgba(37,99,235,0.18), var(--shadow-lg);
      transform: translateY(-3px);
    }}
    .tab-card .tab-icon {{
      font-size: 1.6rem;
      margin-bottom: 4px;
    }}
    .tab-card .tab-number {{
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--text);
      line-height: 1.2;
    }}
    .tab-card.active .tab-number {{
      color: var(--primary);
    }}
    .tab-card .tab-label {{
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-top: 2px;
      font-weight: 400;
    }}
    .tab-card .tab-arrow {{
      display: none;
      font-size: 0.7rem;
      opacity: 0.5;
      margin-top: 4px;
    }}
    .tab-card.active .tab-arrow {{
      display: block;
      color: var(--primary);
    }}

    /* ── 内容面板 ── */
    .panel {{
      display: none;
      background: var(--card-bg);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 28px 24px;
      animation: fadeSlideIn 0.35s ease;
    }}
    .panel.active {{
      display: block;
    }}
    @keyframes fadeSlideIn {{
      from {{ opacity: 0; transform: translateY(8px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .panel h2 {{
      font-size: 1.3rem;
      font-weight: 700;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .panel .panel-meta {{
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}

    /* ── 徽章 ── */
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 3px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 500;
    }}
    .badge-blue {{ background: var(--primary-light); color: var(--primary); }}
    .badge-green {{ background: var(--accent-light); color: var(--accent); }}
    .badge-yellow {{ background: var(--warning-light); color: var(--warning); }}

    /* ── 空状态 ── */
    .empty-state {{
      background: #f9fafb;
      border: 1px dashed var(--border);
      border-radius: 12px;
      padding: 40px 20px;
      text-align: center;
      color: var(--text-secondary);
    }}
    .empty-state .empty-icon {{
      font-size: 2.5rem;
      margin-bottom: 10px;
    }}

    /* ── 时间线 ── */
    .timeline {{
      position: relative;
      padding-left: 28px;
    }}
    .timeline::before {{
      content: "";
      position: absolute;
      left: 10px; top: 8px; bottom: 8px;
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
      left: -22px; top: 6px;
      width: 10px; height: 10px;
      border-radius: 50%;
      background: var(--primary);
      border: 2px solid var(--card-bg);
      box-shadow: 0 0 0 2px var(--primary-light);
    }}
    .timeline-item .date {{
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-bottom: 2px;
    }}
    .timeline-item .title {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
      line-height: 1.5;
    }}
    .timeline-item .meta {{
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }}
    .timeline-item .summary {{
      font-size: 0.875rem;
      color: #4b5563;
      margin-bottom: 8px;
    }}
    .timeline-item .link {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-size: 0.875rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
      transition: color 0.15s;
    }}
    .timeline-item .link:hover {{ color: var(--primary-dark); text-decoration: underline; }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }}
    .tag {{
      background: #f3f4f6;
      color: #4b5563;
      padding: 3px 9px;
      border-radius: 999px;
      font-size: 0.75rem;
    }}

    /* ── 春雨行动省份网格 ── */
    .province-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
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
      margin-bottom: 6px;
    }}
    .province-card .province-name {{
      font-size: 1.05rem;
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
      font-size: 0.85rem;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }}
    .province-card .province-summary {{
      font-size: 0.85rem;
      color: #4b5563;
      margin-bottom: 8px;
      line-height: 1.5;
    }}
    .province-card .link {{
      font-size: 0.85rem;
      color: var(--primary);
      text-decoration: none;
      font-weight: 500;
    }}
    .province-card .link:hover {{ text-decoration: underline; }}

    /* ── 监控站点区域 ── */
    .sites-card {{
      background: var(--card-bg);
      border-radius: 16px;
      box-shadow: var(--shadow);
      padding: 20px 24px;
      margin-top: 16px;
    }}
    .sites-card h3 {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 10px;
    }}

    /* ── 页脚 ── */
    .footer {{
      text-align: center;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 0.85rem;
    }}

    /* ── 响应式 ── */
    @media (max-width: 640px) {{
      header {{ padding: 28px 16px 44px; }}
      header h1 {{ font-size: 1.4rem; }}
      .container {{ margin-top: -22px; padding: 0 12px; }}
      .tab-bar {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
      .tab-card {{ padding: 14px 10px 12px; }}
      .tab-card .tab-number {{ font-size: 1.4rem; }}
      .tab-card .tab-label {{ font-size: 0.78rem; }}
      .panel {{ padding: 20px 16px; }}
      .province-grid {{ grid-template-columns: 1fr; }}
      .timeline {{ padding-left: 22px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>📋 政策通知看板</h1>
    <p>春雨行动 · 国家重点研发计划 · 国家科技重大专项</p>
  </header>

  <div class="container">
    <div class="last-updated">
      <span>🕐</span>
      <span>最后更新：{data.get('lastUpdated', '')}</span>
    </div>

    <!-- 四个可点击卡片 -->
    <div class="tab-bar">
      <div class="tab-card active" data-tab="recent" onclick="switchTab('recent')">
        <div class="tab-icon">⚡</div>
        <div class="tab-number">{recent_count}</div>
        <div class="tab-label">过去12小时新消息</div>
        <div class="tab-arrow">▼</div>
      </div>
      <div class="tab-card" data-tab="all" onclick="switchTab('all')">
        <div class="tab-icon">📚</div>
        <div class="tab-number">{total_count}</div>
        <div class="tab-label">累积通知</div>
        <div class="tab-arrow">▼</div>
      </div>
      <div class="tab-card" data-tab="official" onclick="switchTab('official')">
        <div class="tab-icon">🏛️</div>
        <div class="tab-number">{official_count}</div>
        <div class="tab-label">精选汇总</div>
        <div class="tab-arrow">▼</div>
      </div>
      <div class="tab-card" data-tab="chunyu" onclick="switchTab('chunyu')">
        <div class="tab-icon">🌧️</div>
        <div class="tab-number">{province_count}</div>
        <div class="tab-label">春雨行动库</div>
        <div class="tab-arrow">▼</div>
      </div>
    </div>

    <!-- 面板 1：过去12小时新消息 -->
    <div id="panel-recent" class="panel active">
      <h2>
        <span>⚡</span>
        <span>过去 12 小时新消息</span>
        <span class="badge badge-green">实时</span>
      </h2>
      <div class="panel-meta">{rw_start} — {rw_end} | 下次检查：{next_check}</div>
      {recent_html if recent_items else '<div class="empty-state"><div class="empty-icon">📭</div><p>过去 12 小时内暂未发现相关新政策通知</p></div>'}
    </div>

    <!-- 面板 2：累积通知 -->
    <div id="panel-all" class="panel">
      <h2>
        <span>📚</span>
        <span>累积通知</span>
        <span class="badge badge-blue">全部</span>
      </h2>
      <div class="panel-meta">共收录 {total_count} 条历史记录，按发布时间倒序排列</div>
      {all_html if all_items else '<div class="empty-state"><div class="empty-icon">📭</div><p>暂无累积通知</p></div>'}
    </div>

    <!-- 面板 3：精选汇总 -->
    <div id="panel-official" class="panel">
      <h2>
        <span>🏛️</span>
        <span>精选汇总</span>
        <span class="badge badge-yellow">官网</span>
      </h2>
      <div class="panel-meta">汇总国家/地方卫健委、工信部、科技部、药监局等官方网站发布的政策通知</div>
      {official_html if official_items else '<div class="empty-state"><div class="empty-icon">📭</div><p>暂无官网消息</p></div>'}
    </div>

    <!-- 面板 4：春雨行动库 -->
    <div id="panel-chunyu" class="panel">
      <h2>
        <span>🌧️</span>
        <span>春雨行动库</span>
        <span class="badge badge-green">省份</span>
      </h2>
      <div class="panel-meta">已发布"春雨行动"实施方案或相关工作进展的省份，共 {province_count} 个</div>
      {chunyu_html if chunyu_items else '<div class="empty-state"><div class="empty-icon">📭</div><p>暂无省份入库</p></div>'}
    </div>

    <!-- 监控站点（始终显示） -->
    <div class="sites-card">
      <h3>🔭 重点监控官网</h3>
      {sites_html}
    </div>
  </div>

  <div class="footer">
    <p>由多多维护 · 每日 8:00 / 14:00 / 20:00 自动更新 · <a href="https://github.com/51020807-glitch/policy-dashboard" target="_blank" rel="noopener" style="color:var(--primary);">GitHub</a></p>
  </div>

  <script>
    function switchTab(tabName) {{
      // 切换卡片激活状态
      document.querySelectorAll('.tab-card').forEach(card => {{
        card.classList.toggle('active', card.dataset.tab === tabName);
      }});
      // 切换面板显示
      document.querySelectorAll('.panel').forEach(panel => {{
        panel.classList.toggle('active', panel.id === 'panel-' + tabName);
      }});
      // 滚动到面板
      const panel = document.getElementById('panel-' + tabName);
      if (panel) {{
        panel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }}

    // 支持 URL hash 定位（例如 ?tab=chunyu）
    (function() {{
      const params = new URLSearchParams(window.location.search);
      const tab = params.get('tab');
      if (tab) {{ switchTab(tab); }}
    }})();
  </script>
</body>
</html>
"""


def build_timeline_section(items: list) -> str:
    """构建时间线区域。"""
    if not items:
        return ""
    html_parts = ['<div class="timeline">']
    for item in items:
        html_parts.append(build_timeline_item(item))
    html_parts.append('</div>')
    return ''.join(html_parts)


def build_timeline_item(item: dict) -> str:
    """构建单个时间线条目。"""
    tags = ''.join(
        f'<span class="tag">{html.escape(tag)}</span>'
        for tag in item.get("tags", [])
    )
    link = item.get('link', '')
    link_html = ''
    if link:
        link_html = f'<a class="link" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">查看原文 →</a>'

    return f"""
    <div class="timeline-item">
      <div class="date">{html.escape(item.get('date', ''))}</div>
      <div class="title">{html.escape(item.get('title', ''))}</div>
      <div class="meta">来源：{html.escape(item.get('source', ''))}</div>
      <div class="summary">{html.escape(item.get('summary', ''))}</div>
      {link_html}
      <div class="tags">{tags}</div>
    </div>
    """


def build_chunyu_section(items: list) -> str:
    """构建春雨行动省份卡片网格。"""
    if not items:
        return ""
    cards = []
    for item in items:
        link_html = ''
        link = item.get('link', '')
        if link:
            link_html = f'<a class="link" href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">查看原文 →</a>'
        cards.append(f"""
        <div class="province-card">
          <div class="province-header">
            <span class="province-name">{html.escape(item.get('province', ''))}</span>
            <span class="province-status">{html.escape(item.get('status', ''))}</span>
          </div>
          <div class="province-date">{html.escape(item.get('date', ''))}</div>
          <div class="province-summary">{html.escape(item.get('summary', ''))}</div>
          {link_html}
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
