import re
from CUDAProgramGuide.pattern import Episode

def clean_and_reformat_episodes(episode_list) -> list[Episode]:
    cleaned_list = []
    current_primary = ""  # 用于记录当前的一级标题内容

    for ep in episode_list:
        title = ep.title.strip()
        
        # 匹配开头的数字和点，例如 "1. " 或 "1.1. "
        # ^\d+(\.\d+)*\.?\s* 匹配：开始的一串数字、点、空格
        match = re.match(r'^(\d+(\.\d+)*\.?)\s*(.*)', title)
        
        if match:
            number_part = match.group(1)  # 数字部分，如 "1." 或 "1.1."
            content_part = match.group(3) # 文字部分，如 "Introduction to CUDA"
            
            # 判断级别：计算数字部分中“点”的数量
            dot_count = number_part.count('.')
            
            # 情况1：一级标题 (形如 "1." 只有一个点，或者数字后没点但只有一段数字)
            if dot_count == 1 and number_part.endswith('.'):
                current_primary = content_part
                # 根据需求：我们只保留二级，所以这里不添加进 cleaned_list，只更新当前一级标题名
            
            # 情况2：二级标题 (形如 "1.1.")
            elif dot_count >= 2:
                new_title = f"{current_primary}:{content_part}"
                ep.title = new_title
                cleaned_list.append(ep)
                
    return cleaned_list


def parse_table_to_markdown(table_tag):
    rows = []
    # 处理表头
    thead = table_tag.find('thead')
    if thead:
        for tr in thead.find_all('tr'):
            cols = [th.get_text(strip=True) for th in tr.find_all('th')]
            rows.append("| " + " | ".join(cols) + " |")
            rows.append("| " + " | ".join(['---'] * len(cols)) + " |")
    
    # 处理表身
    tbody = table_tag.find('tbody')
    target = tbody if tbody else table_tag # 有些表格没有 tbody
    for tr in target.find_all('tr', recursive=False):
        cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
        if cols:
            rows.append("| " + " | ".join(cols) + " |")
            
    return "\n".join(rows)