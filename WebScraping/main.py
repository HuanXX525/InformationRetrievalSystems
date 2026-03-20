import json

from bs4 import BeautifulSoup
import requests
import logging  # 确保导入了 logging
import chardet

import CUDAProgramGuide.pattern as CUDA
from CUDAProgramGuide.function import clean_and_reformat_episodes, parse_table_to_markdown
from urllib.parse import urljoin

# 1. 基础配置：设置级别为 INFO，并指定输出到控制台
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

response = requests.get(CUDA.URL)
encoding = chardet.detect(response.content)['encoding']
logger.info(f"检测到页面编码：{encoding}")
response.encoding = encoding

if response.status_code == 200:
    document_list = []
    logger.info("成功获取页面")
    soup = BeautifulSoup(response.content, "lxml")
    # 获取侧边栏导航页
    nav_sidebar = soup.find('nav', class_='bd-docs-nav bd-links') # CONFIG
    if nav_sidebar is None:
        logger.error("未找到侧边栏导航页")
        exit()
    episode_list : list[CUDA.Episode] = []
    references = nav_sidebar.find_all('a', class_='reference internal') # CONFIG
    for reference in references:
        episode_list.append(CUDA.Episode(reference.text, reference['href']))
    episode_list = clean_and_reformat_episodes(episode_list)
    for episode in episode_list:

        # 礼貌抓取：避免请求过快
        import time
        time.sleep(0.5)
        logger.info("抓取章节：{}".format(episode.title))
        # response = requests.get("https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/advanced-kernel-programming.html")
        response = requests.get(urljoin(CUDA.URL, episode.url))
        encoding = chardet.detect(response.content)['encoding']
        logger.info(f"检测到页面编码：{encoding}")
        response.encoding = encoding
        if response.status_code == 200:
            logger.info("成功获取页面")
            soup = BeautifulSoup(response.content, "lxml")
            # 解析每一个章节的内容，每个section下的内容提取为一个"文档"
            # 1. 定位正文主容器 (根据图片，正文在 <article class="bd-article"> 中)
            article = soup.find('article', class_='bd-article')
            if not article:
                continue

            # 2. 查找所有的 section，每个 section 作为一个独立的文档块
            # 使用 recursive=True 因为 section 往往是嵌套的
            sections = article.find_all('section')
            for section in sections:
                # 提取当前 section 的标题 (通常是 h2, h3 等)
                header_node = section.find(['h1', 'h2', 'h3', 'h4', 'h5'], recursive=False)
                section_title = header_node.get_text(strip=True) if header_node else "Untitled Section"
                
                # 组合最终文档标题：一级标题:二级标题 (沿用你之前的格式)
                # 如果 title 中已经包含冒号，说明是子章节，这里可以进一步拼接
                doc_title = f"{episode.title}:{section_title}"
                
                content_segments = []
                
                # 3. 遍历 section 下的直接子元素，提取正文、代码和表格
                # 使用 recursive=False 保证我们只取当前层级的内容，不重复提取子 section 的内容
                for child in section.find_all(recursive=False):
                    # 处理普通段落
                    if child.name == 'p':
                        text = child.get_text(strip=True)
                        if text:
                            content_segments.append(text)
                    
                    # 处理代码块 (根据图片：div class="highlight-c++")
                    # elif child.name == 'div' and 'highlight' in child.get('class', []):
                    classes = child.get('class') or []  # 如果 get 返回 None，则设为空列表
                    if child.name == 'div':
                        if 'pst-scrollable-table-container' in classes:
                            target_table = child.find('table')
                            if target_table:
                                table_content = parse_table_to_markdown(target_table)
                                content_segments.append(table_content)
                        code = child.find("pre", recursive=True)
                        if code is not None:
                            code_block = code.get_text(strip=True)
                            content_segments.append(f"```\n{code_block}\n```")
                        else:
                            text = child.get_text(strip=True)
                            if text:
                                content_segments.append(text)
                        

                    
                    # 处理表格
                    if child.name == 'table':
                        # 简单处理：将表格转为纯文本或自定义格式
                        table_data = []
                        for row in child.find_all('tr'):
                            cells = [td.get_text(strip=True) for td in row.find_all(['th', 'td'])]
                            table_data.append(" | ".join(cells))
                        content_segments.append("\n".join(table_data))

                    elif child.name == 'figure':
                        img_tag = child.find('img')
                        if img_tag is None:
                            logger.warning("提取图片失败")
                            continue
                        src_value = img_tag.get('src')
                        if src_value:
                            # 强制转换为字符串，确保 urljoin 不会收到 AttributeValueList
                            img_url = urljoin(CUDA.URL, str(src_value))
                        # if img_tag:
                            # img_url = urljoin(CUDA.URL, img_tag.get('src'))
                            alt_text = img_tag.get('alt', '无描述')
                            
                            # 尝试获取图注
                            caption_node = child.find('figcaption')
                            caption = caption_node.get_text(strip=True) if caption_node else ""
                            
                            # 将图片信息转化为文本存储，确保 RAG 系统知道这里有一张图 
                            content_segments.append(f"【图片：{alt_text}。图注：{caption}。链接：{img_url}】")

                # 4. 构造结构化文档对象
                if content_segments:
                    document = {
                        "title": doc_title,
                        "url": urljoin(CUDA.URL, episode.url) + f"#{section.get('id', '')}",
                        "content": "\n\n".join(content_segments),
                        "metadata": {
                            "source": "NVIDIA CUDA Programming Guide",
                            "type": "technical_doc"
                        }
                    }
                    document_list.append(document)
                    # 此时你可以将 document 加入一个全局列表，最后统一保存为 JSON
                    # results.append(document)
                    logger.info(f"--- 已提取文档块: {doc_title}")
        else:
            logger.error(f"无法获取页面，状态码：{response.status_code}\nURL: {urljoin(CUDA.URL, episode.url)}")
        # break

    json.dump(document_list, open("CUDA.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    


else:
    logger.error(f"无法获取页面，状态码：{response.status_code}")