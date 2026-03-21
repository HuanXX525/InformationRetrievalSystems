# astrbot-plugin-helloworld

## 方案设计

![架构图](./res/aefcbc195f12059f0a07473d27da4c5e.png)

- 支持的语言：en
- 索引粒度：章节
- 文档格式: json
- 字符编码: utf-8
  
  ```json
  [
    {
      "ID":"", // 唯一标识符，务必确保唯一性，即使不同文档之间
      "title": "",
      "content": "", // 块内容
      "url": "", // 章节所在的文档的url
      "matadata": {} // 自定义数据
    },
    ...
  ]
  ```
