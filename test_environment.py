#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDUKY监控系统 - 测试脚本
用于验证所有依赖是否正确安装
"""

import sys
import os

def test_imports():
    """测试所有必要的导入"""
    print("正在测试Python依赖...")
    
    try:
        import flask
        print(f"✓ Flask: {flask.__version__}")
    except ImportError as e:
        print(f"✗ Flask导入失败: {e}")
        return False
    
    try:
        import flask_sqlalchemy
        print(f"✓ Flask-SQLAlchemy: {flask_sqlalchemy.__version__}")
    except ImportError as e:
        print(f"✗ Flask-SQLAlchemy导入失败: {e}")
        return False
    
    try:
        import requests
        print(f"✓ Requests: {requests.__version__}")
    except ImportError as e:
        print(f"✗ Requests导入失败: {e}")
        return False
    
    try:
        import apscheduler
        print(f"✓ APScheduler: {apscheduler.__version__}")
    except ImportError as e:
        print(f"✗ APScheduler导入失败: {e}")
        return False
    
    try:
        import bs4
        print(f"✓ BeautifulSoup4: {bs4.__version__}")
    except ImportError as e:
        print(f"✗ BeautifulSoup4导入失败: {e}")
        return False
    
    try:
        import telegram
        print(f"✓ python-telegram-bot: {telegram.__version__}")
    except ImportError as e:
        print(f"✗ python-telegram-bot导入失败: {e}")
        return False
    
    try:
        import lxml
        print(f"✓ lxml: {lxml.__version__}")
    except ImportError as e:
        print(f"✗ lxml导入失败: {e}")
        return False
    
    try:
        import werkzeug
        print(f"✓ Werkzeug: {werkzeug.__version__}")
    except ImportError as e:
        print(f"✗ Werkzeug导入失败: {e}")
        return False
    
    try:
        import pytz
        print(f"✓ pytz: {pytz.__version__}")
    except ImportError as e:
        print(f"✗ pytz导入失败: {e}")
        return False
    
    try:
        import ntplib
        print("✓ ntplib: 已安装")
    except ImportError as e:
        print(f"✗ ntplib导入失败: {e}")
        return False
    
    return True

def test_file_structure():
    """测试文件结构"""
    print("\n正在测试文件结构...")
    
    required_files = [
        'run_app.py',
        'app_v2_fixed.py',
        'requirements.txt',
        'web/templates',
        'web/static'
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist

def test_app_basic():
    """测试应用基本功能"""
    print("\n正在测试应用基本功能...")
    
    try:
        # 添加项目根目录到Python路径
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app_v2_fixed import app
        print("✓ 应用程序成功导入")
        
        # 测试应用配置
        with app.app_context():
            print("✓ 应用上下文正常")
            
        print("✓ 应用基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 应用测试失败: {e}")
        return False

def main():
    print("====================================")
    print("    EDUKY-Monitor 环境测试")
    print("====================================")
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {os.name}")
    print(f"当前目录: {os.getcwd()}")
    print("====================================")
    
    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)
    
    success = True
    
    # 测试导入
    if not test_imports():
        success = False
    
    # 测试文件结构
    if not test_file_structure():
        success = False
    
    # 测试应用
    if not test_app_basic():
        success = False
    
    print("\n====================================")
    if success:
        print("✓ 所有测试通过！环境配置正常")
        print("可以安全地运行 python run_app.py")
    else:
        print("✗ 测试失败！请检查上述错误")
        print("请安装缺失的依赖: pip install -r requirements.txt")
    print("====================================")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())