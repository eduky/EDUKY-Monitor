#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库结构迁移脚本 - 添加 previous_stock 字段
"""

import sys
import os
import sqlite3

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_database():
    """迁移数据库，添加previous_stock字段"""
    try:
        from app_v2_fixed import app, db
        
        with app.app_context():
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if db_uri.startswith('sqlite:///'):
                db_path = db_uri[10:]  # 移除 'sqlite:///'
                # 移除查询参数
                if '?' in db_path:
                    db_path = db_path.split('?')[0]
            else:
                raise ValueError(f"不支持的数据库类型: {db_uri}")
            
            print(f"🔧 迁移数据库: {db_path}")
            
            # 连接到数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在 previous_stock 列
            cursor.execute("PRAGMA table_info(stock_histories)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'previous_stock' not in columns:
                print("   ➕ 添加 previous_stock 字段...")
                cursor.execute("ALTER TABLE stock_histories ADD COLUMN previous_stock INTEGER DEFAULT 0")
                conn.commit()
                print("   ✅ previous_stock 字段添加成功")
            else:
                print("   ℹ️  previous_stock 字段已存在")
            
            # 更新现有记录的 previous_stock 值
            print("   🔄 更新现有记录...")
            cursor.execute("""
                SELECT id, product_id, stock_count, timestamp 
                FROM stock_histories 
                WHERE previous_stock = 0
                ORDER BY product_id, timestamp
            """)
            records = cursor.fetchall()
            
            if records:
                # 按产品分组处理
                product_records = {}
                for record in records:
                    product_id = record[1]
                    if product_id not in product_records:
                        product_records[product_id] = []
                    product_records[product_id].append(record)
                
                # 为每个产品的历史记录推断 previous_stock
                for product_id, product_records_list in product_records.items():
                    # 按时间排序
                    product_records_list.sort(key=lambda x: x[3])  # 按 timestamp 排序
                    
                    # 获取产品的初始库存（假设第一条记录的前值为0）
                    previous_stock = 0
                    
                    for record in product_records_list:
                        history_id, _, current_stock, _ = record
                        
                        # 更新 previous_stock
                        cursor.execute(
                            "UPDATE stock_histories SET previous_stock = ? WHERE id = ?",
                            (previous_stock, history_id)
                        )
                        
                        # 下一条记录的 previous_stock 就是当前的 stock_count
                        previous_stock = current_stock
                
                conn.commit()
                print(f"   ✅ 更新了 {len(records)} 条历史记录")
            else:
                print("   ℹ️  没有需要更新的记录")
            
            conn.close()
            print("✅ 数据库迁移完成!")
            return True
            
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🗃️  数据库结构迁移")
    print("=" * 60)
    
    print("🎯 迁移目标:")
    print("   - 为 stock_histories 表添加 previous_stock 字段")
    print("   - 更新现有记录的 previous_stock 值")
    print("   - 保持数据完整性")
    
    print("\n" + "=" * 60)
    
    if migrate_database():
        print("\n🎉 数据库迁移成功!")
        print("\n📝 迁移内容:")
        print("   ✅ 添加了 previous_stock 字段")
        print("   ✅ 更新了现有历史记录")
        print("   ✅ 数据结构已优化")
    else:
        print("\n❌ 迁移失败，请检查错误信息")

if __name__ == "__main__":
    main()