# 高等科学体系 · 学术站点（Higher Science — Academic Site）

本站点是「高等科学体系」的对外发布载体，包含文章、栏目、术语表与站点构建脚本。

- 正式站点（国内）：<http://higher-science.cn/>
- 镜像站点（GitHub Pages）：<https://higher-science.github.io/>

## 关于本体系

高等科学体系以**信息本体论**为基底（信息即主体之间的相互作用），区分两件事：

- **初等科学** —— 对象可拆可装可复原，由外力组织，方法有效；
- **高等科学** —— 整体通过规则、边界与关系结构构成其成员的角色，不可拆装。

体系的核心命题包括：**反身性统摄**（整体如何构成成员角色）、**认知权**（定义什么可被认识、被言说、被想象的权力）、**生成逻辑**（先归纳、再推演，反例出现则框架升级，新框架保留旧框架的全部记录）、**非还原律**，以及形式化层 **MIA（数学信息公设）**。

## 目录结构

```
_config.yml     站点配置
_posts/         文章（Markdown，文件名格式 YYYY-MM-DD-标题.md）
_tabs/          固定页面（关于等）
_data/          站点数据（联系方式、分享项等）
assets/         图片与样式
_plugins/       构建扩展
tools/          发帖工具与辅助脚本
.zenodo.json    Zenodo 存档元数据
CITATION.cff    引用信息（GitHub「Cite this repository」按钮由此生成）
```

## 如何发布一篇新文章

```shell
cd C:\Users\R\Documents\GitHub\higher-science.github.io
python tools\new_post.py --title "文章标题" --file 草稿.md --push
```

不带 `--push` 只写本地不发布；`--dry` 预演；可选 `--categories` `--tags` `--desc` `--slug` `--date` `--pin`。
详见 `tools/如何发帖.md`。推送到 `main` 后 1–2 分钟自动上线。

## 存档与引用

每次在 GitHub 发布一个 Release，Zenodo 会自动存档该版本的源码快照并分配 DOI。
元数据写在 `.zenodo.json`（若同时存在 `CITATION.cff`，Zenodo 只读前者）。

（首次 Release 发布后，此处的 DOI 徽章与引用格式会补上。）

## 许可

本仓库包含两类内容，适用不同许可：

| 部分 | 内容 | 许可 |
|---|---|---|
| **原创内容** | 全部文章、术语表、站点正文与其他原创文本 | **CC BY 4.0**（署名即可自由传播、改编，含商业使用）　Copyright (c) 2026 朱瑞宇 (Ruiyu Zhu) |
| **站点主题与构建代码** | Jekyll / Chirpy 主题衍生部分 | **MIT**　Copyright (c) 2021 Cotes Chung　见 `LICENSE-MIT` |

CC BY 4.0 完整文本见 [`LICENSE`](LICENSE)；
人类可读摘要：<https://creativecommons.org/licenses/by/4.0/deed.zh>

---

*站点主题基于 [Chirpy](https://github.com/cotes2020/jekyll-theme-chirpy) 构建。*
