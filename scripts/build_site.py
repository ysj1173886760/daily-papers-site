#!/usr/bin/env python3
"""
网站构建脚本 - 生成静态HTML页面和RSS feed
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader
from feedgen.feed import FeedGenerator
import markdown

class SiteBuilder:
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.templates_dir = self.base_dir / "templates"
        self.output_dir = self.base_dir / "public"
        self.data_dir = self.base_dir / "data"
        
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "posts").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)
        
        # 初始化Jinja2
        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        # 加载配置
        self.config = self.load_config()
        
    def load_config(self):
        """加载网站配置"""
        config_file = self.base_dir / "config.yml"
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            # 默认配置
            return {
                "site": {
                    "title": "Daily AI Papers",
                    "description": "Latest papers in AI research",
                    "url": "https://your-username.github.io/daily-papers-site",
                    "author": "AI Research Team",
                    "build_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
    
    def load_papers_data(self):
        """加载论文数据"""
        papers_file = self.data_dir / "papers.json"
        if papers_file.exists():
            with open(papers_file) as f:
                return json.load(f)
        else:
            # 如果没有数据文件，返回空数据
            return {"posts": [], "stats": {"total_papers": 0, "categories_count": 0, "days_active": 0}}
    
    def build_index_page(self, data):
        """构建首页"""
        template = self.jinja_env.get_template("index.html")
        
        # 获取最近的文章
        recent_posts = sorted(
            data.get("posts", []), 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )[:10]
        
        html = template.render(
            site=self.config["site"],
            recent_posts=recent_posts,
            total_papers=data.get("stats", {}).get("total_papers", 0),
            categories_count=data.get("stats", {}).get("categories_count", 0),
            days_active=data.get("stats", {}).get("days_active", 0)
        )
        
        with open(self.output_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print("✓ 首页构建完成")
    
    def build_post_pages(self, data):
        """构建文章页面"""
        template = self.jinja_env.get_template("post.html")
        posts = data.get("posts", [])
        
        for i, post in enumerate(posts):
            # 设置前后文章导航
            prev_post = posts[i-1] if i > 0 else None
            next_post = posts[i+1] if i < len(posts)-1 else None
            
            html = template.render(
                site=self.config["site"],
                post=post,
                prev_post=prev_post,
                next_post=next_post
            )
            
            # 生成文件名
            filename = post.get("filename", f"post-{i}.html")
            with open(self.output_dir / "posts" / filename, "w", encoding="utf-8") as f:
                f.write(html)
        
        print(f"✓ {len(posts)} 个文章页面构建完成")
    
    def build_about_page(self):
        """构建关于页面"""
        template = self.jinja_env.get_template("about.html")
        
        html = template.render(site=self.config["site"])
        
        with open(self.output_dir / "about.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        print("✓ 关于页面构建完成")
    
    def build_rss_feed(self, data):
        """构建RSS feed"""
        fg = FeedGenerator()
        
        # 设置feed基本信息
        site_config = self.config["site"]
        fg.id(site_config["url"])
        fg.title(site_config["title"])
        fg.link(href=site_config["url"], rel='alternate')
        fg.link(href=f"{site_config['url']}/rss.xml", rel='self')
        fg.description(site_config["description"])
        fg.language('zh-cn')
        fg.lastBuildDate(datetime.now(timezone.utc))
        fg.managingEditor(f"{site_config.get('email', 'noreply@example.com')} ({site_config['author']})")
        
        # 添加文章条目
        posts = data.get("posts", [])
        for post in sorted(posts, key=lambda x: x.get("date", ""), reverse=True)[:50]:
            fe = fg.add_entry()
            
            post_url = f"{site_config['url']}{post.get('url', '')}"
            fe.id(post_url)
            fe.title(post.get("title", "Untitled"))
            fe.link(href=post_url)
            fe.description(post.get("excerpt", ""))
            
            # 解析日期
            try:
                post_date = datetime.strptime(post.get("date", ""), "%Y-%m-%d")
                fe.pubDate(post_date.replace(tzinfo=timezone.utc))
            except:
                fe.pubDate(datetime.now(timezone.utc))
            
            # 添加内容
            if post.get("content"):
                fe.content(post["content"], type='CDATA')
            
            # 添加分类
            if post.get("category"):
                fe.category({
                    "term": post["category"],
                    "scheme": "http://example.com/categories",
                    "label": post["category"]
                })
        
        # 保存RSS文件
        rss_str = fg.rss_str(pretty=True)
        with open(self.output_dir / "rss.xml", "wb") as f:
            f.write(rss_str)
        
        print("✓ RSS feed构建完成")
    
    def copy_assets(self):
        """复制静态资源"""
        import shutil
        
        assets_src = self.base_dir / "assets"
        assets_dst = self.output_dir / "assets"
        
        if assets_src.exists():
            if assets_dst.exists():
                shutil.rmtree(assets_dst)
            shutil.copytree(assets_src, assets_dst)
            print("✓ 静态资源复制完成")
    
    def build(self):
        """构建整个网站"""
        print("开始构建网站...")
        
        # 加载数据
        data = self.load_papers_data()
        
        # 构建各个页面
        self.build_index_page(data)
        self.build_post_pages(data)
        self.build_about_page()
        self.build_rss_feed(data)
        self.copy_assets()
        
        print("🎉 网站构建完成！")
        print(f"输出目录: {self.output_dir}")

def main():
    builder = SiteBuilder()
    builder.build()

if __name__ == "__main__":
    main()