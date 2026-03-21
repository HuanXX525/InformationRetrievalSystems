import json

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
# from .init import load_spacy_model
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
import os.path as os_path
from pathlib import Path
import os
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.analysis import StemmingAnalyzer
from whoosh.index import create_in, exists_in, open_dir
from whoosh.qparser import QueryParser



# @register()
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        try:
            # self.nlp = load_spacy_model()
            self.name = "astrbot_plugin_information_retrieval"
            self.data_path = os_path.join(get_astrbot_data_path(), "plugin_data", self.name)
            self.document_path = os_path.join(self.data_path, "documents")
            self.index_path = os_path.join(self.data_path, "index")
            # 1. 创建索引目录
            if not os.path.exists(self.index_path):
                os.makedirs(self.index_path)
            if not os.path.exists(self.document_path):
                os.makedirs(self.document_path)
            
            # 2. 定义 Schema
            self.schema = Schema(
                ID=ID(stored=True, unique=True),
                title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
                url=ID(stored=True),
                content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
                metadata=TEXT(stored=True)
            )
    # 检查目录下是否已经存在有效的 Whoosh 索引
            if exists_in(self.index_path):
                self.d_index = open_dir(self.index_path)
                logger.info("成功加载现有索引。")
            else:
                self.d_index = create_in(self.index_path, self.schema)
                logger.info("未发现索引，已初始化新索引。")
            logger.info(f"\n[NOTE] 将要索引的文档置于 {self.document_path}\n")
            logger.info(f"{self.name} 插件初始化成功")
        except Exception as e:
            logger.error(f"初始化失败")
            logger.error(e)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    def quary_with_count(self, event: AstrMessageEvent, show_count:int=5):
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components 
        logger.info(message_chain)
        with self.d_index.searcher() as searcher:
        # 在 content 字段中搜索
            parser = QueryParser("content", self.d_index.schema)
            query = parser.parse(message_str)
            
            results = searcher.search(query, limit=show_count)
            
            yield event.plain_result(f"共找到 {len(results)} 个结果：\n")
            TEMPLATE = """
评分：{score:.2f}
标题：{title}
链接：{url}
----------------
"""
            res = ""
            for hit in results:
                res+=TEMPLATE.format(score=hit.score, title=hit["title"], url=hit["url"])
        yield event.plain_result(res) # 发送一条纯文本消息


    # @filter.command("QuaryMore")
    # async def quarymore(self, event: AstrMessageEvent, show_count:int=5):
    #     """显式查询指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
    #     # user_name = event.get_sender_name()
    #     self.quary_with_count(event, show_count)

    @filter.command("Quary")
    async def quary(self, event: AstrMessageEvent):
        message_str = event.message_str.replace("Quary", "", 1).strip() # 用户发的纯文本消息字符串
        
        logger.info(f"查询{message_str}")
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components 
        logger.info(message_chain)
        with self.d_index.searcher() as searcher:
        # 在 content 字段中搜索
            parser = QueryParser("content", self.d_index.schema)
            query = parser.parse(message_str)
            
            results = searcher.search(query, limit=5)
            
            yield event.plain_result(f"共找到 {len(results)} 个结果：\n")
            TEMPLATE = """
评分：{score:.2f}
标题：{title}
链接：{url}
----------------
"""
            res = ""
            for hit in results:
                res+=TEMPLATE.format(score=hit.score, title=hit["title"], url=hit["url"])
        yield event.plain_result(res) # 发送一条纯文本消息

    @filter.command("showdocs")
    async def showdocs(self, event: AstrMessageEvent):
        """查询所有文档""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        p = Path(self.document_path)
        TEMPLATE = """
查询到{count}个文档文件

{files}
"""
        res = ""
        counter = 0
        # 列出当前目录下的所有文件（不含子目录）
        for file in p.iterdir():
            if file.is_file():
                res += f"文件名:{file.name}     大小:{(file.stat().st_size/1048576):.2f}MB\n"
                counter += 1
        yield event.plain_result(TEMPLATE.format(count=counter, files=res)) # 发送一条纯文本消息

    @filter.command("index")
    async def index(self, event: AstrMessageEvent, fileName:str):
        """索引指定文档""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        # message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        # logger.info(message_chain)
        # use_str = event.message_str
        d_path = os_path.join(self.document_path, fileName)
        writer = self.d_index.writer()
        success_count = 0
        fail_count = 0

        with open(d_path, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        try:
            for doc in documents:
                if not all(k in doc for k in ['ID', 'url', 'content', 'title', 'metadata']) :
                    logger.warning(f"跳过格式不全的文档: {doc.get('title', '未知标题')}")
                    fail_count += 1
                    continue
                m_data = doc['metadata']
                if isinstance(m_data, dict):
                    m_data = json.dumps(m_data, ensure_ascii=False)
                else:
                    m_data = str(m_data)
                # 即使多次运行，由于 url 是唯一的，索引也不会膨胀
                writer.update_document(
                    ID=doc['ID'],
                    metadata=m_data,
                    title=doc['title'],
                    url=doc['url'],
                    content=doc['content']
                )
                success_count += 1
        except Exception as e:
            logger.warning(f"索引失败: {e}")
            # fail_count += 1
            # break
            yield event.plain_result(f"索引失败: {e}")

        try:
            writer.commit()
            logger.info(f"索引成功: {success_count} 条, 失败: {fail_count} 条")
            yield event.plain_result(f"索引成功: {success_count} 条, 失败: {fail_count} 条")
        except Exception as e:
            logger.error(f"提交失败: {e}")
            yield event.plain_result(f"提交失败: {e}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
