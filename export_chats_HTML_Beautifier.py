# -*- coding: utf-8 -*-
import os
import sys
import webbrowser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ==========================================
# 1. 渲染器类 (V8.0 菜单性能深度优化版)
# ==========================================
class MobileQQRenderer:
    def __init__(self, owner_name):
        self.owner_name = owner_name
        self.messages = []
        self.avatar_colors = {"self": "#0099ff", "other": "#ff5c5c"}
        
        self.css_style = """
        /* --- 全局重置 --- */
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { 
            background-color: #f5f5f5; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            margin: 0; padding: 0; 
        }
        
        /* 容器与导航 */
        .mobile-container { 
            max-width: 600px; margin: 0 auto; min-height: 100vh; position: relative; 
            background-color: #f5f5f5; border-left: 1px solid #ebedf0; border-right: 1px solid #ebedf0; 
            padding-top: 50px; 
        }
        .nav-bar { 
            position: fixed; top: 0; left: 0; right: 0; margin: 0 auto; max-width: 600px; 
            height: 50px; background: linear-gradient(90deg, #29b6f6, #0099ff); color: white; 
            padding: 0 15px; display: flex; align-items: center; justify-content: space-between; 
            z-index: 1000; box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        }
        .nav-title { font-size: 18px; font-weight: 500; }
        .nav-btn { background: transparent; border: none; color: white; font-size: 24px; padding: 5px 15px; cursor: pointer; }
        
        /* --- 聊天区域 (正文性能优化) --- */
        .chat-area { padding: 15px 12px 80px 12px; }
        .day-container { 
            content-visibility: auto; 
            contain-intrinsic-size: 1000px; /* 预估高度，防止滚动条剧烈跳动 */
        }
        
        /* --- 消息气泡样式 --- */
        .date-header { text-align: center; margin: 20px 0; position: sticky; top: 55px; z-index: 10; pointer-events: none; }
        .date-header span { background-color: rgba(0,0,0,0.15); color: #fff; padding: 4px 12px; border-radius: 12px; font-size: 12px; backdrop-filter: blur(2px); }
        .time-tip { text-align: center; margin: 10px 0; color: #ccc; font-size: 12px; }
        
        .message-row { display: flex; margin-bottom: 15px; align-items: flex-start; }
        .avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #ccc; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; }
        .bubble-container { max-width: 75%; display: flex; flex-direction: column; }
        .sender-name { font-size: 12px; color: #999; margin-bottom: 4px; margin-left: 6px; }
        .bubble { padding: 10px 14px; border-radius: 10px; font-size: 16px; line-height: 1.5; word-wrap: break-word; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .bubble img { max-width: 100%; border-radius: 6px; display: block; height: auto; }
        
        .message-row.other .avatar { margin-right: 10px; }
        .message-row.other .bubble { background-color: #fff; color: #000; border-top-left-radius: 2px; }
        .message-row.self { flex-direction: row-reverse; }
        .message-row.self .avatar { margin-left: 10px; }
        .message-row.self .bubble-container { align-items: flex-end; }
        .message-row.self .sender-name { display: none; }
        .message-row.self .bubble { background-color: #0099ff; color: #fff; border-top-right-radius: 2px; }
        
        /* 搜索高亮 */
        .highlight-match { background-color: #ffeb3b; color: #000; }
        .current-match { background-color: #ff9800; color: #fff; box-shadow: 0 0 0 3px rgba(255, 152, 0, 0.5); border-radius: 2px; }

        /* --- 菜单抽屉 (菜单性能深度优化) --- */
        .menu-overlay { 
            position: fixed; top: 0; right: 0; bottom: 0; left: 0; 
            background: rgba(0,0,0,0.5); z-index: 2000; 
            visibility: hidden; opacity: 0; 
            transition: opacity 0.2s, visibility 0.2s; 
        }
        .menu-overlay.show { visibility: visible; opacity: 1; }
        
        .menu-drawer { 
            position: absolute; top: 0; right: 0; bottom: 0; width: 85%; max-width: 320px; 
            background: #fff; 
            transform: translateX(100%); 
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); 
            display: flex; flex-direction: column; 
            box-shadow: -5px 0 15px rgba(0,0,0,0.1); 
            will-change: transform; /* GPU加速提示 */
            contain: layout size; /* 告诉浏览器此容器尺寸独立，减少重排 */
        }
        .menu-overlay.show .menu-drawer { transform: translateX(0); }
        
        .drawer-header { padding: 15px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; font-weight: bold; flex-shrink: 0; }
        .drawer-content { flex: 1; overflow-y: auto; padding: 10px; -webkit-overflow-scrolling: touch; }

        /* --- 菜单折叠项优化 (解决卡顿的核心) --- */
        details.menu-year { 
            margin-bottom: 5px; 
            border: 1px solid #f0f0f0; 
            border-radius: 6px; 
            overflow: hidden;
            
            /* 关键优化：折叠时不渲染内部成百上千的天数节点 */
            content-visibility: auto; 
            contain-intrinsic-size: 46px; /* 预估标题高度 */
        }
        
        details.menu-year > summary { 
            background: #f8f9fa; padding: 12px; font-weight: bold; cursor: pointer; 
            list-style: none; display: flex; justify-content: space-between; align-items: center; 
        }
        details.menu-year > summary::after { content: '+'; font-weight: normal; color: #999; }
        details.menu-year[open] > summary::after { content: '-'; }
        
        /* 月份优化 */
        details.menu-month { 
            margin: 0; border-top: 1px solid #eee; 
            content-visibility: auto; /* 对月份也进行懒渲染 */
            contain-intrinsic-size: 40px;
        }
        details.menu-month > summary { 
            padding: 10px 12px 10px 24px; cursor: pointer; color: #333; font-size: 14px; 
            background: #fff; border-bottom: 1px solid #fcfcfc; 
        }
        
        .menu-day-item { 
            display: flex; justify-content: space-between; padding: 10px 12px 10px 40px; 
            font-size: 13px; color: #666; cursor: pointer; border-bottom: 1px solid #f5f5f5; 
            background: #fff; 
        }
        .menu-day-item:active { background: #e6f7ff; color: #0099ff; }
        
        /* 搜索框与回到顶部 */
        .search-area { padding-bottom: 10px; border-bottom: 1px solid #eee; margin-bottom: 10px; }
        .search-group { display: flex; gap: 5px; margin-bottom: 8px; }
        .search-input { flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .search-btn { background: #0099ff; color: white; border: none; padding: 0 12px; border-radius: 4px; font-size: 14px; }
        .search-nav { display: flex; justify-content: space-between; font-size: 13px; color: #666; }
        .nav-link { color: #0099ff; padding: 5px 10px; cursor: pointer; }
        
        .back-to-top { 
            position: fixed; bottom: 30px; right: 20px; width: 45px; height: 45px; 
            background: rgba(255,255,255,0.95); border-radius: 50%; box-shadow: 0 4px 12px rgba(0,0,0,0.15); 
            display: flex; align-items: center; justify-content: center; color: #0099ff; 
            font-weight: bold; opacity: 0; transform: scale(0.8); transition: all 0.3s; 
            pointer-events: none; z-index: 1500; border: 1px solid #eee; 
        }
        .back-to-top.show { opacity: 1; transform: scale(1); pointer-events: auto; }
        """

        self.js_script = """
        // 1. 菜单切换
        function toggleMenu() {
            const overlay = document.getElementById('menuOverlay');
            if (overlay.classList.contains('show')) {
                overlay.classList.remove('show');
                document.body.style.overflow = ''; 
            } else {
                overlay.classList.add('show');
                document.body.style.overflow = 'hidden'; 
            }
        }

        // 2. 跳转与重排
        function jumpToDate(dateId) {
            toggleMenu(); 
            // 使用 setTimeout 允许菜单动画先播放
            setTimeout(() => {
                const el = document.getElementById(dateId);
                if(el) {
                    // 强制唤醒被 content-visibility 隐藏的元素
                    el.style.contentVisibility = 'visible'; 
                    // 触发重排，确保高度计算正确
                    void el.offsetHeight;
                    
                    const offset = 60; 
                    const pos = el.getBoundingClientRect().top + window.pageYOffset - offset;
                    window.scrollTo({ top: pos, behavior: "auto" });
                }
            }, 100);
        }

        // 3. 回到顶部
        const topBtn = document.getElementById('backToTopBtn');
        window.addEventListener('scroll', () => {
            if (window.scrollY > 600) topBtn.classList.add('show');
            else topBtn.classList.remove('show');
        }, { passive: true });
        
        function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }); }

        // 4. 搜索逻辑 (兼容 content-visibility)
        let matches = [];
        let currentMatchIndex = -1;
        
        async function executeSearch() {
            const keyword = document.getElementById('searchInput').value.trim();
            const statusEl = document.getElementById('searchStatus');
            
            if (!keyword) { statusEl.innerText = ''; return; }
            statusEl.innerText = '搜索中...';
            
            // 清理高亮
            document.querySelectorAll('.highlight-match').forEach(el => {
                el.parentNode.replaceChild(document.createTextNode(el.innerText), el);
            });
            document.querySelectorAll('.current-match').forEach(el => el.classList.remove('current-match'));
            
            matches = [];
            currentMatchIndex = -1;
            
            // UI 喘息
            await new Promise(r => setTimeout(r, 20));

            const bubbles = document.querySelectorAll('.bubble');
            const safeKeyword = keyword.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'); 
            const regex = new RegExp(safeKeyword, 'gi');
            
            const chunkSize = 500;
            for (let i = 0; i < bubbles.length; i += chunkSize) {
                const chunk = Array.from(bubbles).slice(i, i + chunkSize);
                chunk.forEach(bubble => {
                    // 使用 textContent 匹配隐藏文本
                    if (bubble.textContent.toLowerCase().includes(keyword.toLowerCase())) {
                        bubble.innerHTML = bubble.innerHTML.replace(regex, '<span class="highlight-match">$&</span>');
                        bubble.querySelectorAll('.highlight-match').forEach(m => matches.push(m));
                    }
                });
                if (i % 1000 === 0) await new Promise(r => setTimeout(r, 0)); 
            }

            if (matches.length > 0) {
                currentMatchIndex = 0;
                highlightCurrent();
            } else {
                statusEl.innerText = '未找到';
            }
        }

        function highlightCurrent() {
            document.querySelectorAll('.current-match').forEach(el => el.classList.remove('current-match'));
            const target = matches[currentMatchIndex];
            if (target) {
                target.classList.add('current-match');
                
                // 唤醒父容器
                const dayContainer = target.closest('.day-container');
                if(dayContainer) {
                    dayContainer.style.contentVisibility = 'visible';
                    void dayContainer.offsetHeight;
                }
                
                target.scrollIntoView({ behavior: 'auto', block: 'center' });
                // 二次校正
                setTimeout(() => { target.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 100);
                
                document.getElementById('searchStatus').innerText = `${currentMatchIndex + 1}/${matches.length}`;
            }
        }
        
        function nextMatch() { if (matches.length === 0) return; currentMatchIndex = (currentMatchIndex + 1) % matches.length; highlightCurrent(); }
        function prevMatch() { if (matches.length === 0) return; currentMatchIndex = (currentMatchIndex - 1 + matches.length) % matches.length; highlightCurrent(); }
        """

    def add_message(self, dt_obj, sender, content):
        self.messages.append({
            "dt": dt_obj, "sender": sender, "content": content, "is_self": sender == self.owner_name
        })

    def generate_html(self, output_file, chat_title="聊天记录"):
        self.messages.sort(key=lambda x: x['dt'])
        
        # 构建日期索引
        date_groups = {} 
        date_hierarchy = {} 
        
        for msg in self.messages:
            d_str = msg['dt'].strftime("%Y-%m-%d")
            
            if d_str not in date_groups: date_groups[d_str] = []
            date_groups[d_str].append(msg)
            
            y = str(msg['dt'].year)
            m = str(msg['dt'].month)
            if y not in date_hierarchy: date_hierarchy[y] = {}
            if m not in date_hierarchy[y]: date_hierarchy[y][m] = set()
            date_hierarchy[y][m].add(d_str)

        sorted_dates = sorted(date_groups.keys())

        # HTML 构建
        html = [
            '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
            f'<title>{chat_title}</title><style>{self.css_style}</style></head><body>',
            '<div class="mobile-container">',
            
            # 顶部导航
            f'<div class="nav-bar"><div class="nav-title">{chat_title}</div><button class="nav-btn" onclick="toggleMenu()">☰</button></div>',
            
            # 菜单 (预渲染结构，但在浏览器中懒加载渲染)
            '<div class="menu-overlay" id="menuOverlay" onclick="toggleMenu()"><div class="menu-drawer" onclick="event.stopPropagation()">',
            '<div class="drawer-header"><span>导航</span><span onclick="toggleMenu()" style="padding:10px;font-size:20px">×</span></div>',
            '<div class="drawer-content">',
            
            # 搜索区
            '<div class="search-area"><div class="search-group"><input type="text" id="searchInput" class="search-input" placeholder="搜索关键词"><button class="search-btn" onclick="executeSearch()">搜</button></div>',
            '<div class="search-nav"><span class="nav-link" onclick="prevMatch()">上一个</span><span id="searchStatus" style="line-height:28px"></span><span class="nav-link" onclick="nextMatch()">下一个</span></div></div>',
            
            # 日期列表 (嵌套手风琴)
            '<div id="dateList">',
        ]
        
        for year in sorted(date_hierarchy.keys(), reverse=True):
            html.append(f'<details class="menu-year"><summary>{year}年</summary>')
            months = date_hierarchy[year]
            for month in sorted(months.keys(), key=lambda x: int(x), reverse=True):
                html.append(f'<details class="menu-month"><summary>{month}月</summary>')
                days_set = months[month]
                for d_str in sorted(list(days_set), reverse=True):
                    count = len(date_groups[d_str])
                    display_day = d_str.split('-')[-1] + "日"
                    html.append(f'<div class="menu-day-item" onclick="jumpToDate(\'date-{d_str}\')"><span>{display_day}</span><span>{count}条</span></div>')
                html.append('</details>')
            html.append('</details>')
            
        html.append('</div></div></div></div>') # 闭合菜单

        # 正文区域
        html.append('<div class="chat-area">')
        for date_str in sorted_dates:
            html.append(f'<div id="date-{date_str}" class="day-container">')
            html.append(f'<div class="date-header"><span>{date_str}</span></div>')
            
            last_dt = None
            for msg in date_groups[date_str]:
                if last_dt is None or (msg['dt'] - last_dt) > timedelta(minutes=5):
                    html.append(f'<div class="time-tip">{msg["dt"].strftime("%H:%M")}</div>')
                last_dt = msg['dt']
                
                row_cls = "self" if msg['is_self'] else "other"
                avatar_bg = self.avatar_colors["self"] if msg['is_self'] else self.avatar_colors["other"]
                short_name = msg['sender'][0] if msg['sender'] else "?"
                content = msg["content"].replace('<img ', '<img loading="lazy" ')
                
                html.append(f'<div class="message-row {row_cls}"><div class="avatar" style="background-color: {avatar_bg}">{short_name}</div>')
                html.append(f'<div class="bubble-container">')
                if not msg['is_self']: html.append(f'<div class="sender-name">{msg["sender"]}</div>')
                html.append(f'<div class="bubble">{content}</div></div></div>')
            html.append('</div>')

        html.append('<div id="backToTopBtn" class="back-to-top" onclick="scrollToTop()">↑</div>')
        html.append('</div></div>')
        html.append(f'<script>{self.js_script}</script></body></html>')

        with open(output_file, "w", encoding="utf-8") as f: f.write("\n".join(html))
        return os.path.abspath(output_file)

# ==========================================
# 2. 解析逻辑
# ==========================================
def extract_messages_from_html(file_path):
    print(f"正在读取文件: {file_path} ...")
    raw_messages = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return []

    date_blocks = soup.find_all("details", class_="date-block")
    print(f"找到 {len(date_blocks)} 个日期块，正在提取数据...")

    for block in date_blocks:
        summary = block.find("summary")
        if not summary: continue
        date_str = summary.get_text(strip=True)
        
        groups = block.find_all("div", class_="sender-message-group")
        for group in groups:
            sender_div = group.find("div", class_="sender")
            if not sender_div: continue
            sender = sender_div.get_text(strip=True)
            
            items = group.find_all("div", class_="message-item")
            for item in items:
                time_span = item.find("span", class_="timestamp")
                content_span = item.find("span", class_="message-content")
                if time_span and content_span:
                    full_dt_str = f"{date_str} {time_span.get_text(strip=True)}"
                    try:
                        dt = datetime.strptime(full_dt_str, "%Y-%m-%d %H:%M:%S")
                        content_html = "".join([str(x) for x in content_span.contents])
                        raw_messages.append({
                            "dt": dt,
                            "sender": sender,
                            "content": content_html
                        })
                    except ValueError: pass
    
    print(f"解析完成！共提取 {len(raw_messages)} 条消息。")
    return raw_messages

# ==========================================
# 3. 交互逻辑
# ==========================================
def get_input_path():
    while True:
        path = input("\n请输入聊天记录HTML文件的完整路径: ").strip()
        path = path.strip('"').strip("'")
        if os.path.exists(path) and os.path.isfile(path):
            return path
        else:
            print("❌ 路径无效或文件不存在，请重新输入。")

def select_my_nickname(raw_messages):
    if not raw_messages:
        return "我"
    senders = list(set(msg['sender'] for msg in raw_messages))
    senders.sort()
    
    print("\n请选择哪一个名字代表【你自己】:")
    for index, name in enumerate(senders):
        print(f"{index + 1}. {name}")
    
    while True:
        choice = input(f"请输入序号 (1-{len(senders)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(senders):
                selected = senders[idx]
                print(f"✅ 已选择: {selected}")
                return selected
        print("❌ 输入无效。")

if __name__ == "__main__":
    print("=== QQ聊天记录转手机版HTML工具 ===")
    
    input_file_path = get_input_path()
    raw_data = extract_messages_from_html(input_file_path)
    
    if raw_data:
        my_nickname = select_my_nickname(raw_data)
        
        renderer = MobileQQRenderer(owner_name=my_nickname)
        for msg in raw_data:
            renderer.add_message(msg['dt'], msg['sender'], msg['content'])
        
        base_name = os.path.splitext(input_file_path)[0]
        output_file_name = f"{base_name}_手机版.html"
        
        print(f"\n正在生成文件，请稍候...")
        output_path = renderer.generate_html(output_file_name, chat_title="聊天详情")
        
        print(f"\n🎉 成功生成文件: {output_path}")
        webbrowser.open(f"file://{output_path}")
        input("\n按回车键退出程序...")
    else:
        print("\n⚠️ 未能在文件中提取到任何消息。")
        input("\n按回车键退出程序...")