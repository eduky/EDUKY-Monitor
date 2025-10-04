#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDUKY-商品监控系统
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import requests
import json
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os
import sqlite3
from threading import Lock
import pytz
import ntplib
import hashlib
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static',
            instance_path=os.path.join(os.path.dirname(__file__), 'web/instance'))
app.config['SECRET_KEY'] = 'your-secret-key-here-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(__file__), "web", "instance", "inventory_monitor_v2.db")}?check_same_thread=false'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 会话安全配置
from datetime import timedelta
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # 会话超时时间2小时
    SESSION_COOKIE_SECURE=False,  # 开发环境设为False，生产环境应设为True
    SESSION_COOKIE_HTTPONLY=True,  # 防止XSS攻击
    SESSION_COOKIE_SAMESITE='Lax',  # 防止CSRF攻击
)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 20,
    'pool_recycle': -1,
    'pool_pre_ping': True,
    'connect_args': {'check_same_thread': False, 'timeout': 30}
}

db = SQLAlchemy(app)

# 数据库锁
db_lock = Lock()

# 时区设置
CHINA_TZ = pytz.timezone('Asia/Shanghai')

# NTP服务器列表
NTP_SERVERS = [
    'time.windows.com',
    'pool.ntp.org', 
    'time.nist.gov',
    'cn.pool.ntp.org',
    'ntp.ntsc.ac.cn'
]

def get_internet_time():
    """获取互联网时间 (中国时区)"""
    for server in NTP_SERVERS:
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(server, version=3, timeout=5)
            utc_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
            china_time = utc_time.astimezone(CHINA_TZ)
            logger.info(f"成功从NTP服务器 {server} 获取时间: {china_time}")
            return china_time
        except Exception as e:
            logger.warning(f"从NTP服务器 {server} 获取时间失败: {e}")
            continue
    
    # 如果所有NTP服务器都失败，使用本地时间作为备用
    logger.warning("所有NTP服务器都不可用，使用本地时间")
    return datetime.now(CHINA_TZ)

def utc_to_china_time(utc_time):
    """将UTC时间转换为中国时间"""
    if utc_time is None:
        return None
    if utc_time.tzinfo is None:
        utc_time = pytz.utc.localize(utc_time)
    return utc_time.astimezone(CHINA_TZ)

def db_time_to_china_time(db_time):
    """将数据库中的时间（已经是中国时间）转换为带时区的中国时间"""
    if db_time is None:
        return None
    if db_time.tzinfo is None:
        # 数据库中存储的时间已经是中国时间，只需要添加时区信息
        return CHINA_TZ.localize(db_time)
    return db_time.astimezone(CHINA_TZ)

# 数据模型
class Product(db.Model):
    """商品模型"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    target_selector = db.Column(db.String(200), nullable=False)
    current_stock = db.Column(db.Integer, default=0)
    last_stock = db.Column(db.Integer, default=0)
    threshold = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    updated_at = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    buy_url = db.Column(db.String(500))
    
    # 添加版本控制字段
    version = db.Column(db.Integer, default=1)

class NotificationConfig(db.Model):
    """通知配置模型"""
    __tablename__ = 'notification_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_bot_token = db.Column(db.String(200))
    
    # 频道通知配置
    channel_enabled = db.Column(db.Boolean, default=False)
    channel_id = db.Column(db.String(100))
    
    # 群组通知配置
    group_enabled = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.String(100))
    
    # 个人通知配置
    personal_enabled = db.Column(db.Boolean, default=False)
    personal_chat_id = db.Column(db.String(100))
    
    # 用户通知配置（新字段，兼容前端）
    user_enabled = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.String(100))
    
    # 检测间隔设置
    check_interval = db.Column(db.Integer, default=120)  # 默认120秒
    
    # 通知类型开关
    restock_enabled = db.Column(db.Boolean, default=True)
    sale_enabled = db.Column(db.Boolean, default=True)
    
    # 通知模板配置
    template_restock = db.Column(db.Text, default="🎉 补货通知\n📦 商品名称: {product_name}\n📈 补货数量: {stock_difference}\n📊 当前库存: {current_stock}")
    template_sale = db.Column(db.Text, default="🎉 销售通知\n📦 商品名称: {product_name}\n📈 被购买: {stock_difference}\n📊 剩余库存: {current_stock}")
    
    created_at = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    updated_at = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))

class StockHistory(db.Model):
    """库存历史记录"""
    __tablename__ = 'stock_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stock_count = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False, default=0)  # 记录变化前的库存
    timestamp = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    change_type = db.Column(db.String(20))  # increase, decrease
    
    product = db.relationship('Product', backref=db.backref('stock_histories', lazy=True))

class NotificationLog(db.Model):
    """通知日志"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='sent')
    timestamp = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    
    product = db.relationship('Product', backref=db.backref('notification_logs', lazy=True))

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: get_internet_time().replace(tzinfo=None))
    last_login = db.Column(db.DateTime)
    must_change_password = db.Column(db.Boolean, default=True)  # 强制修改密码标记
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def check_password(self, password):
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

# 登录相关配置
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'

# 登录装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': '请先登录', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        
        # 检查会话是否过期
        if 'login_time' in session:
            login_time = session['login_time']
            if isinstance(login_time, str):
                login_time = datetime.fromisoformat(login_time)
            # 检查是否超过2小时
            if datetime.now() - login_time > timedelta(hours=2):
                session.clear()
                flash('会话已过期，请重新登录', 'warning')
                if request.is_json:
                    return jsonify({'success': False, 'message': '会话已过期，请重新登录', 'redirect': '/login'}), 401
                return redirect(url_for('login'))
        
        # 检查用户是否需要强制修改密码（除了修改密码页面本身）
        if f.__name__ != 'change_password':
            user = db.session.get(User, session['user_id'])
            if user and user.must_change_password:
                flash('首次登录需要修改默认密码', 'warning')
                if request.is_json:
                    return jsonify({'success': False, 'message': '首次登录需要修改默认密码', 'redirect': '/change_password'}), 302
                return redirect(url_for('change_password'))
        
        return f(*args, **kwargs)
    return decorated_function

def init_default_user():
    """初始化默认管理员用户"""
    try:
        with app.app_context():
            # 检查是否已存在用户
            if User.query.first() is None:
                admin = User(username=DEFAULT_ADMIN_USERNAME)
                admin.set_password(DEFAULT_ADMIN_PASSWORD)
                admin.must_change_password = True  # 强制修改默认密码
                db.session.add(admin)
                db.session.commit()
                logger.info(f"创建默认管理员账户: {DEFAULT_ADMIN_USERNAME} (需要强制修改密码)")
    except Exception as e:
        logger.error(f"初始化默认用户失败: {e}")

# 库存监控类 - 重构版
class InventoryMonitorV2:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def check_stock(self, product):
        """检查单个商品库存 - 改进版"""
        try:
            logger.info(f"开始检查商品库存: {product.name}")
            
            response = self.session.get(product.url, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据CSS选择器获取库存数量
            stock_element = soup.select_one(product.target_selector)
            
            if stock_element:
                import re
                stock_text = stock_element.get_text(strip=True)
                logger.info(f"提取到库存文本: '{stock_text}'")
                
                # 提取数字
                numbers = re.findall(r'\d+', stock_text)
                current_stock = int(numbers[0]) if numbers else 0
                
                logger.info(f"解析库存数量: {current_stock}")
                return current_stock
            else:
                logger.warning(f"未找到库存元素: {product.target_selector}")
                return 0
                
        except Exception as e:
            logger.error(f"检查商品 {product.name} 库存失败: {str(e)}")
            return None

    def test_selector(self, product):
        """测试CSS选择器 - 返回详细信息用于API"""
        try:
            logger.info(f"开始检查商品库存: {product.name}")
            
            response = self.session.get(product.url, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据CSS选择器获取库存数量
            stock_element = soup.select_one(product.target_selector)
            
            if stock_element:
                import re
                stock_text = stock_element.get_text(strip=True)
                logger.info(f"提取到库存文本: '{stock_text}'")
                
                # 提取数字
                numbers = re.findall(r'\d+', stock_text)
                current_stock = int(numbers[0]) if numbers else 0
                
                logger.info(f"解析库存数量: {current_stock}")
                return {
                    'success': True,
                    'stock_count': current_stock,
                    'extracted_text': stock_text
                }
            else:
                logger.warning(f"未找到库存元素: {product.target_selector}")
                return {
                    'success': False,
                    'error': f"未找到匹配的元素: {product.target_selector}",
                    'details': '请检查CSS选择器是否正确'
                }
                
        except Exception as e:
            logger.error(f"检查商品 {product.name} 库存失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'details': '请检查URL是否正确且网站可以访问'
            }

    def update_stock_safe(self, product_id, new_stock):
        """安全更新商品库存 - 使用数据库锁"""
        with db_lock:
            try:
                with app.app_context():
                    # 重新获取最新的产品数据
                    product = Product.query.filter_by(id=product_id).first()
                    if not product:
                        logger.error(f"产品ID {product_id} 不存在")
                        return False, None, None
                    
                    old_stock = product.current_stock
                    
                    logger.info(f"库存更新: {product.name} - 旧库存: {old_stock}, 新库存: {new_stock}")
                    
                    # 更新库存信息
                    product.last_stock = old_stock
                    product.current_stock = new_stock
                    product.updated_at = get_internet_time().replace(tzinfo=None)
                    product.version += 1  # 版本控制
                    
                    # 确定变化类型并只在有变化时记录历史
                    stock_changed = (old_stock != new_stock)
                    if stock_changed:
                        if new_stock > old_stock:
                            change_type = "increase"
                        elif new_stock < old_stock:
                            change_type = "decrease"
                        
                        # 只在库存变化时记录历史
                        history = StockHistory(
                            product_id=product.id,
                            stock_count=new_stock,
                            previous_stock=old_stock,
                            change_type=change_type
                        )
                        db.session.add(history)
                        logger.info(f"库存历史记录: {product.name} {change_type} - {old_stock} → {new_stock}")
                    else:
                        logger.debug(f"库存无变化，跳过历史记录: {product.name} - {new_stock}")
                    
                    # 提交事务
                    db.session.commit()
                    
                    logger.info(f"库存更新成功: {product.name}, 是否变化: {stock_changed}")
                    
                    return stock_changed, old_stock, new_stock
                    
            except Exception as e:
                logger.error(f"库存更新失败: 产品ID {product_id}, 错误: {e}")
                try:
                    db.session.rollback()
                except:
                    pass
                return False, None, None

# Telegram通知类 - 改进版
class TelegramNotifierV2:
    def __init__(self):
        pass
    
    def should_send_notification(self, old_stock, new_stock):
        """判断是否应该发送通知 - 简化版本"""
        
        # 计算库存变化
        stock_difference = new_stock - old_stock
        
        logger.info(f"通知判断: 旧库存={old_stock}, 新库存={new_stock}, 差值={stock_difference}")
        
        # 无变化不通知
        if stock_difference == 0:
            logger.info("不触发通知: 库存无变化")
            return False, None, stock_difference
        
        # 补货通知：库存增加
        if stock_difference > 0:
            logger.info(f"触发条件: 库存增加 +{stock_difference} (补货通知)")
            return True, "restock", stock_difference
        
        # 销售通知：库存减少
        elif stock_difference < 0:
            logger.info(f"触发条件: 库存减少 {stock_difference} (销售通知)")
            return True, "sale", abs(stock_difference)
        
        # 理论上不会到达这里
        logger.info("不触发通知: 未知情况")
        return False, None, stock_difference

    def send_notification(self, config, product, notification_type, stock_difference):
        """发送通知"""
        if not config or not config.telegram_bot_token:
            logger.warning("未配置Telegram Bot Token")
            return

        # 强制刷新 product，确保 current_stock 是最新
        with app.app_context():
            latest_product = Product.query.filter_by(id=product.id).first()
            if latest_product:
                product = latest_product

        # 检查通知类型开关（向后兼容）
        restock_enabled = getattr(config, 'restock_enabled', True)
        sale_enabled = getattr(config, 'sale_enabled', True)

        if notification_type == "restock" and not restock_enabled:
            logger.info("补货通知已禁用，跳过发送")
            return
        elif notification_type == "sale" and not sale_enabled:
            logger.info("销售通知已禁用，跳过发送")
            return

        try:
            message = self.format_message(product, notification_type, stock_difference)

            # 记录通知日志
            self._log_notification(product, notification_type, message, "attempting")

            # 发送到各个渠道
            sent_count = 0

            if config.channel_enabled and config.channel_id:
                if self._send_to_chat(config.telegram_bot_token, config.channel_id, message, product):
                    sent_count += 1

            if config.group_enabled and config.group_id:
                if self._send_to_chat(config.telegram_bot_token, config.group_id, message, product):
                    sent_count += 1

            if config.personal_enabled and config.personal_chat_id:
                if self._send_to_chat(config.telegram_bot_token, config.personal_chat_id, message, product):
                    sent_count += 1

            # 新的用户通知字段（兼容性）
            if hasattr(config, 'user_enabled') and hasattr(config, 'user_id') and config.user_enabled and config.user_id:
                if self._send_to_chat(config.telegram_bot_token, config.user_id, message, product):
                    sent_count += 1

            if sent_count > 0:
                self._log_notification(product, notification_type, message, "sent")
                logger.info(f"通知发送成功: {product.name}, 发送到 {sent_count} 个渠道")
            else:
                self._log_notification(product, notification_type, message, "failed")
                logger.error(f"通知发送失败: {product.name}, 没有可用渠道")

        except Exception as e:
            logger.error(f"发送通知异常: {product.name}, 错误: {e}")
            self._log_notification(product, notification_type, str(e), "error")

    def _send_to_chat(self, bot_token, chat_id, message, product):
        """发送消息到指定聊天，支持内联按钮"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            # 添加内联键盘按钮
            inline_keyboard = []
            
            # 购买按钮
            if product.buy_url:
                buy_button = [{
                    "text": "🛒 前往购买",
                    "url": product.buy_url
                }]
                inline_keyboard.append(buy_button)
            
            # 如果有按钮，添加到请求数据
            if inline_keyboard:
                reply_markup = {
                    "inline_keyboard": inline_keyboard
                }
                data['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                logger.info(f"消息发送成功到 {chat_id}")
                return True
            else:
                logger.error(f"Telegram API错误: {result}")
                return False
                
        except Exception as e:
            logger.error(f"发送消息到 {chat_id} 失败: {e}")
            return False

    def _log_notification(self, product, notification_type, message, status):
        """记录通知日志"""
        try:
            with db_lock:
                with app.app_context():
                    log = NotificationLog(
                        product_id=product.id,
                        notification_type=notification_type,
                        message=message,
                        status=status
                    )
                    db.session.add(log)
                    db.session.commit()
        except Exception as e:
            logger.error(f"记录通知日志失败: {e}")
            try:
                db.session.rollback()
            except:
                pass

    def format_message(self, product, notification_type, stock_difference):
        """使用模板格式化通知消息"""
        current_time = get_internet_time().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取通知配置和模板
        config = NotificationConfig.query.first()
        if not config:
            # 使用默认模板
            return self._format_default_message(product, notification_type, stock_difference, current_time)
        
        # 准备模板变量
        template_vars = {
            'product_name': product.name,
            'current_stock': product.current_stock,
            'previous_stock': product.last_stock,
            'stock_difference': stock_difference,
            'check_time': current_time,
            'product_url': product.url,
            'buy_url': product.buy_url or product.url
        }
        
        # 根据通知类型选择模板
        if notification_type == "restock":
            # 补货通知：库存增加
            template = getattr(config, 'template_restock', 
                             getattr(config, 'template_in_stock', 
                                   '🎉补货通知:\n\n📦 商品名称: {product_name}\n📈 补货数量: {stock_difference} 件\n📦 当前库存: {current_stock} 件\n\n🛒 前往购买：{buy_url}'))
        elif notification_type == "sale":
            # 销售通知：库存减少
            template = getattr(config, 'template_sale', 
                             getattr(config, 'template_out_of_stock', 
                                   '🎉销售通知:\n\n📦 商品名称: {product_name}\n📈 被购买: {stock_difference} 件\n📦 剩余库存: {current_stock} 件\n\n🛒 前往购买：{buy_url}'))
        else:
            # 默认使用补货模板
            template = getattr(config, 'template_restock', 
                             getattr(config, 'template_in_stock', 
                                   '🎉补货通知:\n\n📦 商品名称: {product_name}\n📈 补货数量: {stock_difference} 件\n📦 当前库存: {current_stock} 件\n\n🛒 前往购买：{buy_url}'))
        
        try:
            # 使用模板格式化消息
            message = template.format(**template_vars)
            return message
        except Exception as e:
            logger.error(f"模板格式化失败: {e}")
            # 使用内置默认模板作为后备
            if notification_type == "restock":
                return f"📦 补货通知\n\n【{product.name}】补货 {stock_difference} 件\n\n📦 当前库存：{product.current_stock} 件\n🕐 检测时间：{current_time}" + (f"\n\n🛒 前往购买：{product.buy_url}" if product.buy_url else "")
            elif notification_type == "sale":
                return f"🛒 销售通知\n\n【{product.name}】被购买 {stock_difference} 件\n\n📦 当前库存：{product.current_stock} 件\n🕐 检测时间：{current_time}" + (f"\n\n🛒 前往购买：{product.buy_url}" if product.buy_url else "")
            else:
                return f"📊 【{product.name}】库存变化\n\n📦 当前库存：{product.current_stock} 件\n📊 变化数量：{stock_difference:+d}\n\n🕐 检测时间：{current_time}" + (f"\n\n🛒 前往购买：{product.buy_url}" if product.buy_url else "")
    
    def _format_default_message(self, product, notification_type, stock_difference, current_time):
        """默认消息格式"""
        if notification_type == "restock":
            message = f"🎉 补货通知\n📦 商品名称: {product.name}\n📈 补货数量: {stock_difference}\n📊 当前库存: {product.current_stock}"
        elif notification_type == "sale":
            message = f"🎉 销售通知\n📦 商品名称: {product.name}\n📈 被购买: {abs(stock_difference)}\n📊 剩余库存: {product.current_stock}"
        else:
            # 兼容旧的通知类型
            message = f"🎉 库存变化\n📦 商品名称: {product.name}\n📊 当前库存: {product.current_stock}\n📈 变化数量: {stock_difference}"
        
        # 不在消息文本中添加购买链接，因为会通过按钮显示
        return message

# 全局对象
monitor = InventoryMonitorV2()
notifier = TelegramNotifierV2()
scheduler = BackgroundScheduler()

def send_telegram_notification(message, chat_id, bot_token):
    """发送Telegram通知的辅助函数"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            return True
        else:
            logger.error(f"Telegram API错误: {result}")
            return False
            
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        return False

def monitor_all_products_v2():
    """监控所有商品 - 重构版本"""
    current_time = get_internet_time().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"========== 开始新一轮监控 [{current_time}] ==========")
    
    try:
        with app.app_context():
            products = Product.query.filter_by(is_active=True).all()
            config = NotificationConfig.query.first()
            
            logger.info(f"活跃商品数量: {len(products)}")
            logger.info(f"通知配置状态: {'已配置' if config and config.telegram_bot_token else '未配置'}")
            
            for product in products:
                try:
                    logger.info(f"--- 检查商品: {product.name} ---")
                    
                    # 检查新库存
                    new_stock = monitor.check_stock(product)
                    
                    if new_stock is not None:
                        # 安全更新库存
                        stock_changed, old_stock, updated_new_stock = monitor.update_stock_safe(product.id, new_stock)
                        
                        if stock_changed and config:
                            # 判断是否需要发送通知
                            should_notify, notification_type, stock_difference = notifier.should_send_notification(old_stock, updated_new_stock)
                            
                            if should_notify:
                                logger.info(f"准备发送通知: {notification_type}")
                                notifier.send_notification(config, product, notification_type, stock_difference)
                            else:
                                logger.info("不需要发送通知")
                        else:
                            if not stock_changed:
                                logger.info("库存无变化，跳过通知")
                            if not config:
                                logger.info("未配置通知，跳过")
                    else:
                        logger.warning(f"无法获取 {product.name} 的库存信息")
                        
                except Exception as e:
                    logger.error(f"处理商品 {product.name} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 商品间添加延迟
                time.sleep(1)
                
    except Exception as e:
        logger.error(f"监控过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info(f"========== 监控轮次结束 [{get_internet_time().strftime('%Y-%m-%d %H:%M:%S')}] ==========")

# 动态更新调度器
def update_scheduler_v2():
    """更新调度器间隔"""
    try:
        with app.app_context():
            config = NotificationConfig.query.first()
            # 现在check_interval直接存储秒数
            interval_seconds = config.check_interval if config and config.check_interval else 120
        
        # 移除现有任务
        try:
            scheduler.remove_job('monitor_job_v2')
        except:
            pass
            
        # 添加新任务 - 使用秒级精度
        scheduler.add_job(
            func=monitor_all_products_v2,
            trigger="interval",
            seconds=interval_seconds,
            id='monitor_job_v2'
        )
        logger.info(f"调度器已更新，检测间隔：{interval_seconds}秒")
    except Exception as e:
        logger.error(f"更新调度器失败: {e}")

# 模板过滤器
@app.template_filter('china_time')
def china_time_filter(dt):
    """将UTC时间转换为中国时间的模板过滤器"""
    if dt is None:
        return ''
    # 假设数据库中的时间是UTC时间，转换为中国时间
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    china_time = dt.astimezone(CHINA_TZ)
    return china_time.strftime('%Y-%m-%d %H:%M:%S')

@app.template_filter('china_time_short')
def china_time_short_filter(dt):
    """将UTC时间转换为中国时间的短格式模板过滤器"""
    if dt is None:
        return ''
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    china_time = dt.astimezone(CHINA_TZ)
    return china_time.strftime('%m-%d %H:%M')

# 路由定义

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            # 设置永久会话以启用超时控制
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['login_time'] = datetime.now().isoformat()
            
            # 更新最后登录时间
            user.last_login = get_internet_time().replace(tzinfo=None)
            db.session.commit()
            
            logger.info(f"用户登录成功: {username}")
            
            # 如果是默认用户且需要修改密码，重定向到修改密码页面
            if user.must_change_password:
                flash('首次登录需要修改默认密码', 'warning')
                return redirect(url_for('change_password'))
            
            # 重定向到原来要访问的页面或首页
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('用户名或密码错误', 'error')
            logger.warning(f"用户登录失败: {username}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户注销"""
    username = session.get('username', '未知用户')
    session.clear()
    logger.info(f"用户注销: {username}")
    flash('已成功注销', 'success')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证输入
        if not current_password or not new_password or not confirm_password:
            flash('所有字段都必须填写', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('新密码和确认密码不匹配', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('新密码长度不能少于6位', 'error')
            return render_template('change_password.html')
        
        if new_password == current_password:
            flash('新密码不能与当前密码相同', 'error')
            return render_template('change_password.html')
        
        # 验证当前密码
        user = db.session.get(User, session['user_id'])
        if not user or not user.check_password(current_password):
            flash('当前密码错误', 'error')
            return render_template('change_password.html')
        
        # 更新密码
        user.set_password(new_password)
        user.must_change_password = False  # 清除强制修改密码标记
        db.session.commit()
        
        flash('密码修改成功', 'success')
        logger.info(f"用户 {user.username} 修改密码成功")
        
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/api/check_session', methods=['GET'])
def check_session():
    """检查会话状态API"""
    if 'user_id' not in session:
        return jsonify({'valid': False, 'message': '未登录'})
    
    # 检查会话是否过期
    if 'login_time' in session:
        login_time = session['login_time']
        if isinstance(login_time, str):
            login_time = datetime.fromisoformat(login_time)
        
        elapsed = datetime.now() - login_time
        total_minutes = int(elapsed.total_seconds() / 60)
        remaining_minutes = 120 - total_minutes  # 2小时 = 120分钟
        
        if elapsed > timedelta(hours=2):
            session.clear()
            return jsonify({'valid': False, 'message': '会话已过期'})
        
        return jsonify({
            'valid': True,
            'remaining_minutes': max(0, remaining_minutes),
            'elapsed_minutes': total_minutes
        })
    
    return jsonify({'valid': True, 'remaining_minutes': 120})

@app.route('/api/change_password', methods=['POST'])
@login_required
def api_change_password():
    """修改密码API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据格式错误'}), 400
        
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        # 验证输入
        if not current_password or not new_password:
            return jsonify({'success': False, 'message': '请填写所有字段'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度不能少于6位'}), 400
        
        # 获取当前用户
        user_id = session.get('user_id')
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        # 验证当前密码
        if not user.check_password(current_password):
            return jsonify({'success': False, 'message': '当前密码错误'}), 400
        
        # 设置新密码
        user.set_password(new_password)
        
        with db_lock:
            db.session.commit()
        
        logger.info(f"用户 {user.username} 成功修改密码")
        return jsonify({'success': True, 'message': '密码修改成功'})
        
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return jsonify({'success': False, 'message': f'系统错误: {str(e)}'}), 500

@app.route('/')
@login_required
def index():
    """主页"""
    products = Product.query.all()
    config = NotificationConfig.query.first()
    
    # 调试日志 - 检查个人通知配置
    if config:
        logger.info(f"首页加载 - 个人通知配置: user_enabled={getattr(config, 'user_enabled', 'N/A')}, user_id={getattr(config, 'user_id', 'N/A')}, personal_enabled={getattr(config, 'personal_enabled', 'N/A')}")
    
    return render_template('index.html', products=products, config=config)

@app.route('/debug/config')
def debug_config():
    """调试配置信息"""
    config = NotificationConfig.query.first()
    if not config:
        return "没有配置记录"
    
    debug_info = {
        'telegram_bot_token': bool(config.telegram_bot_token),
        'channel_enabled': getattr(config, 'channel_enabled', 'N/A'),
        'channel_id': getattr(config, 'channel_id', 'N/A'),
        'group_enabled': getattr(config, 'group_enabled', 'N/A'), 
        'group_id': getattr(config, 'group_id', 'N/A'),
        'personal_enabled': getattr(config, 'personal_enabled', 'N/A'),
        'personal_chat_id': getattr(config, 'personal_chat_id', 'N/A'),
        'user_enabled': getattr(config, 'user_enabled', 'N/A'),
        'user_id': getattr(config, 'user_id', 'N/A'),
    }
    
    return f"<pre>{str(debug_info)}</pre>"

@app.route('/products')
@login_required
def products():
    """商品管理页面"""
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/api/test_selector', methods=['POST'])
@login_required
def test_selector():
    """测试CSS选择器"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        selector = data.get('selector', '').strip()
        
        if not url or not selector:
            return jsonify({
                'success': False,
                'error': 'URL和CSS选择器不能为空'
            })
        
        # 验证URL格式
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({
                'success': False,
                'error': 'URL格式无效'
            })
        
        # 使用监控类测试选择器
        monitor = InventoryMonitorV2()
        
        # 创建临时Product对象用于测试
        temp_product = type('TempProduct', (), {
            'name': '测试商品',
            'url': url,
            'target_selector': selector,
            'id': 0
        })()
        
        # 测试库存检查
        result = monitor.test_selector(temp_product)
        
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"测试CSS选择器失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '测试过程中发生错误，请检查URL和选择器'
        }), 500

@app.route('/api/get_page_title', methods=['POST'])
@login_required
def get_page_title():
    """获取网页标题作为商品名称"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL不能为空'
            })
        
        # 验证URL格式
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return jsonify({
                'success': False,
                'error': 'URL格式无效'
            })
        
        # 获取网页标题
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 获取标题
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                
                # 清理标题（移除常见的网站后缀）
                common_suffixes = [
                    ' - 淘宝网', ' - 天猫', ' - 京东', ' - 拼多多', 
                    ' - 小红书', ' - 1688', ' - 苏宁易购',
                    '【图片 价格 品牌 报价】', '【价格 图片 品牌 报价】'
                ]
                
                for suffix in common_suffixes:
                    if title.endswith(suffix):
                        title = title[:-len(suffix)].strip()
                
                # 限制标题长度
                if len(title) > 50:
                    title = title[:50] + '...'
                
                return jsonify({
                    'success': True,
                    'title': title
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '无法获取网页标题'
                })
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '请求超时，请检查URL是否正确'
            })
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'无法访问网页: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f"获取网页标题失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取标题失败，请手动输入'
        }), 500

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    """添加商品"""
    if request.method == 'POST':
        url = request.form['url']
        buy_url = request.form.get('buy_url', '').strip()
        if not buy_url:  # 如果购买链接为空，默认使用监控URL
            buy_url = url
            
        product = Product(
            name=request.form['name'],
            url=url,
            target_selector=request.form['target_selector'],
            threshold=int(request.form.get('threshold', 1)),
            buy_url=buy_url
        )
        db.session.add(product)
        db.session.commit()
        flash('商品添加成功!', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """编辑商品"""
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.url = request.form['url']
        product.target_selector = request.form['target_selector']
        product.threshold = int(request.form.get('threshold', 1))
        
        # 如果购买链接为空，默认使用监控URL
        buy_url = request.form.get('buy_url', '').strip()
        if not buy_url:
            buy_url = product.url
        product.buy_url = buy_url
        
        product.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('商品更新成功!', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    """删除商品"""
    product = Product.query.get_or_404(id)
    
    # 删除相关的历史记录和通知日志
    StockHistory.query.filter_by(product_id=id).delete()
    NotificationLog.query.filter_by(product_id=id).delete()
    
    db.session.delete(product)
    db.session.commit()
    
    flash('商品删除成功!', 'success')
    return redirect(url_for('products'))

@app.route('/api/stock_history/<int:product_id>')
@login_required
def get_stock_history(product_id):
    """获取商品库存历史"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # 获取最近30条历史记录
        histories = StockHistory.query.filter_by(product_id=product_id)\
            .order_by(StockHistory.timestamp.desc())\
            .limit(30).all()
        
        # 格式化历史数据
        history_data = []
        for history in histories:
            history_data.append({
                'id': history.id,
                'stock_count': history.stock_count,
                'timestamp': db_time_to_china_time(history.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'change_type': history.change_type or 'unknown'
            })
        
        return jsonify({
            'success': True,
            'product_name': product.name,
            'histories': history_data
        })
        
    except Exception as e:
        logger.error(f"获取库存历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """设置页面"""
    config = NotificationConfig.query.first()
    if not config:
        config = NotificationConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.telegram_bot_token = request.form['telegram_bot_token']
        
        config.channel_enabled = 'channel_enabled' in request.form
        config.channel_id = request.form['channel_id']
        
        config.group_enabled = 'group_enabled' in request.form
        config.group_id = request.form['group_id']
        
        config.user_enabled = 'user_enabled' in request.form
        config.user_id = request.form['user_id']
        
        # 调试日志
        logger.info(f"保存个人通知设置: user_enabled={config.user_enabled}, user_id={config.user_id}")
        
        # 检测间隔设置（前端传入秒数，直接以秒为单位存储）
        try:
            interval_seconds = int(request.form.get('check_interval', 120))
            if interval_seconds < 10:
                interval_seconds = 10
            elif interval_seconds > 3600:
                interval_seconds = 3600
            # 直接以秒为单位存储
            config.check_interval = interval_seconds
        except:
            config.check_interval = 120
        
        # 通知类型开关（向后兼容）
        if hasattr(config, 'restock_enabled'):
            config.restock_enabled = 'restock_enabled' in request.form
        if hasattr(config, 'sale_enabled'):
            config.sale_enabled = 'sale_enabled' in request.form
        
        # 通知模板设置（向后兼容）
        if hasattr(config, 'template_restock'):
            config.template_restock = request.form.get('template_restock', getattr(config, 'template_restock', ''))
        if hasattr(config, 'template_sale'):
            config.template_sale = request.form.get('template_sale', getattr(config, 'template_sale', ''))
        
        config.updated_at = get_internet_time().replace(tzinfo=None)
        
        db.session.commit()
        
        # 更新调度器间隔
        update_scheduler_v2()
        
        flash('设置保存成功!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', config=config)

@app.route('/api/export_data', methods=['GET'])
@login_required
def export_data():
    """导出所有数据"""
    try:
        with app.app_context():
            # 导出商品数据
            products = Product.query.all()
            products_data = []
            for p in products:
                products_data.append({
                    'name': p.name,
                    'url': p.url,
                    'target_selector': p.target_selector,
                    'current_stock': p.current_stock,
                    'last_stock': p.last_stock,
                    'threshold': p.threshold,
                    'is_active': p.is_active,
                    'buy_url': p.buy_url,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                    'updated_at': p.updated_at.isoformat() if p.updated_at else None
                })
            
            # 导出通知配置数据
            config = NotificationConfig.query.first()
            config_data = None
            if config:
                config_data = {
                    'telegram_bot_token': config.telegram_bot_token,
                    'channel_enabled': config.channel_enabled,
                    'channel_id': config.channel_id,
                    'group_enabled': config.group_enabled,
                    'group_id': config.group_id,
                    'personal_enabled': config.personal_enabled,
                    'personal_chat_id': config.personal_chat_id,
                    'user_enabled': getattr(config, 'user_enabled', False),
                    'user_id': getattr(config, 'user_id', ''),
                    'check_interval': config.check_interval,
                    'restock_enabled': getattr(config, 'restock_enabled', True),
                    'sale_enabled': getattr(config, 'sale_enabled', True),
                    'template_restock': getattr(config, 'template_restock', ''),
                    'template_sale': getattr(config, 'template_sale', '')
                }
            
            # 导出库存历史数据（最近1000条）
            histories = StockHistory.query.order_by(StockHistory.timestamp.desc()).limit(1000).all()
            histories_data = []
            for h in histories:
                histories_data.append({
                    'product_name': h.product.name if h.product else 'Unknown',
                    'stock_count': h.stock_count,
                    'timestamp': h.timestamp.isoformat() if h.timestamp else None,
                    'change_type': h.change_type
                })
            
            # 组装导出数据
            export_data = {
                'export_info': {
                    'export_time': get_internet_time().isoformat(),
                    'version': '2.0',
                    'app_name': 'EDUKY-商品监控系统'
                },
                'products': products_data,
                'notification_config': config_data,
                'stock_histories': histories_data
            }
            
            return jsonify({
                'success': True,
                'data': export_data,
                'message': f'成功导出 {len(products_data)} 个商品和相关配置'
            })
            
    except Exception as e:
        logger.error(f"数据导出失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导出失败: {str(e)}'
        }), 500

@app.route('/api/import_data', methods=['POST'])
@login_required
def import_data():
    """导入数据"""
    try:
        if 'backup_file' not in request.files:
            return jsonify({
                'success': False,
                'message': '请选择备份文件'
            }), 400
            
        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '请选择备份文件'
            }), 400
            
        if not file.filename.endswith('.json'):
            return jsonify({
                'success': False,
                'message': '请选择JSON格式的备份文件'
            }), 400
        
        # 读取并解析文件
        file_content = file.read().decode('utf-8')
        import_data = json.loads(file_content)
        
        # 验证数据格式
        if 'products' not in import_data or 'notification_config' not in import_data:
            return jsonify({
                'success': False,
                'message': '备份文件格式不正确'
            }), 400
        
        with db_lock:
            with app.app_context():
                imported_count = 0
                
                # 导入商品数据
                if import_data.get('products'):
                    for product_data in import_data['products']:
                        # 检查是否已存在同名商品
                        existing = Product.query.filter_by(name=product_data['name']).first()
                        if not existing:
                            product = Product(
                                name=product_data['name'],
                                url=product_data['url'],
                                target_selector=product_data['target_selector'],
                                current_stock=product_data.get('current_stock', 0),
                                last_stock=product_data.get('last_stock', 0),
                                threshold=product_data.get('threshold', 1),
                                is_active=product_data.get('is_active', True),
                                buy_url=product_data.get('buy_url', product_data['url'])
                            )
                            db.session.add(product)
                            imported_count += 1
                
                # 导入通知配置（创建或更新）
                if import_data.get('notification_config'):
                    config_data = import_data['notification_config']
                    config = NotificationConfig.query.first()
                    
                    if not config:
                        # 创建新配置
                        config = NotificationConfig(
                            telegram_bot_token=config_data.get('telegram_bot_token', ''),
                            channel_enabled=config_data.get('channel_enabled', False),
                            channel_id=config_data.get('channel_id', ''),
                            group_enabled=config_data.get('group_enabled', False),
                            group_id=config_data.get('group_id', ''),
                            personal_enabled=config_data.get('personal_enabled', False),
                            personal_chat_id=config_data.get('personal_chat_id', ''),
                            user_enabled=config_data.get('user_enabled', False),
                            user_id=config_data.get('user_id', ''),
                            check_interval=config_data.get('check_interval', 120),
                            restock_enabled=config_data.get('restock_enabled', True),
                            sale_enabled=config_data.get('sale_enabled', True),
                            template_restock=config_data.get('template_restock', ''),
                            template_sale=config_data.get('template_sale', '')
                        )
                        db.session.add(config)
                    else:
                        # 更新现有配置
                        config.telegram_bot_token = config_data.get('telegram_bot_token', config.telegram_bot_token or '')
                        config.channel_enabled = config_data.get('channel_enabled', False)
                        config.channel_id = config_data.get('channel_id', '')
                        config.group_enabled = config_data.get('group_enabled', False)
                        config.group_id = config_data.get('group_id', '')
                        config.personal_enabled = config_data.get('personal_enabled', False)
                        config.personal_chat_id = config_data.get('personal_chat_id', '')
                        config.user_enabled = config_data.get('user_enabled', False)
                        config.user_id = config_data.get('user_id', '')
                        config.check_interval = config_data.get('check_interval', 120)
                        config.restock_enabled = config_data.get('restock_enabled', True)
                        config.sale_enabled = config_data.get('sale_enabled', True)
                        config.template_restock = config_data.get('template_restock', config.template_restock or '')
                        config.template_sale = config_data.get('template_sale', config.template_sale or '')
                        config.updated_at = get_internet_time().replace(tzinfo=None)
                
                # 提交数据库更改
                db.session.commit()
                
                # 构建导入结果消息
                config_imported = bool(import_data.get('notification_config'))
                message_parts = []
                if imported_count > 0:
                    message_parts.append(f'{imported_count} 个商品')
                if config_imported:
                    message_parts.append('系统配置')
                
                message = f'成功导入 {" 和 ".join(message_parts)}' if message_parts else '没有新数据需要导入'
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'imported_products': imported_count,
                    'imported_config': config_imported
                })
                
    except json.JSONDecodeError:
        return jsonify({
            'success': False,
            'message': '备份文件格式错误，请检查JSON格式'
        }), 400
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        logger.error(f"数据导入失败: {e}")
        return jsonify({
            'success': False,
            'message': f'导入失败: {str(e)}'
        }), 500

@app.route('/api/products')
@login_required
def api_products():
    """API: 获取所有商品"""
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'current_stock': p.current_stock,
        'last_stock': p.last_stock,
        'threshold': p.threshold,
        'is_active': p.is_active,
        'updated_at': db_time_to_china_time(p.updated_at).isoformat() if p.updated_at else None,
        'version': p.version
    } for p in products])

@app.route('/api/system_status')
@login_required
def api_system_status():
    """API: 获取系统状态"""
    with app.app_context():
        total_products = Product.query.count()
        active_products = Product.query.filter_by(is_active=True).count()
        in_stock_products = Product.query.filter(Product.current_stock > 0).count()
        out_stock_products = Product.query.filter(Product.current_stock == 0).count()
        
        # 获取最近的监控时间
        latest_update = db.session.query(db.func.max(Product.updated_at)).scalar()
        
        config = NotificationConfig.query.first()
        
        # 获取当前互联网时间
        current_internet_time = get_internet_time()
        
        return jsonify({
            'total_products': total_products,
            'active_products': active_products,
            'in_stock_products': in_stock_products,
            'out_stock_products': out_stock_products,
            'latest_update': db_time_to_china_time(latest_update).isoformat() if latest_update else None,
            'latest_update_formatted': db_time_to_china_time(latest_update).strftime('%Y-%m-%d %H:%M:%S') if latest_update else '从未检查',
            'current_time': current_internet_time.isoformat(),
            'current_time_formatted': current_internet_time.strftime('%Y-%m-%d %H:%M:%S'),
            'bot_configured': bool(config and config.telegram_bot_token),
            'notification_channels': sum([
                bool(config.channel_enabled) if config else False,
                bool(config.group_enabled) if config else False,
                bool(config.personal_enabled) if config else False,
                bool(getattr(config, 'user_enabled', False)) if config else False
            ]) if config else 0,
            'check_interval': config.check_interval if config and config.check_interval else 120
        })

@app.route('/api/sync_time', methods=['POST'])
@login_required
def api_sync_time():
    """API: 同步互联网时间"""
    try:
        internet_time = get_internet_time()
        return jsonify({
            'success': True,
            'current_time': internet_time.isoformat(),
            'formatted_time': internet_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': 'Asia/Shanghai',
            'timestamp': internet_time.timestamp()
        })
    except Exception as e:
        logger.error(f"时间同步失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test_monitor/<int:product_id>', methods=['POST'])
@login_required
def api_test_monitor(product_id):
    """测试单个商品监控"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # 检查库存
        new_stock = monitor.check_stock(product)
        
        if new_stock is not None:
            # 更新库存
            stock_changed, old_stock, updated_stock = monitor.update_stock_safe(product_id, new_stock)
            
            return jsonify({
                'success': True,
                'stock': updated_stock,
                'old_stock': old_stock,
                'changed': stock_changed,
                'message': f'库存检测成功，当前库存: {updated_stock}'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法获取库存信息，请检查网址和CSS选择器'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        })

@app.route('/api/manual_check', methods=['POST'])
@login_required
def api_manual_check():
    """手动触发检查所有商品"""
    try:
        # 在后台线程中运行监控
        def run_monitor():
            monitor_all_products_v2()
        
        import threading
        monitor_thread = threading.Thread(target=run_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return jsonify({
            'success': True,
            'message': '手动检查已触发，请稍后查看结果'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'手动检查失败: {str(e)}'
        })

@app.route('/api/recent_notifications')
@login_required
def api_recent_notifications():
    """API: 获取最近的通知"""
    notifications = NotificationLog.query\
        .order_by(NotificationLog.timestamp.desc())\
        .limit(50).all()
    
    return jsonify([{
        'id': n.id,
        'product_name': n.product.name if n.product else '未知商品',
        'notification_type': n.notification_type,
        'message': n.message,
        'status': n.status,
        'timestamp': db_time_to_china_time(n.timestamp).isoformat()
    } for n in notifications])

@app.route('/logs')
@login_required
def logs_page():
    """日志页面"""
    return render_template('logs.html')

@app.route('/api/monitoring_logs')
@login_required
def api_monitoring_logs():
    """API: 获取监控日志"""
    try:
        logs = []
        
        # 获取库存变化历史记录
        history_logs = db.session.query(StockHistory, Product)\
            .join(Product, StockHistory.product_id == Product.id)\
            .order_by(StockHistory.timestamp.desc())\
            .limit(1000).all()
            
        for history, product in history_logs:
            # 确定日志级别和消息，基于变化类型
            stock_difference = history.stock_count - history.previous_stock
            if history.change_type == 'increase':
                level = 'success'
                message = f'库存补货: +{stock_difference} 件'
            elif history.change_type == 'decrease':
                level = 'warning'
                message = f'库存减少: -{abs(stock_difference)} 件'
            else:
                # 这种情况现在不应该出现，因为我们只在有变化时记录
                level = 'info'
                message = f'库存变化: {stock_difference:+d} 件'
                
            logs.append({
                'id': f'stock_{history.id}',
                'product_id': product.id,
                'product_name': product.name,
                'level': level,
                'message': message,
                'details': f'变化时间: {db_time_to_china_time(history.timestamp).strftime("%Y-%m-%d %H:%M:%S")} | 库存变化: {history.previous_stock} → {history.stock_count} | 变化类型: {history.change_type}',
                'timestamp': db_time_to_china_time(history.timestamp).isoformat(),
                'stock_count': history.stock_count,
                'previous_stock': history.previous_stock,
                'change_type': history.change_type,
                'source': 'inventory_change'
            })
        
        # 获取通知日志记录
        notification_logs = db.session.query(NotificationLog, Product)\
            .join(Product, NotificationLog.product_id == Product.id)\
            .order_by(NotificationLog.timestamp.desc())\
            .limit(1000).all()
            
        for notif, product in notification_logs:
            # 确定日志级别
            if notif.status == 'sent':
                level = 'success'
                message = f'{notif.notification_type} 通知发送成功'
            elif notif.status == 'failed':
                level = 'error'
                message = f'{notif.notification_type} 通知发送失败'
            elif notif.status == 'error':
                level = 'error'
                message = f'{notif.notification_type} 通知发送出错'
            else:
                level = 'info'
                message = f'{notif.notification_type} 通知状态: {notif.status}'
                
            details = f'发送时间: {db_time_to_china_time(notif.timestamp).strftime("%Y-%m-%d %H:%M:%S")}'
            if notif.message:
                details += f' | 消息: {notif.message}'
                
            logs.append({
                'id': f'notification_{notif.id}',
                'product_id': product.id,
                'product_name': product.name,
                'level': level,
                'message': message,
                'details': details,
                'timestamp': db_time_to_china_time(notif.timestamp).isoformat(),
                'notification_type': notif.notification_type,
                'notification_status': notif.status,
                'source': 'notification'
            })
        
        # 按时间倒序排列所有日志
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 限制返回的日志数量
        logs = logs[:2000]
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        })
        
    except Exception as e:
        logger.error(f"获取监控日志失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取日志失败: {str(e)}'
        })

@app.route('/clear_logs', methods=['POST'])
@app.route('/api/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    """清除所有日志"""
    try:
        with db_lock:
            # 删除所有库存历史记录
            history_deleted = StockHistory.query.delete()
            
            # 删除所有通知记录
            notification_deleted = NotificationLog.query.delete()
            
            db.session.commit()
        
        total_deleted = history_deleted + notification_deleted
        
        return jsonify({
            'success': True,
            'message': f'已清除 {total_deleted} 条日志记录 (库存历史: {history_deleted}, 通知记录: {notification_deleted})',
            'deleted_count': total_deleted
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"清除日志失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/toggle_product_status/<int:product_id>', methods=['POST'])
@login_required
def toggle_product_status(product_id):
    """切换商品监控状态"""
    try:
        with db_lock:
            product = Product.query.get_or_404(product_id)
            product.is_active = not product.is_active
            db.session.commit()
            
            status_text = "启用" if product.is_active else "暂停"
            logger.info(f"商品 {product.name} 监控状态已{status_text}")
            
            return jsonify({
                'success': True,
                'message': f'商品 "{product.name}" 监控已{status_text}',
                'is_active': product.is_active
            })
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"切换商品状态失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/test_notification', methods=['POST'])
@app.route('/api/test_notification', methods=['POST'])
@login_required
def test_notification():
    """测试通知发送"""
    try:
        # 获取测试类型
        data = request.get_json()
        test_type = data.get('type') if data else None
        
        config = NotificationConfig.query.first()
        if not config or not config.telegram_bot_token:
            return jsonify({
                'success': False,
                'message': '请先配置Telegram机器人令牌'
            }), 400
        
        # 使用中国时间
        china_time = get_internet_time()
        test_message = "🧪 测试通知\n\n📦 商品名称: 华为云2（测试商品）\n📈 补货数量: 5 件\n📊 当前库存: 10 件\n\n🕐 发送时间: " + china_time.strftime('%Y-%m-%d %H:%M:%S') + " (中国时间)"
        
        # 创建一个虚拟商品对象用于测试按钮
        class TestProduct:
            def __init__(self):
                self.name = "华为云2（测试商品）"
                self.buy_url = "https://djk.pub"
        
        test_product = TestProduct()
        
        results = []
        total_success = 0
        
        # 根据类型测试对应的通知渠道
        if test_type == 'channel':
            # 只测试频道通知
            if config.channel_id and config.channel_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.channel_id, test_message, test_product)
                results.append({
                    'type': '频道消息',
                    'target': config.channel_id,
                    'success': success
                })
                if success:
                    total_success += 1
            else:
                return jsonify({
                    'success': False,
                    'message': '频道通知未启用或未配置频道ID'
                }), 400
                
        elif test_type == 'group':
            # 只测试群组通知
            if config.group_id and config.group_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.group_id, test_message, test_product)
                results.append({
                    'type': '群组消息',
                    'target': config.group_id,
                    'success': success
                })
                if success:
                    total_success += 1
            else:
                return jsonify({
                    'success': False,
                    'message': '群组通知未启用或未配置群组ID'
                }), 400
                
        elif test_type == 'user':
            # 测试个人通知
            sent_any = False
            if hasattr(config, 'user_id') and hasattr(config, 'user_enabled') and config.user_id and config.user_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.user_id, test_message, test_product)
                results.append({
                    'type': '个人消息',
                    'target': config.user_id,
                    'success': success
                })
                if success:
                    total_success += 1
                sent_any = True
            
            if not sent_any:
                return jsonify({
                    'success': False,
                    'message': '个人通知未启用或未配置用户ID'
                }), 400
        else:
            # 测试所有已启用的通知渠道
            # 测试个人通知（兼容两个字段）
            if config.personal_chat_id and config.personal_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.personal_chat_id, test_message, test_product)
                results.append({
                    'type': '个人消息',
                    'target': config.personal_chat_id,
                    'success': success
                })
                if success:
                    total_success += 1
            
            # 测试用户通知（新字段）
            if hasattr(config, 'user_id') and hasattr(config, 'user_enabled') and config.user_id and config.user_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.user_id, test_message, test_product)
                results.append({
                    'type': '用户消息',
                    'target': config.user_id,
                    'success': success
                })
                if success:
                    total_success += 1
            
            # 测试群组通知
            if config.group_id and config.group_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.group_id, test_message, test_product)
                results.append({
                    'type': '群组消息',
                    'target': config.group_id,
                    'success': success
                })
                if success:
                    total_success += 1
            
            # 测试频道通知
            if config.channel_id and config.channel_enabled:
                success = notifier._send_to_chat(config.telegram_bot_token, config.channel_id, test_message, test_product)
                results.append({
                    'type': '频道消息',
                    'target': config.channel_id,
                    'success': success
                })
                if success:
                    total_success += 1
        
        if not results:
            return jsonify({
                'success': False,
                'message': '请至少配置一个接收者（个人、群组或频道）'
            }), 400
        
        return jsonify({
            'success': total_success > 0,
            'message': f'测试完成！成功发送 {total_success}/{len(results)} 条消息',
            'results': results,
            'success_count': total_success,
            'total_count': len(results)
        })
        
    except Exception as e:
        logger.error(f"测试通知失败: {e}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    logger.info("初始化库存监控系统 V2...")
    
    with app.app_context():
        db.create_all()
        logger.info("数据库初始化完成")
        
        # 初始化默认管理员用户
        init_default_user()
    
    # 启动调度器
    try:
        with app.app_context():
            config = NotificationConfig.query.first()
            interval_seconds = config.check_interval if config else 120
        
        scheduler.add_job(
            func=monitor_all_products_v2,
            trigger="interval",
            seconds=interval_seconds,
            id='monitor_job_v2'
        )
        scheduler.start()
        
        logger.info(f"定时任务启动完成，间隔: {interval_seconds} 秒")
        logger.info("系统启动成功！访问 http://localhost:5000")
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        logger.warning(f"调度器启动失败: {e}")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("停止服务...")
        scheduler.shutdown()
