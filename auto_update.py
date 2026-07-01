#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政策通知自动更新脚本 — 运行在 GitHub Actions 中。
搜索新政策通知 → 更新 dashboard-data.json → 重新生成 index.html。
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

# ── 配置 ──────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "dashboard-data.json"
HTML_FILE = BASE_DIR / "index.html"

# 北京时间时区
TZ_BEIJING = timezone(timedelta(hours=8))

# 搜索关键词
KEYWORDS = [
    "春雨行动 医疗器械 临床创新 成果转化",
    "国家重点研发计划 指南 通知",
    "国家科技重大专项 立项",
]

# 重点监控官网及其搜索入口
MONITORED_SITES = [
    "国家卫健委 nhc.gov.cn",
    "国家工信部 miit.gov.cn",
    "国家科技部 service.most.gov.cn",
    "国家药监局 nmpa.gov.cn",
    "各省药监局",
]

# 官网精确搜索 URL（使用搜索引擎的 site: 语法来搜索官网内容）
OFFICIAL_SEARCHES = [
    ("site:nhc.gov.cn 春雨行动 医疗器械", "国家卫健委"),
    ("site:nmpa.gov.cn 春雨行动 医疗器械 创新", "国家药监局"),
    ("site:miit.gov.cn 医疗器械 创新 成果转化", "国家工信部"),
    ("site:service.most.gov.cn 国家重点研发计划 指南 通知", "国家科技部"),
    ("site:gov.cn 春雨行动 医疗器械 药监局 实施方案", "各省政府"),
]


# ── 工具函数 ──────────────────────────────────────────

def now_beijing() -> datetime:
    """获取当前北京时间。"""
    return datetime.now(TZ_BEIJING)


def format_bj(dt: datetime) -> str:
    """格式化为北京时间字符串。"""
    return dt.astimezone(TZ_BEIJING).strftime("%Y-%m-%d %H:%M")


def format_date_bj(dt: datetime) -> str:
    """格式化为日期字符串。"""
    return dt.astimezone(TZ_BEIJING).strftime("%Y-%m-%d")


def load_data() -> dict:
    """加载看板数据。"""
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {
        "lastUpdated": "",
        "nextCheck": "",
        "recentWindow": {"start": "", "end": ""},
        "recentItems": [],
        "allItems": [],
        "officialItems": [],
        "chunyuItems": [],
        "monitoredSites": MONITORED_SITES,
    }


def save_data(data: dict):
    """保存看板数据。"""
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def normalize_title(title: str) -> str:
    """生成规范的标题键，用于去重。"""
    # 提取前30个字作为去重键
    key = re.sub(r"\s+", "", title)
    return key[:30]


# ── 搜索 ──────────────────────────────────────────────

def search_duckduckgo(query: str, max_results: int = 10) -> list[dict]:
    """
    使用 DuckDuckGo 搜索（通过 HTML 抓取，避免依赖故障）。
    返回列表：[{title, link, snippet, date}, ...]
    """
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="cn-zh", max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", ""),
                        "date": r.get("date", ""),
                    }
                )
        return results
    except ImportError:
        print("[WARN] duckduckgo_search 未安装，跳过 DuckDuckGo 搜索")
        return []
    except Exception as e:
        print(f"[WARN] DuckDuckGo 搜索失败: {e}")
        return []


def search_bing(query: str, max_results: int = 10) -> list[dict]:
    """使用 Bing 搜索作为备用。"""
    try:
        encoded = quote(query)
        url = f"https://www.bing.com/search?q={encoded}&count={max_results}&setlang=zh-cn"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for item in soup.select("li.b_algo"):
            title_el = item.select_one("h2 a")
            snippet_el = item.select_one(".b_caption p")
            if title_el:
                results.append(
                    {
                        "title": title_el.get_text(strip=True),
                        "link": title_el.get("href", ""),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "date": "",
                    }
                )
        return results[:max_results]
    except Exception as e:
        print(f"[WARN] Bing 搜索失败: {e}")
        return []


def combined_search(query: str, max_results: int = 10) -> list[dict]:
    """组合搜索：先 DuckDuckGo，失败则用 Bing。"""
    results = search_duckduckgo(query, max_results)
    if not results:
        print(f"  DuckDuckGo 无结果，尝试 Bing...")
        results = search_bing(query, max_results)
    return results


def fetch_page_title(url: str) -> str:
    """抓取网页标题。"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title
        if title:
            return title.get_text(strip=True)
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
    except Exception:
        pass
    return ""


# ── 解析与过滤 ────────────────────────────────────────

def is_relevant(item: dict) -> bool:
    """判断搜索结果是否与目标政策相关。"""
    text = (item.get("title", "") + item.get("snippet", "")).lower()
    # 必须包含的关键词之一
    must_have = ["春雨行动", "国家重点研发计划", "国家科技重大专项"]
    has_keyword = any(kw.lower() in text for kw in must_have)

    # 排除无关内容
    exclude = ["天气预报", "电影", "电视剧", "综艺", "游戏", "彩票"]
    has_exclude = any(ex.lower() in text for ex in exclude)

    return has_keyword and not has_exclude


def is_official_source(item: dict) -> bool:
    """判断是否来自官方政府网站。"""
    link = item.get("link", "").lower()
    official_domains = [
        "gov.cn", "nhc.gov.cn", "miit.gov.cn", "nmpa.gov.cn",
        "most.gov.cn", "service.most.gov.cn",
    ]
    return any(d in link for d in official_domains)


def extract_date_from_text(text: str) -> str:
    """从文本中提取日期。"""
    # 常见格式：2026年6月1日 / 2026-06-01 / 2026.06.01
    patterns = [
        r"(\d{4})[年\-\/.](\d{1,2})[月\-\/.](\d{1,2})",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            try:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                return f"{y:04d}-{mo:02d}-{d:02d}"
            except ValueError:
                pass
    return ""


def guess_source_from_url(url: str) -> str:
    """从 URL 猜测来源。"""
    source_map = {
        "nhc.gov.cn": "国家卫健委",
        "miit.gov.cn": "国家工信部",
        "nmpa.gov.cn": "国家药监局",
        "most.gov.cn": "国家科技部",
        "gov.cn": "政府网站",
        "qq.com": "腾讯新闻",
        "sohu.com": "搜狐",
        "sina.com": "新浪",
        "cnpharm.com": "中国医药报",
        "163.com": "网易",
    }
    for domain, name in source_map.items():
        if domain in url:
            return name
    return "网络来源"


def extract_tags(text: str, url: str) -> list[str]:
    """从文本和URL中提取标签。"""
    tags = []
    if "春雨行动" in text:
        tags.append("春雨行动")
    if "国家重点研发计划" in text:
        tags.append("国家重点研发计划")
    if "国家科技重大专项" in text:
        tags.append("国家科技重大专项")
    if any(d in url for d in ["gov.cn"]):
        tags.append("官方发文")

    # 提取省份
    provinces = [
        "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林",
        "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
        "湖北", "湖南", "广东", "广西", "海南", "四川", "贵州", "云南",
        "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆", "内蒙古",
    ]
    for p in provinces:
        if p in text[:200]:  # 只在标题和前200字中检测省份
            if p not in tags:
                tags.append(p)
            if len(tags) >= 5:
                break

    return tags[:5]


# ── 主更新逻辑 ────────────────────────────────────────

def collect_new_items(since: datetime) -> list[dict]:
    """收集自指定时间以来的新政策通知。"""
    all_results = []

    # 1. 搜索关键词
    for kw in KEYWORDS:
        print(f"\n🔍 搜索: {kw}")
        results = combined_search(kw, max_results=8)
        relevant = [r for r in results if is_relevant(r)]
        print(f"  找到 {len(relevant)} 条相关结果")
        all_results.extend(relevant)
        time.sleep(2)  # 避免请求过于频繁

    # 2. 搜索官方渠道
    for query, source_name in OFFICIAL_SEARCHES:
        print(f"\n🔍 官方搜索 [{source_name}]: {query}")
        results = combined_search(query, max_results=5)
        relevant = [r for r in results if is_relevant(r)]
        print(f"  找到 {len(relevant)} 条相关结果")
        for r in relevant:
            r["_official_source"] = source_name
        all_results.extend(relevant)
        time.sleep(2)

    # 3. 去重并格式化
    seen = set()
    items = []
    for r in all_results:
        title = r.get("title", "").strip()
        if not title:
            continue
        norm = normalize_title(title)
        if norm in seen:
            continue
        seen.add(norm)

        link = r.get("link", "")
        snippet = r.get("snippet", "")

        # 提取日期
        date_str = r.get("date", "") or extract_date_from_text(title + snippet)
        if not date_str:
            date_str = format_date_bj(now_beijing())

        source = r.get("_official_source", "") or guess_source_from_url(link)
        tags = extract_tags(title + snippet, link)

        items.append(
            {
                "date": date_str,
                "title": title,
                "source": source,
                "summary": snippet[:200] if snippet else "",
                "link": link,
                "tags": tags,
            }
        )

    # 按日期倒序排列
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def update_dashboard():
    """主流程：更新看板数据。"""
    now = now_beijing()
    print(f"🕐 当前北京时间: {format_bj(now)}")

    # 加载现有数据
    data = load_data()

    # 计算时间窗口
    twelve_hours_ago = now - timedelta(hours=12)
    recent_window = {
        "start": format_bj(twelve_hours_ago),
        "end": format_bj(now),
    }

    # 确定下次检查时间
    hour = now.hour
    if hour < 8:
        next_hour = 8
    elif hour < 14:
        next_hour = 14
    elif hour < 20:
        next_hour = 20
    else:
        next_hour = 8  # 明天8点

    next_check = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    if next_check <= now:
        next_check += timedelta(days=1)
        next_check = next_check.replace(hour=8)

    # 收集新数据
    print("\n" + "=" * 60)
    print("开始搜索新政策通知...")
    print("=" * 60)

    scanned_items = collect_new_items(twelve_hours_ago)

    # 去重（与已有 allItems 比对）
    existing_titles = {normalize_title(it["title"]) for it in data.get("allItems", [])}
    new_items = []
    for item in scanned_items:
        norm = normalize_title(item["title"])
        if norm not in existing_titles:
            new_items.append(item)
            existing_titles.add(norm)

    print(f"\n📊 扫描到 {len(scanned_items)} 条，新增 {len(new_items)} 条")

    # 判断是否是过去12小时内的新消息
    recent_cutoff = format_date_bj(twelve_hours_ago)
    recent_new = [
        item for item in new_items if item["date"] >= recent_cutoff
    ]

    # 判断是否来自官方渠道
    official_new = [
        item
        for item in new_items
        if is_official_source(item) or "_official_source" in item
    ]

    # 更新数据
    data["lastUpdated"] = format_bj(now)
    data["nextCheck"] = format_bj(next_check)
    data["recentWindow"] = recent_window

    # 更新 recentItems（仅过去12小时的新消息）
    data["recentItems"] = recent_new

    # 追加到 allItems（前面插入）
    all_items = data.get("allItems", [])
    all_titles = {normalize_title(it["title"]) for it in all_items}
    for item in reversed(new_items):  # 按时间正序插入
        if normalize_title(item["title"]) not in all_titles:
            all_items.insert(0, item)
    # 按日期倒序排列
    all_items.sort(key=lambda x: x.get("date", ""), reverse=True)
    data["allItems"] = all_items

    # 追加到 officialItems
    official_items = data.get("officialItems", [])
    off_titles = {normalize_title(it["title"]) for it in official_items}
    for item in official_new:
        if normalize_title(item["title"]) not in off_titles:
            official_items.insert(0, item)
    official_items.sort(key=lambda x: x.get("date", ""), reverse=True)
    data["officialItems"] = official_items

    data["monitoredSites"] = MONITORED_SITES

    # 保存数据
    save_data(data)
    print(f"✅ 数据已保存到 {DATA_FILE}")

    # 重新生成 HTML
    update_html(data)
    print(f"✅ 看板已生成到 {HTML_FILE}")


def update_html(data: dict):
    """调用 update_dashboard.py 中的逻辑生成 HTML。"""
    sys.path.insert(0, str(BASE_DIR))
    from update_dashboard import build_html

    html_content = build_html(data)
    HTML_FILE.write_text(html_content, encoding="utf-8")


# ── 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    update_dashboard()
