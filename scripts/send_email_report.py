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

        if text_content:
            msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        if html_content:
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))

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


