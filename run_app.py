#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDUKY监控系统 - 应用启动器
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# 设置系统编码为UTF-8 (Windows兼容性)
if sys.platform.startswith('win'):
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except:
        pass

# 确保logs目录存在
os.makedirs('logs', exist_ok=True)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_v2_fixed import app, scheduler, logger

def setup_logging():
    """配置日志"""
    log_file = os.path.join('logs', 'app.log')
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

if __name__ == '__main__':
    print("🚀 启动 EDUKY 监控系统...")
    
    # 配置日志
    setup_logging()
    
    try:
        # 启动调度器
        if not scheduler.running:
            scheduler.start()
            logger.info("调度器已启动")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭系统...")
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
    finally:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("调度器已关闭")
        print("👋 EDUKY 监控系统已关闭")