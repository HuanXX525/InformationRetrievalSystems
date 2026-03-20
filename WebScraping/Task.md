# 任务

写爬虫程序爬取 `https://docs.nvidia.com/cuda/cuda-programming-guide/` 页面上所有的章节标题以及内容，图片下载到本地，并且将爬取到的内容的图片链接改为本地相对路径。

关于爬取单位，以标题为分割单位，每个标题下的内容为一个单位，结果存到JSON文件中

每个单位的JSON的格式如下：
{
    "title": "章节标题",
    "content": "章节内容",
    "href": "来源"
}

使用的库为lxml和beautifulsoup4，其他库请自行选择。
