#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送财经报告到邮箱的独立脚本

用法示例：
  python scripts/send_email_report.py \
    --subject "📌 2025-10-14 财经新闻摘要" \
    --html-file output/latest_report.html \
    --text-file output/latest_report.txt

所需环境变量（推荐配置在 GitHub Secrets）：
  - SMTP_SERVER
  - SMTP_PORT
  - EMAIL_USERNAME
  - EMAIL_PASSWORD
  - EMAIL_FROM (可选，默认与 USERNAME 相同)
  - EMAIL_TO (逗号分隔)
"""

import argparse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    # Python-Markdown
    import markdown as md
except Exception:
    md = None


def build_html(markdown_text: str) -> str:
    """将Markdown渲染为带样式的HTML，若缺少依赖则做简易替换。"""
    if md:
        body = md.markdown(markdown_text, extensions=[
            'extra', 'admonition', 'codehilite', 'sane_lists', 'toc'
        ])
    else:
        # 兜底：极简替换，保证基本可读
        body = (markdown_text
                .replace('\n', '<br/>')
                .replace('**', '')
                )
    # 简洁邮件模板
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;line-height:1.6;color:#222;background:#f6f8fa;margin:0;padding:0;}}
    .container{{max-width:760px;margin:0 auto;background:#fff;padding:24px 24px 32px;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.06);}}
    h1,h2,h3{{color:#111;margin:16px 0 8px;}}
    h1{{font-size:22px}}
    h2{{font-size:18px;border-left:4px solid #6366f1;padding-left:8px;}}
    h3{{font-size:16px;color:#444;}}
    p,li{{font-size:14px;color:#333;}}
    a{{color:#2563eb;text-decoration:none;}}
    a:hover{{text-decoration:underline;}}
    hr{{border:none;border-top:1px solid #eee;margin:16px 0}}
    .footer{{color:#777;font-size:12px;margin-top:24px;text-align:center;}}
  </style>
  <title>Report</title>
  </head>
<body>
  <div class="container">{body}</div>
  <div class="footer">此邮件由 GitHub Actions 自动发送</div>
</body>
</html>
""".strip()


def send_email(subject: str, html_content: str, text_content: str) -> bool:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    from_email = os.getenv("EMAIL_FROM") or username
    to_raw = os.getenv("EMAIL_TO", "").strip()

    if not username or not password or not to_raw:
        print("❌ 邮件配置不完整，需设置: EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_TO")
        return False

    recipients = [e.strip() for e in to_raw.split(",") if e.strip()]
    if not recipients:
        print("❌ 收件人列表为空")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = username if '@' in (username or '') else from_email
        msg['To'] = ", ".join(recipients)

        # 构造HTML：优先使用提供的HTML；否则将文本Markdown渲染为HTML
        final_html = html_content
        if not final_html and text_content:
            final_html = build_html(text_content)

        # 若传入的HTML其实是Markdown痕迹，优先用text版本渲染
        if final_html and ('**' in final_html or '\n#' in final_html or '## ' in final_html):
            final_html = build_html(text_content or final_html)

        if text_content:
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        if final_html:
            msg.attach(MIMEText(final_html, 'html', 'utf-8'))

        server = None
        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.starttls()
            server.login(username, password)
            server.send_message(msg)
            print("✅ 邮件发送成功")
            return True
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='发送财经报告到邮箱')
    parser.add_argument('--subject', required=True, help='邮件主题')
    parser.add_argument('--html-file', help='HTML 内容文件路径')
    parser.add_argument('--text-file', help='纯文本内容文件路径')
    args = parser.parse_args()

    html_content = ''
    text_content = ''

    if args.html_file and Path(args.html_file).exists():
        html_content = Path(args.html_file).read_text(encoding='utf-8')
    if args.text_file and Path(args.text_file).exists():
        text_content = Path(args.text_file).read_text(encoding='utf-8')

    if not html_content and not text_content:
        print("❌ 未提供有效内容文件")
        return 1

    ok = send_email(args.subject, html_content, text_content)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())


