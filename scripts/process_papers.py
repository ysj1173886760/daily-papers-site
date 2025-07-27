#!/usr/bin/env python3
"""
处理论文数据的脚本 - 接收主项目推送的数据并转换为网站格式
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import markdown

def process_papers_data(data_str):
    """处理从主项目推送的论文数据"""
    try:
        # 解析JSON数据
        incoming_data = json.loads(data_str)
        
        # 加载现有数据
        data_file = Path("data/papers.json")
        data_file.parent.mkdir(exist_ok=True)
        
        if data_file.exists():
            with open(data_file) as f:
                existing_data = json.load(f)
        else:
            existing_data = {"posts": [], "stats": {"total_papers": 0, "categories_count": 0, "days_active": 0}}
        
        # 处理新的论文数据
        new_posts = []
        for file_info in incoming_data.get("html_files", []):
            post = {
                "title": f"{file_info['date']} {file_info['category']} Papers ({file_info['papers_count']}篇)",
                "date": file_info['date'],
                "date_formatted": datetime.strptime(file_info['date'], "%Y-%m-%d").strftime("%Y年%m月%d日"),
                "category": file_info['category'],
                "papers_count": file_info['papers_count'],
                "url": file_info['url'],
                "filename": file_info['filename'],
                "excerpt": f"今日{file_info['category']}领域精选论文 {file_info['papers_count']} 篇，包含详细分析和关键洞察。",
                "tags": [file_info['category'], "AI Research", "arXiv"],
                "content": ""  # 这里可以添加处理后的内容
            }
            new_posts.append(post)
        
        # 合并数据（避免重复）
        existing_urls = {post["url"] for post in existing_data["posts"]}
        for post in new_posts:
            if post["url"] not in existing_urls:
                existing_data["posts"].append(post)
        
        # 按日期排序
        existing_data["posts"].sort(key=lambda x: x["date"], reverse=True)
        
        # 更新统计信息
        categories = set(post["category"] for post in existing_data["posts"])
        dates = set(post["date"] for post in existing_data["posts"])
        
        existing_data["stats"] = {
            "total_papers": sum(post["papers_count"] for post in existing_data["posts"]),
            "categories_count": len(categories),
            "days_active": len(dates)
        }
        
        # 保存更新后的数据
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 处理完成，新增 {len(new_posts)} 个条目")
        return True
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def create_sample_data():
    """创建示例数据用于测试"""
    sample_data = {
        "posts": [
            {
                "title": "2024-07-27 RAG Papers (3篇)",
                "date": "2024-07-27",
                "date_formatted": "2024年07月27日",
                "category": "RAG",
                "papers_count": 3,
                "url": "/posts/2024-07-27-rag.html",
                "filename": "2024-07-27-rag.html",
                "excerpt": "今日RAG领域精选论文 3 篇，包含详细分析和关键洞察。",
                "tags": ["RAG", "AI Research", "arXiv"],
                "content": "<h2>论文概述</h2><p>今日为您带来3篇RAG领域的前沿研究...</p>"
            },
            {
                "title": "2024-07-26 Knowledge Graph Papers (2篇)",
                "date": "2024-07-26",
                "date_formatted": "2024年07月26日",
                "category": "Knowledge Graph",
                "papers_count": 2,
                "url": "/posts/2024-07-26-kg.html",
                "filename": "2024-07-26-kg.html",
                "excerpt": "今日Knowledge Graph领域精选论文 2 篇，包含详细分析和关键洞察。",
                "tags": ["Knowledge Graph", "AI Research", "arXiv"],
                "content": "<h2>论文概述</h2><p>今日为您带来2篇知识图谱领域的前沿研究...</p>"
            }
        ],
        "stats": {
            "total_papers": 5,
            "categories_count": 2,
            "days_active": 2
        }
    }
    
    data_file = Path("data/papers.json")
    data_file.parent.mkdir(exist_ok=True)
    
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print("✓ 示例数据创建完成")

def main():
    parser = argparse.ArgumentParser(description='处理论文数据')
    parser.add_argument('--data', help='论文数据JSON字符串')
    parser.add_argument('--sample', action='store_true', help='创建示例数据')
    
    args = parser.parse_args()
    
    if args.sample:
        create_sample_data()
    elif args.data:
        process_papers_data(args.data)
    else:
        print("请提供 --data 参数或使用 --sample 创建示例数据")

if __name__ == "__main__":
    main()