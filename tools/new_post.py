#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发帖工具 · higher-science.github.io

把一份 Markdown 草稿变成一篇正式文章并（可选）推到线上。

用法示例
--------
1) 只生成文件，不发布：
   python tools/new_post.py --title "为什么知识越多越危险" --file 草稿.md --slug wei-shen-me

2) 生成并立即发布上线：
   python tools/new_post.py --title "为什么知识越多越危险" --file 草稿.md --slug wei-shen-me --push

3) 正文直接写在命令行里：
   python tools/new_post.py --title "短评：从组成走向生成" --body "正文……" --push

4) 预览会生成什么，不写盘：
   python tools/new_post.py --title "测试" --body "x" --dry

参数
----
  --title      文章标题（必填）
  --file       正文来源文件（.md / .txt，UTF-8）
  --body       正文（与 --file 二选一）
  --slug       网址用的英文短名（不填=用标题原文，网址会带中文）
  --date       发布日 YYYY-MM-DD（默认今天）
  --categories 分类，逗号分隔，如：科学,教育
  --tags       标签，逗号分隔
  --desc       摘要（不填=取正文前 80 字）
  --image      封面图路径（可选）
  --pin        置顶（可写 true 或 1-100 的排序号）
  --push       生成后自动提交并推送到 GitHub，约 1 分钟后自动上线
  --dry        只预览，不写文件
"""
import argparse
import datetime as dt
import io
import os
import re
import socket
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(REPO, '_posts')
REMOTE = 'origin'
BRANCH = 'main'
SITE = 'https://higher-science.github.io'
REPO_URL = 'https://github.com/higher-science/higher-science.github.io'


def log(*a):
    print(*a)


def find_proxy():
    """本机 Clash/代理端口（仅作最后兜底；直连优先）。"""
    for port in (26001, 7890, 7897):
        try:
            s = socket.create_connection(('127.0.0.1', port), timeout=0.6)
            s.close()
            return 'http://127.0.0.1:%d' % port
        except OSError:
            continue
    return None


# 清掉环境里的 HTTP(S)_PROXY：本机环境变量里的代理会把 git 带沟里（502/重置）。
# 推送必须直连 github.com，直连不通时改用 GitHub 官方备用 IP 指定解析。
_PROXY_KEYS = ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
               'http_proxy', 'https_proxy', 'all_proxy']
SPARE_IPS = ['140.82.114.3', '140.82.113.3', '140.82.112.3', '140.82.121.3']


def clean_env():
    env = dict(os.environ)
    for k in _PROXY_KEYS:
        env.pop(k, None)
    env['GIT_TERMINAL_PROMPT'] = '0'
    return env


def run_git(*args, extra=(), proxy=None, timeout=240):
    cmd = ['git', '-C', REPO]
    if proxy:
        cmd += ['-c', 'http.proxy=' + proxy]
    else:
        cmd += ['-c', 'http.proxy=']          # 显式关掉代理 -> 直连
    cmd += list(extra) + list(args)
    env = clean_env()
    if proxy:
        env['HTTPS_PROXY'] = proxy
        env['HTTP_PROXY'] = proxy
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       encoding='utf-8', errors='replace', env=env)
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def push_main(branch=BRANCH):
    """按 直连 -> 备用 IP -> 本机代理 的顺序推送，返回 (成功, 说明)。"""
    tries = [('直连', (), None)]
    for ip in SPARE_IPS:
        tries.append(('指定 IP %s' % ip,
                      ('-c', 'http.curloptResolve=github.com:443:%s' % ip), None))
    proxy = find_proxy()
    if proxy:
        tries.append(('代理 %s' % proxy, (), proxy))

    last = ''
    for label, extra, px in tries:
        try:
            rc, out = run_git('push', REMOTE, branch, extra=extra, proxy=px,
                              timeout=150)
        except subprocess.TimeoutExpired:
            log('  通道 %s 超时' % label)
            continue
        if rc == 0:
            return True, label
        last = out.replace('\n', ' ')
        log('  通道 %-18s 不通：%s' % (label, last[:110]))
    return False, last


def slugify(title):
    s = title.strip().lower()
    s = re.sub(r'[\\/:*?"<>|\s]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or 'post'


def first_sentence(text, n=80):
    t = re.sub(r'[#>*`\[\]\(\)]', '', text)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:n] + ('…' if len(t) > n else '')


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--file')
    ap.add_argument('--body')
    ap.add_argument('--slug')
    ap.add_argument('--date')
    ap.add_argument('--categories', default='')
    ap.add_argument('--tags', default='')
    ap.add_argument('--desc', default='')
    ap.add_argument('--image', default='')
    ap.add_argument('--pin', default='')
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    # 正文
    if a.file:
        if not os.path.exists(a.file):
            log('找不到正文文件：', a.file)
            return 2
        body = io.open(a.file, encoding='utf-8').read().strip()
    elif a.body:
        body = a.body.strip()
    else:
        log('请用 --file 或 --body 提供正文。')
        return 2

    date = a.date or dt.date.today().strftime('%Y-%m-%d')
    slug = a.slug or slugify(a.title)

    def yaml_list(raw):
        items = [x.strip() for x in raw.split(',') if x.strip()]
        return '[%s]' % ', '.join(items) if items else ''

    cats = yaml_list(a.categories)
    tags = yaml_list(a.tags)

    fm = ['---', 'layout: post', 'title: "%s"' % a.title.replace('"', '\\"'),
          'date: %s 09:00:00 +0800' % date]
    if cats:
        fm.append('categories: %s' % cats)
    if tags:
        fm.append('tags: %s' % tags)
    desc = a.desc or first_sentence(body)
    if desc:
        fm.append('description: "%s"' % desc.replace('"', '\\"'))
    if a.image:
        fm.append('image: %s' % a.image)
    if a.pin:
        fm.append('pin: %s' % a.pin)
    fm.append('---')

    content = '\n'.join(fm) + '\n\n' + body + '\n'
    fname = '%s-%s.md' % (date, slug)
    fpath = os.path.join(POSTS, fname)

    log('标题   ：', a.title)
    log('发布日 ：', date)
    log('文件名 ：', fname)
    log('网址   ：%s/posts/%s/' % (SITE, slug))
    log('字符数 ：', len(body))
    if a.dry:
        log('\n---- 预览（未写盘）----')
        log(content[:1200])
        return 0

    if not os.path.isdir(POSTS):
        log('!! 找不到 _posts 目录：', POSTS)
        return 1
    if os.path.exists(fpath):
        log('!! 已存在同名文件，未覆盖：', fpath)
        return 1
    io.open(fpath, 'w', encoding='utf-8', newline='\n').write(content)
    log('已写入：', fpath)

    if not a.push:
        log('\n（未发布。加 --push 即可自动提交并上线）')
        return 0

    rc, out = run_git('add', '-A')
    if rc:
        log('git add 失败：', out)
        return 1

    rc, out = run_git('commit', '-m', 'post: %s' % a.title)
    if rc:
        log('git commit 失败：', out)
        return 1
    log('提交   ：', out.splitlines()[0] if out else 'ok')

    rc, out = run_git('pull', '--rebase', REMOTE, BRANCH, timeout=120)
    if rc:
        log('（pull 未成功，继续尝试推送）：', out[:160])

    log('推送   ：按 直连 → 备用 IP → 本机代理 顺序试')
    ok, info = push_main(BRANCH)
    if not ok:
        log('!! 推送失败：', info[:300])
        log('文件已在本地保存（%s），可稍后重试 --push。' % fname)
        return 1
    log('推送成功（通道：%s）。' % info)
    log('约 1 分钟后上线：%s/posts/%s/' % (SITE, slug))
    log('构建进度：%s/actions' % REPO_URL)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
