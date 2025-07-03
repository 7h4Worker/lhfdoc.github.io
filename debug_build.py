#!/usr/bin/env python3
"""
调试脚本：检查 teedoc 构建输出和路径配置
"""
import json
import os
import sys

def main():
    # 读取配置
    with open('site_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"Site name: {config['site_name']}")
    print(f"Site root URL: {config['site_root_url']}")
    print(f"Site domain: {config['site_domain']}")
    print(f"Site protocol: {config['site_protocol']}")
    
    # 计算输出目录
    site_root_url = config['site_root_url']
    out_dir = f"out{site_root_url}"
    
    print(f"\nExpected output directory: {out_dir}")
    print(f"Final URL should be: {config['site_protocol']}://{config['site_domain']}{site_root_url}")
    
    # 检查是否存在构建输出
    if os.path.exists(out_dir):
        print(f"\n✓ Output directory exists: {out_dir}")
        
        # 列出一些关键文件
        key_files = ['index.html', 'static/css', 'static/js']
        for file_path in key_files:
            full_path = os.path.join(out_dir, file_path)
            if os.path.exists(full_path):
                print(f"✓ Found: {full_path}")
            else:
                print(f"✗ Missing: {full_path}")
                
        # 检查 index.html 中的资源路径
        index_path = os.path.join(out_dir, 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if site_root_url in content:
                    print(f"✓ Found correct root URL '{site_root_url}' in index.html")
                else:
                    print(f"✗ Root URL '{site_root_url}' not found in index.html")
                    print("   This might indicate a path configuration issue")
    else:
        print(f"\n✗ Output directory does not exist: {out_dir}")
        print("   Run 'teedoc build' first")

if __name__ == "__main__":
    main()
