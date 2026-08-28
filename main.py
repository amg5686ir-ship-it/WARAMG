# -*- coding: utf-8 -*-
"""
WAR BOT - Telegram World War Strategy Game
نسخه کامل یک‌تکه - همه چیز در یک فایل
"""

import telebot
from telebot import types
import sqlite3
import json
import time
import threading
import random
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# =============================================
# ۱. پیکربندی
# =============================================

# از متغیرهای محیطی یا مقادیر مستقیم
TOKEN = os.environ.get('BOT_TOKEN', '8688261466:AAEYEsRqFCjjc6Kbi3zBUEQFwoAA88MbQmk')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 8080581244))
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@your_channel')
WAR_CHANNEL_ID = os.environ.get('WAR_CHANNEL_ID', CHANNEL_ID)

bot = telebot.TeleBot(TOKEN)
conn = sqlite3.connect('game_bot.db', check_same_thread=False)
cursor = conn.cursor()

# =============================================
# ۲. دیتابیس - همه جدول‌ها
# =============================================

def init_database():
    """ایجاد همه جدول‌های دیتابیس"""
    
    # ۱. جدول کشورها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        flag TEXT NOT NULL,
        is_vip INTEGER DEFAULT 0,
        has_strait INTEGER DEFAULT 0,
        strait_name TEXT DEFAULT '',
        is_strait_open INTEGER DEFAULT 1,
        is_sanctioned INTEGER DEFAULT 0,
        sanctioned_by INTEGER DEFAULT NULL,
        owner_id INTEGER DEFAULT NULL,
        chat_id INTEGER DEFAULT NULL,
        
        -- منابع اقتصادی
        money INTEGER DEFAULT 1000000,
        oil INTEGER DEFAULT 100,
        gold INTEGER DEFAULT 100,
        iron INTEGER DEFAULT 500,
        stones INTEGER DEFAULT 500,
        wood INTEGER DEFAULT 500,
        food INTEGER DEFAULT 500,
        meat INTEGER DEFAULT 500,
        clothes INTEGER DEFAULT 500,
        
        -- آمار کشور
        population INTEGER DEFAULT 1000000,
        happiness INTEGER DEFAULT 70,
        military_readiness INTEGER DEFAULT 50,
        
        -- زمان‌ها
        last_income TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ۲. جدول شهرها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        population INTEGER DEFAULT 50000,
        infrastructure_level INTEGER DEFAULT 1,
        defense_level INTEGER DEFAULT 0,
        has_power_plant INTEGER DEFAULT 0,
        has_internet INTEGER DEFAULT 1,
        is_quarantined INTEGER DEFAULT 0,
        is_occupied INTEGER DEFAULT 0,
        factories TEXT DEFAULT '{}',
        companies TEXT DEFAULT '{}',
        deployed_defenses TEXT DEFAULT '[]',
        deployed_units TEXT DEFAULT '{}',
        is_capital INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۳. جدول واحدهای نظامی
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS military_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        unit_type TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        name TEXT NOT NULL,
        power INTEGER DEFAULT 10,
        cost_money INTEGER DEFAULT 10000,
        cost_oil INTEGER DEFAULT 0,
        build_time_minutes INTEGER DEFAULT 10,
        deployed_city_id INTEGER DEFAULT NULL,
        is_ready INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۴. جدول موشک‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS missiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        missile_type TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        name TEXT NOT NULL,
        power INTEGER DEFAULT 30,
        range_km INTEGER DEFAULT 100,
        cost_money INTEGER DEFAULT 50000,
        cost_oil INTEGER DEFAULT 5,
        build_time_minutes INTEGER DEFAULT 20,
        is_nuclear INTEGER DEFAULT 0,
        is_ready INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۵. جدول پدافند
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS defenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        defense_type TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        name TEXT NOT NULL,
        intercept_chance INTEGER DEFAULT 50,
        cost_money INTEGER DEFAULT 150000,
        cost_oil INTEGER DEFAULT 5,
        build_time_minutes INTEGER DEFAULT 25,
        is_ready INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۶. جدول پهپادها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        drone_type TEXT NOT NULL,
        count INTEGER DEFAULT 0,
        name TEXT NOT NULL,
        power INTEGER DEFAULT 15,
        range_km INTEGER DEFAULT 100,
        cost_money INTEGER DEFAULT 30000,
        cost_oil INTEGER DEFAULT 3,
        build_time_minutes INTEGER DEFAULT 15,
        is_ready INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۷. جدول واحدهای سایبری
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cyber_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        cyber_level TEXT NOT NULL,
        name TEXT NOT NULL,
        attack_power INTEGER DEFAULT 10,
        defense_power INTEGER DEFAULT 10,
        cost_money INTEGER DEFAULT 50000,
        cost_oil INTEGER DEFAULT 2,
        build_time_minutes INTEGER DEFAULT 20,
        is_ready INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES countries(id)
    )
    ''')
    
    # ۸. جدول جنگ‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS wars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attacker_id INTEGER NOT NULL,
        defender_id INTEGER NOT NULL,
        status TEXT DEFAULT 'declared',
        attacker_casualties INTEGER DEFAULT 0,
        defender_casualties INTEGER DEFAULT 0,
        attacker_damage INTEGER DEFAULT 0,
        defender_damage INTEGER DEFAULT 0,
        resources_consumed TEXT DEFAULT '{}',
        declared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (attacker_id) REFERENCES countries(id),
        FOREIGN KEY (defender_id) REFERENCES countries(id)
    )
    ''')
    
    # ۹. جدول اتحادها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        leader_id INTEGER NOT NULL,
        members TEXT DEFAULT '[]',
        mutual_defense INTEGER DEFAULT 1,
        non_aggression INTEGER DEFAULT 1,
        trade_agreement INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (leader_id) REFERENCES countries(id)
    )
    ''')
    
    # ۱۰. جدول پیمان‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treaties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        country1_id INTEGER NOT NULL,
        country2_id INTEGER NOT NULL,
        duration_days INTEGER DEFAULT 30,
        terms TEXT DEFAULT '{}',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (country1_id) REFERENCES countries(id),
        FOREIGN KEY (country2_id) REFERENCES countries(id)
    )
    ''')
    
    # ۱۱. جدول عملیات اطلاعاتی
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS intelligence_ops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        target_id INTEGER NOT NULL,
        op_type TEXT NOT NULL,
        status TEXT DEFAULT 'planning',
        result TEXT DEFAULT NULL,
        cost_money INTEGER DEFAULT 100000,
        cost_oil INTEGER DEFAULT 5,
        duration_minutes INTEGER DEFAULT 60,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP DEFAULT NULL,
        FOREIGN KEY (source_id) REFERENCES countries(id),
        FOREIGN KEY (target_id) REFERENCES countries(id)
    )
    ''')
    
    # ۱۲. جدول کانال سوئز
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS suez_canal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        is_open INTEGER DEFAULT 1,
        owner_id INTEGER DEFAULT NULL,
        daily_revenue INTEGER DEFAULT 0,
        toll_per_pass INTEGER DEFAULT 100000,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES countries(id)
    )
    ''')
    
    # ۱۳. جدول ادمین‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        added_by INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # ۱۴. جدول نوبت‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS turns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turn_number INTEGER NOT NULL UNIQUE,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP DEFAULT NULL,
        countries_processed INTEGER DEFAULT 0,
        total_countries INTEGER DEFAULT 0,
        status TEXT DEFAULT 'processing'
    )
    ''')
    
    # ۱۵. جدول لاگ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL,
        action TEXT NOT NULL,
        target TEXT DEFAULT '',
        detail TEXT DEFAULT '',
        actor_id INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    print("✅ دیتابیس با موفقیت ایجاد شد")

init_database()

# =============================================
# ۳. دیتای بازی
# =============================================

# ۱۰۰ کشور اول جهان
COUNTRIES_DATA = [
    # ۲۰ کشور VIP
    {'name': 'America', 'flag': '🇺🇸', 'vip': True},
    {'name': 'China', 'flag': '🇨🇳', 'vip': True},
    {'name': 'Russia', 'flag': '🇷🇺', 'vip': True},
    {'name': 'India', 'flag': '🇮🇳', 'vip': True},
    {'name': 'UK', 'flag': '🇬🇧', 'vip': True},
    {'name': 'France', 'flag': '🇫🇷', 'vip': True},
    {'name': 'Germany', 'flag': '🇩🇪', 'vip': True},
    {'name': 'Japan', 'flag': '🇯🇵', 'vip': True},
    {'name': 'Iran', 'flag': '🇮🇷', 'vip': True, 'strait': True, 'strait_name': 'تنگه هرمز'},
    {'name': 'Turkey', 'flag': '🇹🇷', 'vip': True},
    {'name': 'South Korea', 'flag': '🇰🇷', 'vip': True},
    {'name': 'Italy', 'flag': '🇮🇹', 'vip': True},
    {'name': 'Brazil', 'flag': '🇧🇷', 'vip': True},
    {'name': 'Canada', 'flag': '🇨🇦', 'vip': True},
    {'name': 'Australia', 'flag': '🇦🇺', 'vip': True},
    {'name': 'Spain', 'flag': '🇪🇸', 'vip': True},
    {'name': 'Mexico', 'flag': '🇲🇽', 'vip': True},
    {'name': 'Indonesia', 'flag': '🇮🇩', 'vip': True},
    {'name': 'Netherlands', 'flag': '🇳🇱', 'vip': True},
    {'name': 'Saudi Arabia', 'flag': '🇸🇦', 'vip': True},
    
    # ۸۰ کشور عادی
    {'name': 'Egypt', 'flag': '🇪🇬', 'vip': False, 'strait': True, 'strait_name': 'کانال سوئز'},
    {'name': 'Yemen', 'flag': '🇾🇪', 'vip': False, 'strait': True, 'strait_name': 'باب‌المندب'},
    {'name': 'Pakistan', 'flag': '🇵🇰', 'vip': False},
    {'name': 'Nigeria', 'flag': '🇳🇬', 'vip': False},
    {'name': 'Bangladesh', 'flag': '🇧🇩', 'vip': False},
    {'name': 'Ethiopia', 'flag': '🇪🇹', 'vip': False},
    {'name': 'Philippines', 'flag': '🇵🇭', 'vip': False},
    {'name': 'DR Congo', 'flag': '🇨🇩', 'vip': False},
    {'name': 'Vietnam', 'flag': '🇻🇳', 'vip': False},
    {'name': 'Thailand', 'flag': '🇹🇭', 'vip': False},
    {'name': 'South Africa', 'flag': '🇿🇦', 'vip': False},
    {'name': 'Tanzania', 'flag': '🇹🇿', 'vip': False},
    {'name': 'Kenya', 'flag': '🇰🇪', 'vip': False},
    {'name': 'Uganda', 'flag': '🇺🇬', 'vip': False},
    {'name': 'Sudan', 'flag': '🇸🇩', 'vip': False},
    {'name': 'Algeria', 'flag': '🇩🇿', 'vip': False},
    {'name': 'Morocco', 'flag': '🇲🇦', 'vip': False},
    {'name': 'Iraq', 'flag': '🇮🇶', 'vip': False},
    {'name': 'Afghanistan', 'flag': '🇦🇫', 'vip': False},
    {'name': 'Uzbekistan', 'flag': '🇺🇿', 'vip': False},
    {'name': 'Malaysia', 'flag': '🇲🇾', 'vip': False},
    {'name': 'Angola', 'flag': '🇦🇴', 'vip': False},
    {'name': 'Ghana', 'flag': '🇬🇭', 'vip': False},
    {'name': 'Cameroon', 'flag': '🇨🇲', 'vip': False},
    {'name': 'Ivory Coast', 'flag': '🇨🇮', 'vip': False},
    {'name': 'Niger', 'flag': '🇳🇪', 'vip': False},
    {'name': 'Burkina Faso', 'flag': '🇧🇫', 'vip': False},
    {'name': 'Mali', 'flag': '🇲🇱', 'vip': False},
    {'name': 'Malawi', 'flag': '🇲🇼', 'vip': False},
    {'name': 'Chad', 'flag': '🇹🇩', 'vip': False},
    {'name': 'Somalia', 'flag': '🇸🇴', 'vip': False},
    {'name': 'Senegal', 'flag': '🇸🇳', 'vip': False},
    {'name': 'Zimbabwe', 'flag': '🇿🇼', 'vip': False},
    {'name': 'Guinea', 'flag': '🇬🇳', 'vip': False},
    {'name': 'Rwanda', 'flag': '🇷🇼', 'vip': False},
    {'name': 'Benin', 'flag': '🇧🇯', 'vip': False},
    {'name': 'Burundi', 'flag': '🇧🇮', 'vip': False},
    {'name': 'Tunisia', 'flag': '🇹🇳', 'vip': False},
    {'name': 'Bolivia', 'flag': '🇧🇴', 'vip': False},
    {'name': 'Belgium', 'flag': '🇧🇪', 'vip': False},
    {'name': 'Cuba', 'flag': '🇨🇺', 'vip': False},
    {'name': 'Czechia', 'flag': '🇨🇿', 'vip': False},
    {'name': 'Greece', 'flag': '🇬🇷', 'vip': False},
    {'name': 'Portugal', 'flag': '🇵🇹', 'vip': False},
    {'name': 'Sweden', 'flag': '🇸🇪', 'vip': False},
    {'name': 'Hungary', 'flag': '🇭🇺', 'vip': False},
    {'name': 'Austria', 'flag': '🇦🇹', 'vip': False},
    {'name': 'Switzerland', 'flag': '🇨🇭', 'vip': False},
    {'name': 'Bulgaria', 'flag': '🇧🇬', 'vip': False},
    {'name': 'Serbia', 'flag': '🇷🇸', 'vip': False},
    {'name': 'Denmark', 'flag': '🇩🇰', 'vip': False},
    {'name': 'Finland', 'flag': '🇫🇮', 'vip': False},
    {'name': 'Slovakia', 'flag': '🇸🇰', 'vip': False},
    {'name': 'Norway', 'flag': '🇳🇴', 'vip': False},
    {'name': 'Ireland', 'flag': '🇮🇪', 'vip': False},
    {'name': 'Croatia', 'flag': '🇭🇷', 'vip': False},
    {'name': 'Moldova', 'flag': '🇲🇩', 'vip': False},
    {'name': 'Bosnia', 'flag': '🇧🇦', 'vip': False},
    {'name': 'Albania', 'flag': '🇦🇱', 'vip': False},
    {'name': 'Lithuania', 'flag': '🇱🇹', 'vip': False},
    {'name': 'Latvia', 'flag': '🇱🇻', 'vip': False},
    {'name': 'Estonia', 'flag': '🇪🇪', 'vip': False},
    {'name': 'Slovenia', 'flag': '🇸🇮', 'vip': False},
    {'name': 'Cyprus', 'flag': '🇨🇾', 'vip': False},
    {'name': 'Lebanon', 'flag': '🇱🇧', 'vip': False},
    {'name': 'Jordan', 'flag': '🇯🇴', 'vip': False},
    {'name': 'Oman', 'flag': '🇴🇲', 'vip': False},
    {'name': 'Kuwait', 'flag': '🇰🇼', 'vip': False},
    {'name': 'Qatar', 'flag': '🇶🇦', 'vip': False},
    {'name': 'UAE', 'flag': '🇦🇪', 'vip': False},
    {'name': 'Bahrain', 'flag': '🇧🇭', 'vip': False},
    {'name': 'Mongolia', 'flag': '🇲🇳', 'vip': False},
    {'name': 'Nepal', 'flag': '🇳🇵', 'vip': False},
    {'name': 'Sri Lanka', 'flag': '🇱🇰', 'vip': False},
    {'name': 'Myanmar', 'flag': '🇲🇲', 'vip': False},
    {'name': 'Cambodia', 'flag': '🇰🇭', 'vip': False},
    {'name': 'Laos', 'flag': '🇱🇦', 'vip': False},
    {'name': 'North Korea', 'flag': '🇰🇵', 'vip': False},
    {'name': 'Syria', 'flag': '🇸🇾', 'vip': False},
    {'name': 'Libya', 'flag': '🇱🇾', 'vip': False},
]

# دیتای واحدهای نظامی
UNITS_DATA = {
    # نیروی زمینی
    'infantry': {'name': 'سرباز پیاده', 'power': 5, 'cost_money': 10000, 'cost_oil': 0, 'build_time': 5},
    'special_forces': {'name': 'تکاور', 'power': 15, 'cost_money': 50000, 'cost_oil': 2, 'build_time': 15},
    'm1_abrams': {'name': 'M1 Abrams', 'power': 50, 'cost_money': 200000, 'cost_oil': 5, 'build_time': 30},
    'leopard_2a7': {'name': 'Leopard 2A7', 'power': 55, 'cost_money': 220000, 'cost_oil': 5, 'build_time': 30},
    't_90m': {'name': 'T-90M', 'power': 45, 'cost_money': 180000, 'cost_oil': 4, 'build_time': 25},
    'challenger_3': {'name': 'Challenger 3', 'power': 50, 'cost_money': 200000, 'cost_oil': 5, 'build_time': 30},
    'leclerc': {'name': 'Leclerc', 'power': 48, 'cost_money': 190000, 'cost_oil': 5, 'build_time': 28},
    'k2_black_panther': {'name': 'K2 Black Panther', 'power': 52, 'cost_money': 210000, 'cost_oil': 5, 'build_time': 30},
    'merkava_mk4': {'name': 'Merkava Mk.4', 'power': 55, 'cost_money': 230000, 'cost_oil': 5, 'build_time': 35},
    'type_99a': {'name': 'Type 99A', 'power': 48, 'cost_money': 190000, 'cost_oil': 4, 'build_time': 28},
    
    # نیروی هوایی
    'f_22_raptor': {'name': 'F-22 Raptor', 'power': 80, 'cost_money': 350000, 'cost_oil': 8, 'build_time': 45},
    'f_35_lightning': {'name': 'F-35 Lightning II', 'power': 75, 'cost_money': 320000, 'cost_oil': 7, 'build_time': 40},
    'f_16': {'name': 'F-16 Fighting Falcon', 'power': 45, 'cost_money': 180000, 'cost_oil': 4, 'build_time': 30},
    'f_15': {'name': 'F-15 Eagle', 'power': 55, 'cost_money': 220000, 'cost_oil': 5, 'build_time': 35},
    'f_18': {'name': 'F/A-18 Hornet', 'power': 50, 'cost_money': 200000, 'cost_oil': 5, 'build_time': 32},
    'rafale': {'name': 'Rafale', 'power': 52, 'cost_money': 210000, 'cost_oil': 5, 'build_time': 35},
    'eurofighter': {'name': 'Eurofighter Typhoon', 'power': 55, 'cost_money': 220000, 'cost_oil': 5, 'build_time': 35},
    'su_35': {'name': 'Su-35', 'power': 60, 'cost_money': 240000, 'cost_oil': 6, 'build_time': 38},
    'su_57': {'name': 'Su-57', 'power': 70, 'cost_money': 300000, 'cost_oil': 7, 'build_time': 42},
    'j_20': {'name': 'J-20', 'power': 65, 'cost_money': 280000, 'cost_oil': 7, 'build_time': 40},
    'b_1b': {'name': 'B-1B Lancer', 'power': 40, 'cost_money': 250000, 'cost_oil': 10, 'build_time': 45},
    'b_2': {'name': 'B-2 Spirit', 'power': 60, 'cost_money': 400000, 'cost_oil': 12, 'build_time': 50},
    'b_52': {'name': 'B-52 Stratofortress', 'power': 35, 'cost_money': 200000, 'cost_oil': 8, 'build_time': 40},
    'tu_160': {'name': 'Tu-160 Blackjack', 'power': 45, 'cost_money': 280000, 'cost_oil': 10, 'build_time': 48},
    'h_6k': {'name': 'H-6K', 'power': 30, 'cost_money': 180000, 'cost_oil': 7, 'build_time': 35},
}

# دیتای موشک‌ها
MISSILES_DATA = {
    # بالستیک
    'scud': {'name': 'Scud', 'power': 30, 'range': 100, 'cost_money': 50000, 'cost_oil': 5, 'build_time': 20},
    'iskander': {'name': 'Iskander', 'power': 45, 'range': 150, 'cost_money': 80000, 'cost_oil': 8, 'build_time': 30},
    'atacms': {'name': 'ATACMS', 'power': 50, 'range': 200, 'cost_money': 100000, 'cost_oil': 10, 'build_time': 35},
    'df_11': {'name': 'DF-11', 'power': 55, 'range': 220, 'cost_money': 120000, 'cost_oil': 10, 'build_time': 40},
    'df_21': {'name': 'DF-21', 'power': 70, 'range': 300, 'cost_money': 200000, 'cost_oil': 15, 'build_time': 50},
    'df_26': {'name': 'DF-26', 'power': 80, 'range': 350, 'cost_money': 250000, 'cost_oil': 18, 'build_time': 55},
    'minuteman_iii': {'name': 'Minuteman III', 'power': 100, 'range': 500, 'cost_money': 500000, 'cost_oil': 30, 'build_time': 90},
    'trident_ii': {'name': 'Trident II', 'power': 110, 'range': 550, 'cost_money': 550000, 'cost_oil': 32, 'build_time': 95},
    'agni_v': {'name': 'Agni-V', 'power': 95, 'range': 450, 'cost_money': 450000, 'cost_oil': 28, 'build_time': 85},
    
    # کروز
    'tomahawk': {'name': 'Tomahawk', 'power': 60, 'range': 250, 'cost_money': 150000, 'cost_oil': 12, 'build_time': 40},
    'jassm': {'name': 'JASSM', 'power': 55, 'range': 200, 'cost_money': 130000, 'cost_oil': 10, 'build_time': 35},
    'storm_shadow': {'name': 'Storm Shadow', 'power': 50, 'range': 180, 'cost_money': 120000, 'cost_oil': 10, 'build_time': 30},
    'kalibr': {'name': 'Kalibr', 'power': 58, 'range': 220, 'cost_money': 140000, 'cost_oil': 12, 'build_time': 38},
    'kh_101': {'name': 'Kh-101', 'power': 52, 'range': 200, 'cost_money': 135000, 'cost_oil': 11, 'build_time': 35},
    'brahmos': {'name': 'BrahMos', 'power': 60, 'range': 240, 'cost_money': 160000, 'cost_oil': 13, 'build_time': 40},
    'harpoon': {'name': 'Harpoon', 'power': 45, 'range': 160, 'cost_money': 100000, 'cost_oil': 8, 'build_time': 30},
    'exocet': {'name': 'Exocet', 'power': 48, 'range': 170, 'cost_money': 110000, 'cost_oil': 8, 'build_time': 32},
    'naval_strike': {'name': 'Naval Strike', 'power': 50, 'range': 180, 'cost_money': 120000, 'cost_oil': 9, 'build_time': 33},
    'taurus': {'name': 'Taurus', 'power': 55, 'range': 200, 'cost_money': 130000, 'cost_oil': 10, 'build_time': 35},
    
    # هسته‌ای
    'nuclear_icbm': {'name': 'موشک هسته‌ای ICBM', 'power': 500, 'range': 800, 'cost_money': 2000000, 'cost_oil': 100, 'build_time': 120, 'nuclear': True},
}

# دیتای پدافند
DEFENSES_DATA = {
    'patriot': {'name': 'Patriot', 'intercept_chance': 80, 'cost_money': 300000, 'cost_oil': 10, 'build_time': 40},
    'thaad': {'name': 'THAAD', 'intercept_chance': 90, 'cost_money': 400000, 'cost_oil': 12, 'build_time': 50},
    's_300': {'name': 'S-300', 'intercept_chance': 75, 'cost_money': 280000, 'cost_oil': 9, 'build_time': 38},
    's_400': {'name': 'S-400', 'intercept_chance': 85, 'cost_money': 350000, 'cost_oil': 12, 'build_time': 45},
    's_500': {'name': 'S-500', 'intercept_chance': 90, 'cost_money': 400000, 'cost_oil': 15, 'build_time': 50},
    'iron_dome': {'name': 'Iron Dome', 'intercept_chance': 70, 'cost_money': 150000, 'cost_oil': 5, 'build_time': 25},
    'davids_sling': {'name': "David's Sling", 'intercept_chance': 85, 'cost_money': 350000, 'cost_oil': 10, 'build_time': 45},
    'arrow_2': {'name': 'Arrow 2', 'intercept_chance': 88, 'cost_money': 380000, 'cost_oil': 11, 'build_time': 48},
    'arrow_3': {'name': 'Arrow 3', 'intercept_chance': 92, 'cost_money': 420000, 'cost_oil': 13, 'build_time': 52},
    'nasams': {'name': 'NASAMS', 'intercept_chance': 65, 'cost_money': 140000, 'cost_oil': 4, 'build_time': 22},
    'buk_m3': {'name': 'Buk-M3', 'intercept_chance': 72, 'cost_money': 260000, 'cost_oil': 8, 'build_time': 35},
    'tor_m2': {'name': 'Tor-M2', 'intercept_chance': 75, 'cost_money': 160000, 'cost_oil': 5, 'build_time': 28},
    'hq_9': {'name': 'HQ-9', 'intercept_chance': 70, 'cost_money': 250000, 'cost_oil': 8, 'build_time': 35},
    'aster_30': {'name': 'Aster 30', 'intercept_chance': 82, 'cost_money': 320000, 'cost_oil': 11, 'build_time': 42},
}

# دیتای پهپادها
DRONES_DATA = {
    'shahed_136': {'name': 'شاهد-136', 'power': 20, 'range': 100, 'cost_money': 30000, 'cost_oil': 2, 'build_time': 15},
    'ababil': {'name': 'ابابیل', 'power': 15, 'range': 80, 'cost_money': 25000, 'cost_oil': 2, 'build_time': 12},
    'karar': {'name': 'کرار', 'power': 25, 'range': 120, 'cost_money': 35000, 'cost_oil': 3, 'build_time': 18},
    'arash': {'name': 'آرش', 'power': 30, 'range': 150, 'cost_money': 40000, 'cost_oil': 3, 'build_time': 20},
    'tb2': {'name': 'TB2', 'power': 35, 'range': 180, 'cost_money': 50000, 'cost_oil': 4, 'build_time': 25},
    'mq_9': {'name': 'MQ-9 Reaper', 'power': 45, 'range': 250, 'cost_money': 80000, 'cost_oil': 6, 'build_time': 30},
    'global_hawk': {'name': 'Global Hawk', 'power': 10, 'range': 300, 'cost_money': 60000, 'cost_oil': 4, 'build_time': 20},
}

# دیتای واحدهای سایبری
CYBER_DATA = {
    'beginner': {'name': 'هکر مبتدی', 'attack': 10, 'defense': 10, 'cost_money': 10000, 'cost_oil': 1, 'build_time': 10},
    'intermediate': {'name': 'تیم نفوذ سایبری', 'attack': 25, 'defense': 25, 'cost_money': 30000, 'cost_oil': 3, 'build_time': 20},
    'advanced': {'name': 'مرکز جنگ سایبری', 'attack': 50, 'defense': 50, 'cost_money': 80000, 'cost_oil': 8, 'build_time': 35},
    'apt': {'name': 'APT تیم پیشرفته', 'attack': 80, 'defense': 80, 'cost_money': 150000, 'cost_oil': 15, 'build_time': 50},
    'elite': {'name': 'سایبر ارتش ملی', 'attack': 100, 'defense': 100, 'cost_money': 250000, 'cost_oil': 25, 'build_time': 70},
}

# =============================================
# ۴. توابع کمکی دیتابیس
# =============================================

def seed_countries():
    """اضافه کردن ۱۰۰ کشور به دیتابیس"""
    cursor.execute("SELECT COUNT(*) FROM countries")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"ℹ️ {count} کشور قبلاً در دیتابیس وجود دارد")
        return
    
    for country in COUNTRIES_DATA:
        # تعیین منابع اولیه
        if country.get('vip', False):
            money = 10000000
            oil = 1000
            gold = 1000
            iron = 5000
            stones = 5000
            wood = 5000
            food = 5000
            meat = 5000
            clothes = 5000
            population = 5000000
        else:
            money = 1000000
            oil = 100
            gold = 100
            iron = 500
            stones = 500
            wood = 500
            food = 500
            meat = 500
            clothes = 500
            population = 1000000
        
        cursor.execute('''
        INSERT INTO countries (
            name, flag, is_vip, has_strait, strait_name,
            money, oil, gold, iron, stones, wood, food, meat, clothes,
            population
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            country['name'],
            country['flag'],
            1 if country.get('vip', False) else 0,
            1 if country.get('strait', False) else 0,
            country.get('strait_name', ''),
            money, oil, gold, iron, stones, wood, food, meat, clothes,
            population
        ))
    
    conn.commit()
    print(f"✅ {len(COUNTRIES_DATA)} کشور با موفقیت اضافه شدند")

seed_countries()

# =============================================
# ۵. توابع کمکی اصلی
# =============================================

def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def is_owner(user_id: int) -> bool:
    """بررسی مالک بودن کاربر"""
    return user_id == ADMIN_ID

def get_country_by_user(user_id: int):
    """دریافت کشور کاربر"""
    cursor.execute("SELECT * FROM countries WHERE owner_id = ?", (user_id,))
    return cursor.fetchone()

def get_country_by_name(name: str):
    """دریافت کشور با نام"""
    cursor.execute("SELECT * FROM countries WHERE name = ?", (name,))
    return cursor.fetchone()

def get_country_by_id(country_id: int):
    """دریافت کشور با ID"""
    cursor.execute("SELECT * FROM countries WHERE id = ?", (country_id,))
    return cursor.fetchone()

def get_free_countries():
    """دریافت کشورهای بدون مالک"""
    cursor.execute("SELECT * FROM countries WHERE owner_id IS NULL")
    return cursor.fetchall()

def get_all_countries():
    """دریافت همه کشورها"""
    cursor.execute("SELECT * FROM countries")
    return cursor.fetchall()

def is_vip(user_id: int) -> bool:
    """بررسی VIP بودن کشور کاربر"""
    country = get_country_by_user(user_id)
    if not country:
        return False
    return country[3] == 1

def has_strait(user_id: int) -> bool:
    """بررسی داشتن تنگه/کانال"""
    country = get_country_by_user(user_id)
    if not country:
        return False
    return country[4] == 1

def get_strait_name(user_id: int) -> str:
    """دریافت نام تنگه/کانال"""
    country = get_country_by_user(user_id)
    if not country:
        return ""
    return country[5] or ""

def is_strait_open(user_id: int) -> bool:
    """بررسی باز بودن تنگه/کانال"""
    country = get_country_by_user(user_id)
    if not country:
        return True
    return country[6] == 1

def is_country_sanctioned(country_name: str) -> bool:
    """بررسی تحریم بودن کشور"""
    country = get_country_by_name(country_name)
    if not country:
        return False
    return country[7] == 1

def get_cities(country_id: int):
    """دریافت شهرهای یک کشور"""
    cursor.execute("SELECT * FROM cities WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_city(city_id: int):
    """دریافت اطلاعات یک شهر"""
    cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
    return cursor.fetchone()

def get_military_units(country_id: int):
    """دریافت واحدهای نظامی یک کشور"""
    cursor.execute("SELECT * FROM military_units WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_missiles(country_id: int):
    """دریافت موشک‌های یک کشور"""
    cursor.execute("SELECT * FROM missiles WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_defenses(country_id: int):
    """دریافت پدافندهای یک کشور"""
    cursor.execute("SELECT * FROM defenses WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_drones(country_id: int):
    """دریافت پهپادهای یک کشور"""
    cursor.execute("SELECT * FROM drones WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_cyber_units(country_id: int):
    """دریافت واحدهای سایبری یک کشور"""
    cursor.execute("SELECT * FROM cyber_units WHERE country_id = ?", (country_id,))
    return cursor.fetchall()

def get_price_multiplier(user_id: int) -> float:
    """محاسبه ضریب قیمت برای کاربر"""
    multiplier = 1.0
    
    country = get_country_by_user(user_id)
    if country and country[7] == 1:
        multiplier *= 1.3
    
    cursor.execute("SELECT COUNT(*) FROM countries WHERE has_strait = 1 AND is_strait_open = 0")
    closed = cursor.fetchone()[0]
    if closed > 0:
        multiplier *= (1 + (0.5 * closed))
    
    return multiplier

def get_price_with_multiplier(base_price: int, user_id: int) -> int:
    """دریافت قیمت با ضریب"""
    return int(base_price * get_price_multiplier(user_id))

def log_action(actor_id: int, action: str, target: str = '', detail: str = ''):
    """ثبت لاگ"""
    cursor.execute("""
        INSERT INTO logs (ts, actor_id, action, target, detail)
        VALUES (?, ?, ?, ?, ?)
    """, (int(time.time()), actor_id, action, target, detail))
    conn.commit()

# =============================================
# ۶. سیستم اقتصادی - درآمد نوبتی
# =============================================

def calculate_income(country_id: int) -> int:
    """محاسبه درآمد نوبتی کشور"""
    country = get_country_by_id(country_id)
    if not country:
        return 0
    
    # درآمد پایه
    base = 10000
    
    # پاداش جمعیت
    pop_bonus = int(country[18] / 1000) * 5
    
    # پاداش رضایت
    happy_bonus = int(country[19] / 10) * 100
    
    # درآمد از شهرها
    cities = get_cities(country_id)
    city_income = 0
    for city in cities:
        city_income += city[3] // 10  # جمعیت شهر / ۱۰
        city_income += city[4] * 5000  # زیرساخت
    
    total = base + pop_bonus + happy_bonus + city_income
    
    # اگر VIP باشد
    if country[3] == 1:
        total *= 2
    
    return int(total)

def calculate_oil_income(country_id: int) -> int:
    """محاسبه تولید نفت نوبتی"""
    country = get_country_by_id(country_id)
    if not country:
        return 0
    
    base = 5
    pop_bonus = int(country[18] / 10000)
    
    cities = get_cities(country_id)
    city_oil = sum(city[3] // 100000 for city in cities)
    
    total = base + pop_bonus + city_oil
    
    if country[3] == 1:
        total *= 2
    
    return int(total)

def process_turn():
    """پردازش یک نوبت - درآمد همه کشورها"""
    countries = get_all_countries()
    now = datetime.now()
    
    for country in countries:
        country_id = country[0]
        
        income = calculate_income(country_id)
        oil_income = calculate_oil_income(country_id)
        
        # اعمال درآمد
        cursor.execute("""
            UPDATE countries 
            SET money = money + ?, oil = oil + ?,
                population = population + ?,
                last_income = ?
            WHERE id = ?
        """, (
            income, oil_income,
            int(country[18] * 0.001) + 1,  # رشد جمعیت
            now.isoformat(),
            country_id
        ))
        conn.commit()
        
        log_action(0, 'turn_income', country[1], f'+{income} money, +{oil_income} oil')
    
    return len(countries)

# =============================================
# ۷. ترد پردازش نوبت
# =============================================

def turn_loop():
    """حلقه پردازش نوبت (هر ۱ ساعت)"""
    while True:
        try:
            count = process_turn()
            print(f"🔄 نوبت پردازش شد: {count} کشور")
        except Exception as e:
            print(f"❌ خطا در پردازش نوبت: {e}")
        time.sleep(3600)  # ۱ ساعت

def start_turn_thread():
    """شروع ترد پردازش نوبت"""
    thread = threading.Thread(target=turn_loop, daemon=True)
    thread.start()
    print("✅ ترد پردازش نوبت شروع شد")

# =============================================
# ۸. کامندهای اصلی
# =============================================

@bot.message_handler(commands=['start'])
def start_command(message):
    """دستور start - شروع بازی"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # بررسی آیا کاربر کشوری دارد
    country = get_country_by_user(user_id)
    
    if country:
        # کاربر قبلاً کشور دارد - نمایش منو
        menu = main_menu(user_id)
        bot.send_message(chat_id, 
            f"🎮 به بازی جنگ جهانی خوش آمدید!\n"
            f"🏳️ کشور شما: {country[2]} {country[1]}\n"
            f"⭐ VIP: {'بله' if country[3] else 'خیر'}\n"
            f"💰 پول: {country[10]:,}\n"
            f"🛢️ نفت: {country[11]}\n"
            f"👥 جمعیت: {country[18]:,}",
            reply_markup=menu, parse_mode='HTML')
    else:
        # ❌ کاربر کشور ندارد - پیام خطا
        bot.send_message(chat_id, 
            "❌ **شما هیچ کشوری ندارید!**\n\n"
            "برای دریافت کشور، لطفاً با یکی از ادمین‌های ربات تماس بگیرید.\n"
            "ادمین‌ها با دستور `/givecountry @username CountryName` به شما کشور می‌دهند.\n\n"
            "📋 **لیست کشورهای موجود:**",
            parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_command(message):
    """راهنمای بازی"""
    help_text = """
📚 **راهنمای بازی جنگ جهانی**

🎯 **هدف بازی:** تبدیل کشور خود به قدرتمندترین کشور جهان

🏳️ **کشورها:** ۱۰۰ کشور با پرچم و منابع مختلف

⭐ **VIP:** ۲۰ کشور برتر با منابع ۱۰ برابر

💰 **اقتصاد:** هر ۱ ساعت درآمد دریافت می‌کنید

🌍 **شهرها:** هر کشور می‌تواند تا ۵ شهر داشته باشد

⚔️ **نیروها:** خرید و استقرار نیروهای نظامی

🛡️ **پدافند:** حفاظت از شهرها در برابر حملات

🚀 **موشک‌ها:** حملات موشکی به دشمن

🛸 **پهپادها:** عملیات شناسایی و حمله

💻 **سایبری:** حملات و دفاع سایبری

🤝 **دیپلماسی:** اتحاد، پیمان، آتش‌بس

🕵️ **اطلاعات:** جاسوسی از کشورهای دیگر

⚔️ **جنگ:** اعلام جنگ و حمله به کشورهای دیگر

📍 **منوی اصلی:** /menu

👑 **کامندهای مدیریت:** فقط برای ادمین‌ها
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['menu'])
def menu_command(message):
    """نمایش منوی اصلی"""
    user_id = message.from_user.id
    
    country = get_country_by_user(user_id)
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید! از /start استفاده کنید.")
        return
    
    menu = main_menu(user_id)
    bot.send_message(message.chat.id, "📍 منوی اصلی", reply_markup=menu)

@bot.message_handler(commands=['mycountry'])
def my_country_command(message):
    """اطلاعات کشور من"""
    user_id = message.from_user.id
    
    country = get_country_by_user(user_id)
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    info = f"🏳️ {country[2]} **{country[1]}**\n"
    info += f"⭐ VIP: {'✅' if country[3] else '❌'}\n\n"
    info += f"💰 پول: {country[10]:,}\n"
    info += f"📈 درآمد هر نوبت: {calculate_income(country[0]):,}\n"
    info += f"🛢️ نفت: {country[11]}\n"
    info += f"📈 تولید نفت: {calculate_oil_income(country[0])}\n"
    info += f"👥 جمعیت: {country[18]:,}\n"
    info += f"😊 رضایت: {country[19]}%\n"
    info += f"⚔️ آمادگی نظامی: {country[20]}%\n\n"
    
    if country[4]:
        status = "🔓 باز" if country[6] else "🔒 بسته"
        info += f"🌊 {country[5]}: {status}\n"
    
    if country[7]:
        info += "🚫 **این کشور تحریم شده است!**\n"
    
    # آمار نظامی
    units = get_military_units(country[0])
    total_power = sum(u[5] * u[3] for u in units)  # power * count
    
    missiles = get_missiles(country[0])
    total_missile_power = sum(m[5] * m[3] for m in missiles)  # power * count
    
    info += f"\n⚔️ قدرت کل ارتش: {total_power:,}\n"
    info += f"🚀 قدرت کل موشکی: {total_missile_power:,}\n"
    info += f"🏙️ تعداد شهرها: {len(get_cities(country[0]))}"
    
    bot.reply_to(message, info, parse_mode='Markdown')

@bot.message_handler(commands=['countries'])
def countries_command(message):
    """لیست همه کشورها"""
    countries = get_all_countries()
    
    text = "🌍 **لیست کشورها:**\n\n"
    vip_count = 0
    normal_count = 0
    
    for c in countries:
        owner = "👤 گرفته شده" if c[9] else "🆓 آزاد"
        if c[3]:
            vip_count += 1
            text += f"⭐ {c[2]} {c[1]} - {owner}\n"
    
    text += f"\n⭐ VIP: {vip_count} کشور\n"
    text += f"📋 عادی: {len(countries) - vip_count} کشور"
    
    bot.reply_to(message, text, parse_mode='Markdown')

# =============================================
# ۹. منوهای Inline Keyboard
# =============================================

def main_menu(user_id: int) -> types.InlineKeyboardMarkup:
    """منوی اصلی"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        ("🌍 کشور من", f"country_{user_id}"),
        ("💰 اقتصاد", f"economy_{user_id}"),
        ("🏙️ شهرها", f"cities_{user_id}"),
        ("⚔️ ارتش", f"army_{user_id}"),
        ("✈️ نیروی هوایی", f"airforce_{user_id}"),
        ("🚢 نیروی دریایی", f"navy_{user_id}"),
        ("🛡️ پدافند", f"defense_{user_id}"),
        ("🚀 موشک‌ها", f"missiles_{user_id}"),
        ("🛸 پهپادها", f"drones_{user_id}"),
        ("💻 سایبری", f"cyber_{user_id}"),
        ("🤝 دیپلماسی", f"diplomacy_{user_id}"),
        ("🌐 تجارت", f"trade_{user_id}"),
        ("🕵️ اطلاعات", f"intel_{user_id}"),
        ("⚔️ جنگ", f"war_{user_id}"),
        ("🏳️ اتحادها", f"alliances_{user_id}"),
        ("📊 آمار", f"stats_{user_id}"),
    ]
    
    for label, callback in buttons:
        markup.add(types.InlineKeyboardButton(label, callback_data=callback))
    
    # دکمه پنل مدیریت برای ادمین‌ها
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🛡️ پنل مدیریت", callback_data=f"admin_panel_{user_id}"))
    
    return markup

# =============================================
# ۱۰. هندلرهای Callback Query
# =============================================

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """هندلر اصلی Callback Query"""
    user_id = call.from_user.id
    data = call.data
    chat_id = call.message.chat.id
    
    # ========== انتخاب کشور ==========
    if data.startswith('take_country_'):
        country_id = int(data.split('_')[2])
        country = get_country_by_id(country_id)
        
        if not country:
            bot.answer_callback_query(call.id, "❌ کشور یافت نشد!", show_alert=True)
            return
        
        if country[9] is not None:
            bot.answer_callback_query(call.id, "❌ این کشور قبلاً گرفته شده!", show_alert=True)
            return
        
        # بررسی اینکه کاربر قبلاً کشوری ندارد
        existing = get_country_by_user(user_id)
        if existing:
            bot.answer_callback_query(call.id, f"❌ شما قبلاً کشور {existing[1]} دارید!", show_alert=True)
            return
        
        # دادن کشور به کاربر
        cursor.execute("""
            UPDATE countries SET owner_id = ?, chat_id = ?
            WHERE id = ?
        """, (user_id, chat_id, country_id))
        conn.commit()
        
        log_action(user_id, 'take_country', country[1], '')
        
        bot.answer_callback_query(call.id, f"✅ کشور {country[1]} به شما داده شد!")
        
        # نمایش منوی اصلی
        menu = main_menu(user_id)
        bot.edit_message_text(
            f"🎮 به بازی خوش آمدید!\n🏳️ کشور شما: {country[2]} {country[1]}",
            chat_id, call.message.message_id,
            reply_markup=menu, parse_mode='HTML'
        )
    
    # ========== منوی اصلی ==========
    elif data.startswith('country_'):
        my_country_command(call.message)
        bot.answer_callback_query(call.id)
    
    elif data.startswith('economy_'):
        # منوی اقتصاد
        country = get_country_by_user(user_id)
        if not country:
            bot.send_message(chat_id, "❌ شما هیچ کشوری ندارید!")
            bot.answer_callback_query(call.id)
            return
        
        text = f"💰 **اقتصاد {country[2]} {country[1]}**\n\n"
        text += f"💵 پول: {country[10]:,}\n"
        text += f"📈 درآمد هر نوبت: {calculate_income(country[0]):,}\n"
        text += f"🛢️ نفت: {country[11]}\n"
        text += f"📈 تولید نفت: {calculate_oil_income(country[0])}\n"
        text += f"👥 جمعیت: {country[18]:,}\n"
        text += f"😊 رضایت: {country[19]}%\n"
        text += f"⚔️ آمادگی نظامی: {country[20]}%\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_menu_{user_id}"))
        
        bot.edit_message_text(text, chat_id, call.message.message_id, 
                             reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    # ========== شهرها ==========
    elif data.startswith('cities_'):
        country = get_country_by_user(user_id)
        if not country:
            bot.send_message(chat_id, "❌ شما هیچ کشوری ندارید!")
            bot.answer_callback_query(call.id)
            return
        
        cities = get_cities(country[0])
        
        if not cities:
            # ایجاد شهر پایتخت
            cursor.execute("""
                INSERT INTO cities (country_id, name, is_capital, population)
                VALUES (?, 'پایتخت', 1, 100000)
            """, (country[0],))
            conn.commit()
            cities = get_cities(country[0])
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for city in cities:
            markup.add(types.InlineKeyboardButton(
                f"🏙️ {city[2]} (جمعیت: {city[3]:,})",
                callback_data=f"city_{city[0]}"
            ))
        
        markup.add(types.InlineKeyboardButton("➕ شهر جدید", callback_data=f"new_city_{country[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_menu_{user_id}"))
        
        bot.edit_message_text(
            f"🏙️ **شهرهای {country[2]} {country[1]}**\n"
            f"📊 تعداد شهرها: {len(cities)}",
            chat_id, call.message.message_id,
            reply_markup=markup, parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
    
    elif data.startswith('city_'):
        city_id = int(data.split('_')[1])
        city = get_city(city_id)
        
        if not city:
            bot.answer_callback_query(call.id, "❌ شهر یافت نشد!")
            return
        
        text = f"🏙️ **{city[2]}**\n"
        text += f"👥 جمعیت: {city[3]:,}\n"
        text += f"🏗️ زیرساخت: سطح {city[4]}\n"
        text += f"🛡️ پدافند: سطح {city[5]}\n"
        text += f"⚡ نیروگاه: {'✅' if city[6] else '❌'}\n"
        text += f"🌐 اینترنت: {'✅' if city[7] else '❌'}\n"
        text += f"🚫 قرنطینه: {'✅' if city[8] else '❌'}\n"
        text += f"🏴 اشغال: {'✅' if city[9] else '❌'}\n"
        text += f"🏭 کارخانه‌ها: {len(json.loads(city[10] or '{}'))}\n"
        text += f"🏢 شرکت‌ها: {len(json.loads(city[11] or '{}'))}\n"
        text += f"🛡️ پدافند مستقر: {len(json.loads(city[12] or '[]'))}\n"
        text += f"⚔️ نیروهای مستقر: {sum(json.loads(city[13] or '{}').values())}\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏗️ زیرساخت", callback_data=f"build_infra_{city_id}"),
            types.InlineKeyboardButton("🛡️ پدافند", callback_data=f"build_defense_{city_id}")
        )
        markup.add(
            types.InlineKeyboardButton("⚡ نیروگاه", callback_data=f"build_power_{city_id}"),
            types.InlineKeyboardButton("🏭 کارخانه", callback_data=f"build_factory_{city_id}")
        )
        markup.add(
            types.InlineKeyboardButton("🏢 شرکت", callback_data=f"build_company_{city_id}"),
            types.InlineKeyboardButton("🔫 استقرار نیرو", callback_data=f"deploy_units_{city_id}")
        )
        markup.add(
            types.InlineKeyboardButton("🚫 قرنطینه", callback_data=f"quarantine_{city_id}"),
            types.InlineKeyboardButton("🌐 ملی کردن اینترنت", callback_data=f"nationalize_internet_{city_id}")
        )
        markup.add(
            types.InlineKeyboardButton("✏️ تغییر نام", callback_data=f"rename_city_{city_id}"),
            types.InlineKeyboardButton("🔙 بازگشت", callback_data=f"cities_{user_id}")
        )
        
        bot.edit_message_text(text, chat_id, call.message.message_id,
                             reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    # ========== ساخت شهر جدید ==========
    elif data.startswith('new_city_'):
        country_id = int(data.split('_')[2])
        
        # بررسی تعداد شهرها (حداکثر ۵)
        cities = get_cities(country_id)
        if len(cities) >= 5:
            bot.answer_callback_query(call.id, "❌ حداکثر ۵ شهر مجاز است!", show_alert=True)
            return
        
        # ایجاد شهر جدید
        cursor.execute("""
            INSERT INTO cities (country_id, name, population)
            VALUES (?, ?, ?)
        """, (country_id, f"شهر {len(cities) + 1}", 50000))
        conn.commit()
        
        bot.answer_callback_query(call.id, "✅ شهر جدید ایجاد شد!")
        
        # به‌روزرسانی منوی شهرها
        country = get_country_by_user(user_id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        for city in get_cities(country[0]):
            markup.add(types.InlineKeyboardButton(
                f"🏙️ {city[2]} (جمعیت: {city[3]:,})",
                callback_data=f"city_{city[0]}"
            ))
        markup.add(types.InlineKeyboardButton("➕ شهر جدید", callback_data=f"new_city_{country[0]}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_menu_{user_id}"))
        
        bot.edit_message_text(
            f"🏙️ **شهرهای {country[2]} {country[1]}**",
            chat_id, call.message.message_id,
            reply_markup=markup, parse_mode='Markdown'
        )
    
    # ========== ساختن زیرساخت ==========
    elif data.startswith('build_infra_'):
        city_id = int(data.split('_')[2])
        city = get_city(city_id)
        country = get_country_by_id(city[1])
        
        cost = 100000 * (city[4] + 1)
        
        if country[10] < cost:
            bot.answer_callback_query(call.id, f"❌ پول کافی نیست! نیاز به {cost:,} پول", show_alert=True)
            return
        
        # کسر پول و افزایش زیرساخت
        cursor.execute("""
            UPDATE countries SET money = money - ? WHERE id = ?
        """, (cost, country[0]))
        
        cursor.execute("""
            UPDATE cities SET infrastructure_level = infrastructure_level + 1
            WHERE id = ?
        """, (city_id,))
        conn.commit()
        
        log_action(user_id, 'build_infrastructure', city[2], f'level {city[4]+1}')
        bot.answer_callback_query(call.id, f"✅ زیرساخت به سطح {city[4]+1} ارتقا یافت!")
        
        # بازگشت به صفحه شهر
        callback_handler(call)  # این باعث بازگشت به منوی شهر میشه
    
    # ========== ساخت پدافند ==========
    elif data.startswith('build_defense_'):
        city_id = int(data.split('_')[2])
        city = get_city(city_id)
        country = get_country_by_id(city[1])
        
        cost = 200000 * (city[5] + 1)
        
        if country[10] < cost:
            bot.answer_callback_query(call.id, f"❌ پول کافی نیست! نیاز به {cost:,} پول", show_alert=True)
            return
        
        cursor.execute("""
            UPDATE countries SET money = money - ? WHERE id = ?
        """, (cost, country[0]))
        
        cursor.execute("""
            UPDATE cities SET defense_level = defense_level + 1
            WHERE id = ?
        """, (city_id,))
        conn.commit()
        
        log_action(user_id, 'build_defense', city[2], f'level {city[5]+1}')
        bot.answer_callback_query(call.id, f"✅ پدافند شهر به سطح {city[5]+1} ارتقا یافت!")
        callback_handler(call)

    # ========== پذیرش/رد تجارت ==========
    elif data.startswith('trade_accept_'):
        parts = data.split('_')
        from_id = int(parts[2])
        to_id = int(parts[3])
        goods = parts[4]
        amount = int(parts[5])
        
        from_country = get_country_by_id(from_id)
        to_country = get_country_by_id(to_id)
        
        # انتقال کالا
        if goods == 'oil':
            cursor.execute("""
                UPDATE countries SET oil = oil - ? WHERE id = ?
            """, (amount, from_id))
            cursor.execute("""
                UPDATE countries SET oil = oil + ? WHERE id = ?
            """, (amount, to_id))
        elif goods == 'money':
            cursor.execute("""
                UPDATE countries SET money = money - ? WHERE id = ?
            """, (amount, from_id))
            cursor.execute("""
                UPDATE countries SET money = money + ? WHERE id = ?
            """, (amount, to_id))
        else:
            resource_map = {'gold': 'gold', 'iron': 'iron', 'stones': 'stones', 
                           'wood': 'wood', 'food': 'food', 'meat': 'meat', 'clothes': 'clothes'}
            if goods in resource_map:
                col = resource_map[goods]
                cursor.execute(f"UPDATE countries SET {col} = {col} - ? WHERE id = ?", (amount, from_id))
                cursor.execute(f"UPDATE countries SET {col} = {col} + ? WHERE id = ?", (amount, to_id))
        
        conn.commit()
        
        log_action(user_id, 'trade_accept', f'{from_id}-{to_id}', f'{goods}={amount}')
        
        bot.answer_callback_query(call.id, "✅ تجارت تایید شد!")
        bot.edit_message_text("✅ تجارت تایید شد!", chat_id, call.message.message_id)
        
        bot.send_message(from_country[9], f"✅ تجارت {goods} با {to_country[1]} تایید شد!")
        bot.send_message(to_country[9], f"✅ تجارت {goods} با {from_country[1]} تکمیل شد!")
    
    elif data.startswith('trade_reject_'):
        bot.answer_callback_query(call.id, "❌ تجارت رد شد!")
        bot.edit_message_text("❌ تجارت رد شد!", chat_id, call.message.message_id)
    
    # ========== پذیرش/رد آتش‌بس ==========
    elif data.startswith('ceasefire_accept_'):
        war_id = int(data.split('_')[2])
        
        cursor.execute("""
            UPDATE wars SET status = 'ceasefire', ended_at = ? WHERE id = ?
        """, (datetime.now().isoformat(), war_id))
        conn.commit()
        
        war = cursor.fetchone()
        if war:
            bot.send_message(CHANNEL_ID, 
                f"🤝 **آتش‌بس!**\n"
                f"جنگ بین کشورها به پایان رسید."
            )
        
        bot.answer_callback_query(call.id, "✅ آتش‌بس پذیرفته شد!")
        bot.edit_message_text("✅ آتش‌بس پذیرفته شد!", chat_id, call.message.message_id)
    
    elif data.startswith('ceasefire_reject_'):
        bot.answer_callback_query(call.id, "❌ آتش‌بس رد شد!")
        bot.edit_message_text("❌ آتش‌بس رد شد!", chat_id, call.message.message_id)

    
    # ========== برگشت به منو ==========
    elif data.startswith('back_menu_'):
        menu = main_menu(user_id)
        bot.edit_message_text("📍 منوی اصلی", chat_id, call.message.message_id, reply_markup=menu)
        bot.answer_callback_query(call.id)
    
    # ========== پنل مدیریت ==========
    elif data.startswith('admin_panel_'):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ شما ادمین نیستید!", show_alert=True)
            return
        
        markup = admin_panel_menu()
        bot.edit_message_text("🛡️ **پنل مدیریت**", chat_id, call.message.message_id,
                             reply_markup=markup, parse_mode='Markdown')
        bot.answer_callback_query(call.id)
    
    else:
        bot.answer_callback_query(call.id, "❌ دستور نامعتبر!")

# =============================================
# ۱۱. پنل مدیریت
# =============================================

def admin_panel_menu() -> types.InlineKeyboardMarkup:
    """منوی پنل مدیریت"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        ("🌍 مدیریت کشورها", "admin_countries"),
        ("💰 مدیریت اقتصاد", "admin_economy"),
        ("⚔️ مدیریت نظامی", "admin_military"),
        ("🚀 مدیریت موشک‌ها", "admin_missiles"),
        ("⚙️ تنظیمات", "admin_settings"),
        ("📊 لاگ‌ها", "admin_logs"),
        ("🔙 بازگشت", "back_menu")
    ]
    
    for label, callback in buttons:
        markup.add(types.InlineKeyboardButton(label, callback_data=callback))
    
    return markup

# =============================================
# ۱۲. کامندهای ادمین
# =============================================

@bot.message_handler(commands=['givecountry'])
def give_country_command(message):
    """دادن کشور به کاربر - /givecountry @username CountryName"""
    
    # ✅ فقط ادمین‌ها
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ شما ادمین نیستید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /givecountry @username CountryName")
        return
    
    target = parts[1]
    country_name = " ".join(parts[2:])
    
    # تبدیل username به ID
    if target.startswith('@'):
        try:
            user = bot.get_chat(target)
            target_id = user.id
        except:
            bot.reply_to(message, "❌ کاربر یافت نشد!")
            return
    else:
        try:
            target_id = int(target)
        except:
            bot.reply_to(message, "❌ شناسه معتبر نیست!")
            return
    
    # بررسی اینکه کاربر قبلاً کشوری ندارد
    existing = get_country_by_user(target_id)
    if existing:
        bot.reply_to(message, f"❌ کاربر قبلاً کشور {existing[1]} رو داره!")
        return
    
    # بررسی وجود کشور
    country = get_country_by_name(country_name)
    if not country:
        bot.reply_to(message, f"❌ کشور {country_name} وجود ندارد!")
        return
    
    # بررسی آزاد بودن کشور
    if country[9] is not None:
        bot.reply_to(message, f"❌ کشور {country_name} قبلاً داده شده!")
        return
    
    # دادن کشور
    cursor.execute("""
        UPDATE countries SET owner_id = ?, chat_id = ?
        WHERE name = ?
    """, (target_id, target_id, country_name))
    conn.commit()
    
    log_action(message.from_user.id, 'give_country', country_name, str(target_id))
    bot.reply_to(message, f"✅ کشور {country_name} به کاربر داده شد!")
    
    # اطلاع به کاربر
    try:
        bot.send_message(target_id, 
            f"🎉 شما صاحب کشور **{country_name}** شدید!\n"
            f"برای شروع بازی از /start استفاده کنید."
        )
    except:
        pass
        
@bot.message_handler(commands=['freecountries'])
def free_countries_admin(message):
    """لیست کشورهای آزاد - /freecountries"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ شما ادمین نیستید!")
        return
    
    countries = get_free_countries()
    if not countries:
        bot.reply_to(message, "📭 هیچ کشور آزادی وجود ندارد!")
        return
    
    result = "📋 **کشورهای آزاد:**\n\n"
    for c in countries[:20]:
        vip = "⭐ VIP" if c[3] else ""
        result += f"🏳️ {c[2]} {c[1]} {vip}\n"
    
    if len(countries) > 20:
        result += f"\n... و {len(countries) - 20} کشور دیگر"
    
    bot.reply_to(message, result, parse_mode='Markdown')

# =============================================
# ۱۳. کامندهای مالک
# =============================================

@bot.message_handler(commands=['addadmin'])
def add_admin_command(message):
    """اضافه کردن ادمین - /addadmin 123456789"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند ادمین اضافه کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /addadmin 123456789")
        return
    
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ شناسه معتبر نیست!")
        return
    
    if is_admin(target_id):
        bot.reply_to(message, "❌ کاربر قبلاً ادمین است!")
        return
    
    cursor.execute("INSERT INTO admins (user_id, added_by) VALUES (?, ?)", (target_id, message.from_user.id))
    conn.commit()
    
    log_action(message.from_user.id, 'add_admin', str(target_id), '')
    bot.reply_to(message, f"✅ کاربر با ID {target_id} ادمین شد!")

@bot.message_handler(commands=['removeadmin'])
def remove_admin_command(message):
    """حذف ادمین - /removeadmin 123456789"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند ادمین حذف کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /removeadmin 123456789")
        return
    
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ شناسه معتبر نیست!")
        return
    
    if target_id == ADMIN_ID:
        bot.reply_to(message, "❌ نمی‌توانید خودتان را حذف کنید!")
        return
    
    if not is_admin(target_id):
        bot.reply_to(message, "❌ کاربر ادمین نیست!")
        return
    
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (target_id,))
    conn.commit()
    
    log_action(message.from_user.id, 'remove_admin', str(target_id), '')
    bot.reply_to(message, f"✅ کاربر با ID {target_id} از ادمین‌ها حذف شد!")

@bot.message_handler(commands=['addresource'])
def add_resource_command(message):
    """اضافه کردن به منابع - /addresource CountryName resource amount"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند منابع را تغییر دهد!")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ استفاده: /addresource Iran money 1000000")
        return
    
    country_name = parts[1]
    resource = parts[2]
    try:
        amount = int(parts[3])
    except:
        bot.reply_to(message, "❌ مقدار معتبر نیست!")
        return
    
    allowed = ['money', 'oil', 'gold', 'iron', 'stones', 'wood', 'food', 'meat', 'clothes']
    if resource not in allowed:
        bot.reply_to(message, f"❌ منبع {resource} معتبر نیست!")
        return
    
    cursor.execute(f"UPDATE countries SET {resource} = {resource} + ? WHERE name = ?", (amount, country_name))
    conn.commit()
    
    log_action(message.from_user.id, 'add_resource', country_name, f'{resource}+{amount}')
    bot.reply_to(message, f"✅ {amount:,} واحد به {resource} کشور {country_name} اضافه شد!")

@bot.message_handler(commands=['removeresource'])
def remove_resource_command(message):
    """کم کردن از منابع - /removeresource CountryName resource amount"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند منابع را تغییر دهد!")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ استفاده: /removeresource Iran money 100000")
        return
    
    country_name = parts[1]
    resource = parts[2]
    try:
        amount = int(parts[3])
    except:
        bot.reply_to(message, "❌ مقدار معتبر نیست!")
        return
    
    allowed = ['money', 'oil', 'gold', 'iron', 'stones', 'wood', 'food', 'meat', 'clothes']
    if resource not in allowed:
        bot.reply_to(message, f"❌ منبع {resource} معتبر نیست!")
        return
    
    cursor.execute(f"UPDATE countries SET {resource} = MAX(0, {resource} - ?) WHERE name = ?", (amount, country_name))
    conn.commit()
    
    log_action(message.from_user.id, 'remove_resource', country_name, f'{resource}-{amount}')
    bot.reply_to(message, f"✅ {amount:,} واحد از {resource} کشور {country_name} کم شد!")

@bot.message_handler(commands=['deleteuser'])
def delete_user_command(message):
    """حذف کاربر - /deleteuser 123456789"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند کاربر را حذف کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /deleteuser 123456789")
        return
    
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ شناسه معتبر نیست!")
        return
    
    # پاک کردن مالکیت کشور
    cursor.execute("UPDATE countries SET owner_id = NULL, chat_id = NULL WHERE owner_id = ?", (target_id,))
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (target_id,))
    conn.commit()
    
    log_action(message.from_user.id, 'delete_user', str(target_id), '')
    bot.reply_to(message, f"✅ کاربر با ID {target_id} حذف شد!")

@bot.message_handler(commands=['resetcountry'])
def reset_country_command(message):
    """ریست کردن کشور - /resetcountry Iran"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند کشور را ریست کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /resetcountry Iran")
        return
    
    country_name = parts[1]
    country = get_country_by_name(country_name)
    if not country:
        bot.reply_to(message, f"❌ کشور {country_name} وجود ندارد!")
        return
    
    # تنظیم مجدد کشور
    if country[3]:  # VIP
        money, oil = 10000000, 1000
    else:
        money, oil = 1000000, 100
    
    cursor.execute("""
        UPDATE countries 
        SET owner_id = NULL, chat_id = NULL,
            money = ?, oil = ?,
            population = 1000000, happiness = 70, military_readiness = 50
        WHERE name = ?
    """, (money, oil, country_name))
    conn.commit()
    
    log_action(message.from_user.id, 'reset_country', country_name, '')
    bot.reply_to(message, f"✅ کشور {country_name} ریست شد و آماده واگذاری مجدد است!")

@bot.message_handler(commands=['setvip'])
def set_vip_command(message):
    """تغییر وضعیت VIP - /setvip Iran true/false"""
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ فقط مالک می‌تواند وضعیت VIP را تغییر دهد!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /setvip Iran true")
        return
    
    country_name = parts[1]
    is_vip = parts[2].lower() == 'true'
    
    country = get_country_by_name(country_name)
    if not country:
        bot.reply_to(message, f"❌ کشور {country_name} وجود ندارد!")
        return
    
    cursor.execute("UPDATE countries SET is_vip = ? WHERE name = ?", (1 if is_vip else 0, country_name))
    conn.commit()
    
    log_action(message.from_user.id, 'set_vip', country_name, str(is_vip))
    status = "VIP" if is_vip else "عادی"
    bot.reply_to(message, f"✅ کشور {country_name} به حالت {status} تغییر یافت!")

# =============================================
# ۱۵. سیستم جنگ
# =============================================

@bot.message_handler(commands=['declarewar'])
def declare_war_command(message):
    """اعلام جنگ - /declarewar CountryName"""
    user_id = message.from_user.id
    attacker = get_country_by_user(user_id)
    
    if not attacker:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /declarewar Iran")
        return
    
    defender_name = parts[1]
    defender = get_country_by_name(defender_name)
    
    if not defender:
        bot.reply_to(message, f"❌ کشور {defender_name} وجود ندارد!")
        return
    
    if attacker[0] == defender[0]:
        bot.reply_to(message, "❌ نمی‌توانید به خودتان حمله کنید!")
        return
    
    if not defender[9]:  # owner_id
        bot.reply_to(message, "❌ این کشور بازیکن ندارد!")
        return
    
    # بررسی جنگ فعال
    cursor.execute("""
        SELECT * FROM wars 
        WHERE (attacker_id = ? AND defender_id = ? OR attacker_id = ? AND defender_id = ?)
        AND status IN ('declared', 'active')
    """, (attacker[0], defender[0], defender[0], attacker[0]))
    
    existing = cursor.fetchone()
    if existing:
        bot.reply_to(message, "❌ قبلاً جنگی بین این کشورها وجود دارد!")
        return
    
    # اعلام جنگ
    cursor.execute("""
        INSERT INTO wars (attacker_id, defender_id, status, declared_at)
        VALUES (?, ?, 'declared', ?)
    """, (attacker[0], defender[0], datetime.now().isoformat()))
    conn.commit()
    
    war_id = cursor.lastrowid
    log_action(user_id, 'declare_war', defender_name, f'war_id={war_id}')
    
    # اطلاع به کانال
    bot.send_message(CHANNEL_ID, 
        f"⚔️ **اعلام جنگ!**\n"
        f"{attacker[2]} {attacker[1]} به {defender[2]} {defender[1]} اعلام جنگ کرد!\n"
        f"🕐 زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    bot.reply_to(message, f"⚔️ جنگ بین {attacker[1]} و {defender[1]} اعلام شد!")

@bot.message_handler(commands=['attack'])
def attack_command(message):
    """حمله به کشور - /attack CountryName [ground/air/sea/missile/drone]"""
    user_id = message.from_user.id
    attacker = get_country_by_user(user_id)
    
    if not attacker:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /attack Iran ground")
        return
    
    defender_name = parts[1]
    attack_type = parts[2].lower()
    
    defender = get_country_by_name(defender_name)
    if not defender:
        bot.reply_to(message, f"❌ کشور {defender_name} وجود ندارد!")
        return
    
    # بررسی جنگ فعال
    cursor.execute("""
        SELECT * FROM wars 
        WHERE (attacker_id = ? AND defender_id = ? OR attacker_id = ? AND defender_id = ?)
        AND status IN ('declared', 'active')
    """, (attacker[0], defender[0], defender[0], attacker[0]))
    
    war = cursor.fetchone()
    if not war:
        bot.reply_to(message, "❌ ابتدا باید با /declarewar اعلام جنگ کنید!")
        return
    
    # محاسبه قدرت حمله
    attack_power = calculate_attack_power(attacker[0], attack_type)
    defense_power = calculate_defense_power(defender[0], attack_type)
    
    if attack_power == 0:
        bot.reply_to(message, f"❌ شما هیچ نیروی {attack_type} برای حمله ندارید!")
        return
    
    # محاسبه نتیجه
    damage, casualties, success = calculate_battle(attack_power, defense_power)
    
    # اعمال خسارت
    if success:
        # کاهش منابع دشمن
        cursor.execute("""
            UPDATE countries 
            SET money = MAX(0, money - ?),
                oil = MAX(0, oil - ?),
                happiness = MAX(0, happiness - ?),
                military_readiness = MAX(0, military_readiness - ?)
            WHERE id = ?
        """, (damage * 1000, damage // 2, damage // 10, damage // 20, defender[0]))
        conn.commit()
    
    # ثبت نتیجه
    cursor.execute("""
        UPDATE wars 
        SET aggressor_casualties = aggressor_casualties + ?,
            defender_casualties = defender_casualties + ?,
            aggressor_damage = aggressor_damage + ?,
            defender_damage = defender_damage + ?
        WHERE id = ?
    """, (casualties, casualties // 2, damage if success else 0, damage if success else 0, war[0]))
    conn.commit()
    
    log_action(user_id, 'attack', defender_name, f'type={attack_type}, damage={damage}')
    
    # گزارش نتیجه
    result = f"⚔️ **نتیجه حمله {attack_type}**\n"
    result += f"🎯 از: {attacker[2]} {attacker[1]}\n"
    result += f"🎯 به: {defender[2]} {defender[1]}\n"
    result += f"✅ موفقیت: {'✅ بله' if success else '❌ خیر'}\n"
    result += f"💥 خسارت: {damage}\n"
    result += f"💀 تلفات مهاجم: {casualties}\n"
    result += f"💀 تلفات مدافع: {casualties // 2}\n"
    
    bot.reply_to(message, result)

def calculate_attack_power(country_id: int, attack_type: str) -> int:
    """محاسبه قدرت حمله بر اساس نوع"""
    power = 0
    
    if attack_type == 'ground':
        units = get_military_units(country_id)
        ground_types = ['infantry', 'special_forces', 'm1_abrams', 'leopard_2a7', 't_90m', 
                       'challenger_3', 'leclerc', 'k2_black_panther', 'merkava_mk4', 'type_99a']
        for u in units:
            if u[2] in ground_types:
                power += u[5] * u[3]  # power * count
    
    elif attack_type == 'air':
        units = get_military_units(country_id)
        air_types = ['f_22_raptor', 'f_35_lightning', 'f_16', 'f_15', 'f_18', 
                    'rafale', 'eurofighter', 'su_35', 'su_57', 'j_20',
                    'b_1b', 'b_2', 'b_52', 'tu_160', 'h_6k']
        for u in units:
            if u[2] in air_types:
                power += u[5] * u[3]
    
    elif attack_type == 'missile':
        missiles = get_missiles(country_id)
        for m in missiles:
            power += m[5] * m[3]  # power * count
    
    elif attack_type == 'drone':
        drones = get_drones(country_id)
        for d in drones:
            power += d[5] * d[3]  # power * count
    
    # اعمال ضریب قیمت
    multiplier = get_price_multiplier(get_country_by_id(country_id)[9])
    power = int(power / multiplier)
    
    return power

def calculate_defense_power(country_id: int, attack_type: str) -> int:
    """محاسبه قدرت دفاع بر اساس نوع حمله"""
    power = 0
    
    # پدافندهای مستقر در شهرها
    cities = get_cities(country_id)
    for city in cities:
        deployed = json.loads(city[12] or '[]')
        for defense_id in deployed:
            cursor.execute("SELECT * FROM defenses WHERE id = ?", (defense_id,))
            defense = cursor.fetchone()
            if defense:
                power += defense[5] * 10  # intercept_chance * 10
    
    # دفاع طبیعی کشور
    country = get_country_by_id(country_id)
    power += country[20] * 10  # military_readiness
    
    return power

def calculate_battle(attack_power: int, defense_power: int) -> tuple:
    """محاسبه نتیجه نبرد"""
    total_power = attack_power + defense_power
    if total_power == 0:
        return 0, 0, False
    
    # شانس موفقیت
    success_chance = (attack_power / total_power) * 100
    success = random.random() * 100 < success_chance
    
    if success:
        damage = int(attack_power / 100) + random.randint(1, 10)
        casualties = int(attack_power / 50) + random.randint(1, 5)
    else:
        damage = int(defense_power / 200) + random.randint(0, 5)
        casualties = int(attack_power / 30) + random.randint(1, 10)
    
    return damage, casualties, success

# =============================================
# ۱۶. سیستم دیپلماسی
# =============================================

@bot.message_handler(commands=['alliance'])
def alliance_command(message):
    """ایجاد اتحاد - /alliance Name @member1 @member2"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ فقط ادمین می‌تواند اتحاد ایجاد کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /alliance Name @member1 @member2")
        return
    
    name = parts[1]
    members = []
    
    for part in parts[2:]:
        if part.startswith('@'):
            try:
                user = bot.get_chat(part)
                country = get_country_by_user(user.id)
                if country:
                    members.append(country[0])
            except:
                pass
    
    if len(members) < 2:
        bot.reply_to(message, "❌ حداقل ۲ عضو برای اتحاد نیاز است!")
        return
    
    cursor.execute("""
        INSERT INTO alliances (name, leader_id, members)
        VALUES (?, ?, ?)
    """, (name, members[0], json.dumps(members)))
    conn.commit()
    
    log_action(message.from_user.id, 'create_alliance', name, f'{len(members)} members')
    bot.reply_to(message, f"✅ اتحاد {name} با {len(members)} عضو ایجاد شد!")

@bot.message_handler(commands=['treaty'])
def treaty_command(message):
    """ایجاد پیمان - /treaty non_aggression @country1 @country2"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ فقط ادمین می‌تواند پیمان ایجاد کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ استفاده: /treaty non_aggression @country1 @country2")
        return
    
    treaty_type = parts[1]
    
    # پیدا کردن کشورها
    countries = []
    for part in parts[2:4]:
        if part.startswith('@'):
            try:
                user = bot.get_chat(part)
                country = get_country_by_user(user.id)
                if country:
                    countries.append(country[0])
            except:
                pass
    
    if len(countries) < 2:
        bot.reply_to(message, "❌ دو کشور معتبر پیدا نشد!")
        return
    
    cursor.execute("""
        INSERT INTO treaties (type, country1_id, country2_id, duration_days, expires_at)
        VALUES (?, ?, ?, 30, datetime('now', '+30 days'))
    """, (treaty_type, countries[0], countries[1]))
    conn.commit()
    
    log_action(message.from_user.id, 'create_treaty', treaty_type, f'{countries[0]}-{countries[1]}')
    bot.reply_to(message, f"✅ پیمان {treaty_type} بین دو کشور ایجاد شد!")

@bot.message_handler(commands=['ceasefire'])
def ceasefire_command(message):
    """آتش‌بس - /ceasefire CountryName"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /ceasefire Iran")
        return
    
    target_name = parts[1]
    target = get_country_by_name(target_name)
    
    if not target:
        bot.reply_to(message, f"❌ کشور {target_name} وجود ندارد!")
        return
    
    # پیدا کردن جنگ فعال
    cursor.execute("""
        SELECT * FROM wars 
        WHERE (attacker_id = ? AND defender_id = ? OR attacker_id = ? AND defender_id = ?)
        AND status IN ('declared', 'active')
    """, (country[0], target[0], target[0], country[0]))
    
    war = cursor.fetchone()
    if not war:
        bot.reply_to(message, "❌ جنگی بین این کشورها وجود ندارد!")
        return
    
    # درخواست آتش‌بس
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ پذیرش", callback_data=f"ceasefire_accept_{war[0]}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"ceasefire_reject_{war[0]}")
    )
    
    bot.send_message(target[9], 
        f"🤝 درخواست آتش‌بس از {country[2]} {country[1]}",
        reply_markup=markup
    )
    
    bot.reply_to(message, "📨 درخواست آتش‌بس ارسال شد!")

# =============================================
# ۱۷. سیستم کانال سوئز
# =============================================

@bot.message_handler(commands=['suez'])
def suez_command(message):
    """مدیریت کانال سوئز - /suez [status/open/close]"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    # فقط مصر می‌تواند کانال سوئز را مدیریت کند
    if country[1] != 'Egypt':
        bot.reply_to(message, "❌ فقط مصر می‌تواند کانال سوئز را مدیریت کند!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        # نمایش وضعیت
        cursor.execute("SELECT is_open, daily_revenue, toll_per_pass FROM suez_canal LIMIT 1")
        suez = cursor.fetchone()
        
        if suez:
            status = "🔓 باز" if suez[0] else "🔒 بسته"
            bot.reply_to(message, 
                f"🌊 **کانال سوئز**\n"
                f"وضعیت: {status}\n"
                f"💰 درآمد روزانه: {suez[1]:,}\n"
                f"🪙 عوارض هر عبور: {suez[2]:,}"
            )
        return
    
    action = parts[1].lower()
    
    if action == 'open':
        cursor.execute("UPDATE suez_canal SET is_open = 1, last_updated = ?", (datetime.now().isoformat(),))
        conn.commit()
        bot.reply_to(message, "🔓 کانال سوئز باز شد!")
        
        # اطلاع به کانال
        bot.send_message(CHANNEL_ID, "🌊 کانال سوئز **باز** شد! تجارت جهانی روان است.")
        
    elif action == 'close':
        cursor.execute("UPDATE suez_canal SET is_open = 0, last_updated = ?", (datetime.now().isoformat(),))
        conn.commit()
        bot.reply_to(message, "🔒 کانال سوئز بسته شد!")
        
        # اطلاع به کانال
        bot.send_message(CHANNEL_ID, "🌊 کانال سوئز **بسته** شد! تجارت جهانی مختل شده است.")
    
    else:
        bot.reply_to(message, "❌ استفاده: /suez [status/open/close]")

# =============================================
# ۱۸. سیستم اطلاعاتی
# =============================================

@bot.message_handler(commands=['spy'])
def spy_command(message):
    """جاسوسی - /spy CountryName [army/economy/cities]"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /spy Iran army")
        return
    
    target_name = parts[1]
    target = get_country_by_name(target_name)
    
    if not target:
        bot.reply_to(message, f"❌ کشور {target_name} وجود ندارد!")
        return
    
    spy_type = parts[2].lower()
    cost = 100000
    
    if country[10] < cost:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost:,} پول")
        return
    
    # کسر هزینه
    cursor.execute("UPDATE countries SET money = money - ? WHERE id = ?", (cost, country[0]))
    conn.commit()
    
    # شانس موفقیت
    success_chance = 60 + random.randint(0, 30)
    success = random.random() * 100 < success_chance
    
    result = f"🕵️ **عملیات جاسوسی**\n"
    result += f"🎯 از: {country[2]} {country[1]}\n"
    result += f"🎯 به: {target[2]} {target[1]}\n"
    result += f"📋 نوع: {spy_type}\n"
    result += f"✅ موفقیت: {'✅ بله' if success else '❌ خیر'}\n\n"
    
    if success and spy_type == 'army':
        units = get_military_units(target[0])
        result += "**⚔️ اطلاعات ارتش:**\n"
        for u in units:
            result += f"• {u[4]}: {u[3]} عدد (قدرت {u[5]})\n"
        
        missiles = get_missiles(target[0])
        if missiles:
            result += "\n**🚀 اطلاعات موشکی:**\n"
            for m in missiles:
                result += f"• {m[4]}: {m[3]} عدد (قدرت {m[5]})\n"
    
    elif success and spy_type == 'economy':
        result += f"**💰 اطلاعات اقتصادی:**\n"
        result += f"پول: {target[10]:,}\n"
        result += f"نفت: {target[11]}\n"
        result += f"طلا: {target[12]}\n"
        result += f"جمعیت: {target[18]:,}\n"
        result += f"رضایت: {target[19]}%\n"
        result += f"درآمد هر نوبت: {calculate_income(target[0]):,}"
    
    elif success and spy_type == 'cities':
        cities = get_cities(target[0])
        result += f"**🏙️ اطلاعات شهرها ({len(cities)} شهر):**\n"
        for city in cities:
            result += f"• {city[2]}: جمعیت {city[3]:,}\n"
    
    # ثبت عملیات
    cursor.execute("""
        INSERT INTO intelligence_ops (source_id, target_id, op_type, status, result)
        VALUES (?, ?, ?, ?, ?)
    """, (country[0], target[0], spy_type, 'completed' if success else 'failed', result))
    conn.commit()
    
    bot.reply_to(message, result)

# =============================================
# ۱۹. سیستم خرید
# =============================================

@bot.message_handler(commands=['buy'])
def buy_command(message):
    """خرید واحد - /buy unit_type count"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /buy infantry 100")
        return
    
    unit_type = parts[1]
    try:
        count = int(parts[2])
    except:
        bot.reply_to(message, "❌ تعداد معتبر نیست!")
        return
    
    # بررسی وجود واحد در دیتا
    if unit_type in UNITS_DATA:
        data = UNITS_DATA[unit_type]
        unit_name = data['name']
        power = data['power']
        cost_money = data['cost_money'] * count
        cost_oil = data['cost_oil'] * count
        build_time = data['build_time']
    else:
        bot.reply_to(message, f"❌ نوع {unit_type} وجود ندارد!")
        return
    
    # بررسی منابع
    if country[10] < cost_money:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost_money:,} پول")
        return
    
    if country[11] < cost_oil:
        bot.reply_to(message, f"❌ نفت کافی نیست! نیاز به {cost_oil} نفت")
        return
    
    # کسر منابع
    cursor.execute("""
        UPDATE countries 
        SET money = money - ?, oil = oil - ?
        WHERE id = ?
    """, (cost_money, cost_oil, country[0]))
    conn.commit()
    
    # بررسی وجود واحد از قبل
    cursor.execute("""
        SELECT * FROM military_units 
        WHERE country_id = ? AND unit_type = ?
    """, (country[0], unit_type))
    
    existing = cursor.fetchone()
    
    if existing:
        # افزایش تعداد
        cursor.execute("""
            UPDATE military_units 
            SET count = count + ?, is_ready = 0
            WHERE id = ?
        """, (count, existing[0]))
    else:
        # ایجاد واحد جدید
        cursor.execute("""
            INSERT INTO military_units (country_id, unit_type, count, name, power, 
                                       cost_money, cost_oil, build_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (country[0], unit_type, count, unit_name, power, 
              data['cost_money'], data['cost_oil'], build_time))
    
    conn.commit()
    
    log_action(user_id, 'buy_unit', unit_type, f'count={count}')
    
    bot.reply_to(message, 
        f"✅ **خرید موفق!**\n"
        f"🪖 {unit_name}: {count} عدد\n"
        f"💰 هزینه: {cost_money:,} پول\n"
        f"🛢️ هزینه نفت: {cost_oil}\n"
        f"⏱ زمان ساخت: {build_time} دقیقه\n"
        f"⚔️ قدرت کل: {power * count}"
    )

@bot.message_handler(commands=['buymissile'])
def buy_missile_command(message):
    """خرید موشک - /buymissile missile_type count"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /buymissile tomahawk 10")
        return
    
    missile_type = parts[1]
    try:
        count = int(parts[2])
    except:
        bot.reply_to(message, "❌ تعداد معتبر نیست!")
        return
    
    if missile_type in MISSILES_DATA:
        data = MISSILES_DATA[missile_type]
    else:
        bot.reply_to(message, f"❌ نوع {missile_type} وجود ندارد!")
        return
    
    cost_money = data['cost_money'] * count
    cost_oil = data['cost_oil'] * count
    
    if country[10] < cost_money:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost_money:,} پول")
        return
    
    if country[11] < cost_oil:
        bot.reply_to(message, f"❌ نفت کافی نیست! نیاز به {cost_oil} نفت")
        return
    
    cursor.execute("""
        UPDATE countries SET money = money - ?, oil = oil - ? WHERE id = ?
    """, (cost_money, cost_oil, country[0]))
    conn.commit()
    
    cursor.execute("""
        SELECT * FROM missiles WHERE country_id = ? AND missile_type = ?
    """, (country[0], missile_type))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE missiles SET count = count + ?, is_ready = 0 WHERE id = ?
        """, (count, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO missiles (country_id, missile_type, count, name, power, 
                                 range_km, cost_money, cost_oil, build_time_minutes, is_nuclear)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (country[0], missile_type, count, data['name'], data['power'],
              data['range'], cost_money // count, cost_oil // count,
              data['build_time'], 1 if data.get('nuclear', False) else 0))
    
    conn.commit()
    
    log_action(user_id, 'buy_missile', missile_type, f'count={count}')
    
    bot.reply_to(message, 
        f"✅ **خرید موشک موفق!**\n"
        f"🚀 {data['name']}: {count} عدد\n"
        f"💰 هزینه: {cost_money:,} پول\n"
        f"🛢️ هزینه نفت: {cost_oil}\n"
        f"💥 قدرت تخریب: {data['power'] * count}\n"
        f"📡 برد: {data['range']} کیلومتر"
    )

@bot.message_handler(commands=['buydefense'])
def buy_defense_command(message):
    """خرید پدافند - /buydefense defense_type count"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /buydefense patriot 5")
        return
    
    defense_type = parts[1]
    try:
        count = int(parts[2])
    except:
        bot.reply_to(message, "❌ تعداد معتبر نیست!")
        return
    
    if defense_type in DEFENSES_DATA:
        data = DEFENSES_DATA[defense_type]
    else:
        bot.reply_to(message, f"❌ نوع {defense_type} وجود ندارد!")
        return
    
    cost_money = data['cost_money'] * count
    cost_oil = data['cost_oil'] * count
    
    if country[10] < cost_money:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost_money:,} پول")
        return
    
    if country[11] < cost_oil:
        bot.reply_to(message, f"❌ نفت کافی نیست! نیاز به {cost_oil} نفت")
        return
    
    cursor.execute("""
        UPDATE countries SET money = money - ?, oil = oil - ? WHERE id = ?
    """, (cost_money, cost_oil, country[0]))
    conn.commit()
    
    cursor.execute("""
        SELECT * FROM defenses WHERE country_id = ? AND defense_type = ?
    """, (country[0], defense_type))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE defenses SET count = count + ?, is_ready = 0 WHERE id = ?
        """, (count, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO defenses (country_id, defense_type, count, name, intercept_chance,
                                 cost_money, cost_oil, build_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (country[0], defense_type, count, data['name'], data['intercept_chance'],
              data['cost_money'], data['cost_oil'], data['build_time']))
    
    conn.commit()
    
    log_action(user_id, 'buy_defense', defense_type, f'count={count}')
    
    bot.reply_to(message, 
        f"✅ **خرید پدافند موفق!**\n"
        f"🛡️ {data['name']}: {count} عدد\n"
        f"💰 هزینه: {cost_money:,} پول\n"
        f"🛢️ هزینه نفت: {cost_oil}\n"
        f"🎯 شانس رهگیری: {data['intercept_chance']}%"
    )

# =============================================
# ۲۰. آمار و گزارشات
# =============================================

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """آمار جهانی - /stats"""
    countries = get_all_countries()
    
    total_money = sum(c[10] for c in countries)
    total_oil = sum(c[11] for c in countries)
    total_population = sum(c[18] for c in countries)
    total_power = 0
    
    for c in countries:
        units = get_military_units(c[0])
        total_power += sum(u[5] * u[3] for u in units)
    
    # کشورهای دارای جنگ فعال
    cursor.execute("SELECT COUNT(*) FROM wars WHERE status IN ('declared', 'active')")
    active_wars = cursor.fetchone()[0]
    
    stats = f"📊 **آمار جهانی**\n\n"
    stats += f"🌍 تعداد کشورها: {len(countries)}\n"
    stats += f"💰 کل پول: {total_money:,}\n"
    stats += f"🛢️ کل نفت: {total_oil:,}\n"
    stats += f"👥 کل جمعیت: {total_population:,}\n"
    stats += f"⚔️ قدرت کل نظامی: {total_power:,}\n"
    stats += f"⚔️ جنگ‌های فعال: {active_wars}\n"
    
    # ۱۰ کشور برتر از نظر قدرت
    power_ranking = []
    for c in countries:
        units = get_military_units(c[0])
        power = sum(u[5] * u[3] for u in units)
        power_ranking.append((c[1], c[2], power))
    
    power_ranking.sort(key=lambda x: x[2], reverse=True)
    
    stats += "\n🏆 **۱۰ کشور برتر از نظر قدرت:**\n"
    for i, (name, flag, power) in enumerate(power_ranking[:10], 1):
        stats += f"{i}. {flag} {name}: {power:,}\n"
    
    bot.reply_to(message, stats, parse_mode='Markdown')

# =============================================
# ۲۱. شروع تردهای پس‌زمینه
# =============================================

def suez_income_thread():
    """درآمد روزانه کانال سوئز"""
    while True:
        try:
            cursor.execute("SELECT is_open, daily_revenue FROM suez_canal LIMIT 1")
            suez = cursor.fetchone()
            
            if suez and suez[0]:  # باز است
                revenue = suez[1] or 1000000
                
                # اضافه کردن به مصر
                cursor.execute("""
                    UPDATE countries 
                    SET money = money + ? 
                    WHERE name = 'Egypt'
                """, (revenue,))
                conn.commit()
                
                print(f"💰 درآمد کانال سوئز: +{revenue}")
        
        except Exception as e:
            print(f"❌ خطا در درآمد کانال سوئز: {e}")
        
        time.sleep(86400)  # هر ۲۴ ساعت

def start_suez_thread():
    """شروع ترد درآمد کانال سوئز"""
    thread = threading.Thread(target=suez_income_thread, daemon=True)
    thread.start()
    print("✅ ترد درآمد کانال سوئز شروع شد")
    
# =============================================
# ۲۳. سیستم خرید پهپاد
# =============================================

@bot.message_handler(commands=['buydrone'])
def buy_drone_command(message):
    """خرید پهپاد - /buydrone drone_type count"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "❌ استفاده: /buydrone shahed_136 10")
        return
    
    drone_type = parts[1]
    try:
        count = int(parts[2])
    except:
        bot.reply_to(message, "❌ تعداد معتبر نیست!")
        return
    
    if drone_type in DRONES_DATA:
        data = DRONES_DATA[drone_type]
    else:
        bot.reply_to(message, f"❌ نوع {drone_type} وجود ندارد!")
        return
    
    cost_money = data['cost_money'] * count
    cost_oil = data['cost_oil'] * count
    
    if country[10] < cost_money:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost_money:,} پول")
        return
    
    if country[11] < cost_oil:
        bot.reply_to(message, f"❌ نفت کافی نیست! نیاز به {cost_oil} نفت")
        return
    
    cursor.execute("""
        UPDATE countries SET money = money - ?, oil = oil - ? WHERE id = ?
    """, (cost_money, cost_oil, country[0]))
    conn.commit()
    
    cursor.execute("""
        SELECT * FROM drones WHERE country_id = ? AND drone_type = ?
    """, (country[0], drone_type))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE drones SET count = count + ?, is_ready = 0 WHERE id = ?
        """, (count, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO drones (country_id, drone_type, count, name, power, 
                               range_km, cost_money, cost_oil, build_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (country[0], drone_type, count, data['name'], data['power'],
              data['range'], data['cost_money'], data['cost_oil'], data['build_time']))
    
    conn.commit()
    
    log_action(user_id, 'buy_drone', drone_type, f'count={count}')
    
    bot.reply_to(message, 
        f"✅ **خرید پهپاد موفق!**\n"
        f"🛸 {data['name']}: {count} عدد\n"
        f"💰 هزینه: {cost_money:,} پول\n"
        f"🛢️ هزینه نفت: {cost_oil}\n"
        f"💥 قدرت: {data['power'] * count}\n"
        f"📡 برد: {data['range']} کیلومتر"
    )

# =============================================
# ۲۴. سیستم خرید سایبری
# =============================================

@bot.message_handler(commands=['buycyber'])
def buy_cyber_command(message):
    """خرید واحد سایبری - /buycyber level [beginner/intermediate/advanced/apt/elite]"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /buycyber advanced")
        return
    
    level = parts[1]
    
    if level in CYBER_DATA:
        data = CYBER_DATA[level]
    else:
        bot.reply_to(message, f"❌ سطح {level} وجود ندارد!")
        return
    
    cost_money = data['cost_money']
    cost_oil = data['cost_oil']
    
    if country[10] < cost_money:
        bot.reply_to(message, f"❌ پول کافی نیست! نیاز به {cost_money:,} پول")
        return
    
    if country[11] < cost_oil:
        bot.reply_to(message, f"❌ نفت کافی نیست! نیاز به {cost_oil} نفت")
        return
    
    cursor.execute("""
        UPDATE countries SET money = money - ?, oil = oil - ? WHERE id = ?
    """, (cost_money, cost_oil, country[0]))
    conn.commit()
    
    cursor.execute("""
        SELECT * FROM cyber_units WHERE country_id = ? AND cyber_level = ?
    """, (country[0], level))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE cyber_units SET is_ready = 0 WHERE id = ?
        """, (existing[0],))
    else:
        cursor.execute("""
            INSERT INTO cyber_units (country_id, cyber_level, name, attack_power, 
                                    defense_power, cost_money, cost_oil, build_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (country[0], level, data['name'], data['attack'], data['defense'],
              data['cost_money'], data['cost_oil'], data['build_time']))
    
    conn.commit()
    
    log_action(user_id, 'buy_cyber', level, '')
    
    bot.reply_to(message, 
        f"✅ **خرید واحد سایبری موفق!**\n"
        f"💻 {data['name']}: ۱ واحد\n"
        f"💰 هزینه: {cost_money:,} پول\n"
        f"🛢️ هزینه نفت: {cost_oil}\n"
        f"⚔️ قدرت حمله: {data['attack']}\n"
        f"🛡️ قدرت دفاع: {data['defense']}"
    )

# =============================================
# ۲۵. سیستم حمله سایبری
# =============================================

@bot.message_handler(commands=['cyberattack'])
def cyber_attack_command(message):
    """حمله سایبری - /cyberattack CountryName"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ استفاده: /cyberattack Iran")
        return
    
    target_name = parts[1]
    target = get_country_by_name(target_name)
    
    if not target:
        bot.reply_to(message, f"❌ کشور {target_name} وجود ندارد!")
        return
    
    # دریافت واحد سایبری کشور
    cyber_units = get_cyber_units(country[0])
    if not cyber_units:
        bot.reply_to(message, "❌ شما هیچ واحد سایبری ندارید! از /buycyber استفاده کنید.")
        return
    
    # بهترین واحد را انتخاب کنید
    best_unit = max(cyber_units, key=lambda x: x[5])  # attack_power
    attack_power = best_unit[5]  # attack_power
    
    # دفاع سایبری هدف
    target_cyber = get_cyber_units(target[0])
    defense_power = 0
    if target_cyber:
        defense_power = max(target_cyber, key=lambda x: x[6])[6]  # defense_power
    
    # محاسبه نتیجه
    success_chance = attack_power / (attack_power + defense_power + 1) * 100
    success = random.random() * 100 < success_chance
    
    damage = 0
    if success:
        damage = random.randint(1, 20)
        # اعمال خسارت سایبری
        cursor.execute("""
            UPDATE countries 
            SET happiness = MAX(0, happiness - ?),
                money = MAX(0, money - ?),
                military_readiness = MAX(0, military_readiness - ?)
            WHERE id = ?
        """, (damage, damage * 10000, damage // 2, target[0]))
        conn.commit()
    
    log_action(user_id, 'cyber_attack', target_name, f'success={success}, damage={damage}')
    
    result = f"💻 **حمله سایبری**\n"
    result += f"🎯 از: {country[2]} {country[1]}\n"
    result += f"🎯 به: {target[2]} {target[1]}\n"
    result += f"⚔️ قدرت حمله: {attack_power}\n"
    result += f"🛡️ قدرت دفاع: {defense_power}\n"
    result += f"✅ موفقیت: {'✅ بله' if success else '❌ خیر'}\n"
    if success:
        result += f"💥 خسارت وارد شده: {damage}%\n"
        result += f"💰 پول از دست رفته: {damage * 10000:,}\n"
        result += f"😊 کاهش رضایت: {damage}%"
    
    bot.reply_to(message, result)

# =============================================
# ۲۶. سیستم استقرار نیرو در شهر
# =============================================

@bot.message_handler(commands=['deploy'])
def deploy_command(message):
    """استقرار نیرو در شهر - /deploy unit_type count city_name"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ استفاده: /deploy infantry 100 تهران")
        return
    
    unit_type = parts[1]
    try:
        count = int(parts[2])
    except:
        bot.reply_to(message, "❌ تعداد معتبر نیست!")
        return
    
    city_name = " ".join(parts[3:])
    
    # پیدا کردن شهر
    cities = get_cities(country[0])
    target_city = None
    for city in cities:
        if city[2] == city_name:
            target_city = city
            break
    
    if not target_city:
        bot.reply_to(message, f"❌ شهر {city_name} یافت نشد!")
        return
    
    # بررسی وجود واحد
    cursor.execute("""
        SELECT * FROM military_units 
        WHERE country_id = ? AND unit_type = ?
    """, (country[0], unit_type))
    
    unit = cursor.fetchone()
    if not unit:
        bot.reply_to(message, f"❌ شما {unit_type} ندارید!")
        return
    
    if unit[3] < count:
        bot.reply_to(message, f"❌ شما فقط {unit[3]} عدد {unit_type} دارید!")
        return
    
    # کاهش از واحد اصلی
    cursor.execute("""
        UPDATE military_units SET count = count - ? WHERE id = ?
    """, (count, unit[0]))
    
    # اضافه کردن به شهر
    deployed = json.loads(target_city[13] or '{}')
    deployed[unit_type] = deployed.get(unit_type, 0) + count
    
    cursor.execute("""
        UPDATE cities SET deployed_units = ? WHERE id = ?
    """, (json.dumps(deployed), target_city[0]))
    conn.commit()
    
    log_action(user_id, 'deploy_units', f'{city_name}-{unit_type}', f'count={count}')
    
    bot.reply_to(message, 
        f"✅ **استقرار نیرو موفق!**\n"
        f"🪖 {unit[4]}: {count} عدد\n"
        f"🏙️ مستقر در: {city_name}\n"
        f"📊 باقی‌مانده: {unit[3] - count} عدد"
    )

# =============================================
# ۲۷. سیستم تجارت
# =============================================

@bot.message_handler(commands=['trade'])
def trade_command(message):
    """درخواست تجارت - /trade @country goods amount"""
    user_id = message.from_user.id
    country = get_country_by_user(user_id)
    
    if not country:
        bot.reply_to(message, "❌ شما هیچ کشوری ندارید!")
        return
    
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "❌ استفاده: /trade @country oil 100")
        return
    
    target = parts[1]
    goods = parts[2]
    try:
        amount = int(parts[3])
    except:
        bot.reply_to(message, "❌ مقدار معتبر نیست!")
        return
    
    if target.startswith('@'):
        try:
            user = bot.get_chat(target)
            target_country = get_country_by_user(user.id)
            if not target_country:
                bot.reply_to(message, "❌ کاربر مورد نظر کشوری ندارد!")
                return
        except:
            bot.reply_to(message, "❌ کاربر یافت نشد!")
            return
    else:
        bot.reply_to(message, "❌ از @username استفاده کنید!")
        return
    
    # بررسی منابع
    if goods == 'oil' and country[11] < amount:
        bot.reply_to(message, f"❌ نفت کافی نیست! شما {country[11]} نفت دارید.")
        return
    elif goods == 'money' and country[10] < amount:
        bot.reply_to(message, f"❌ پول کافی نیست! شما {country[10]:,} پول دارید.")
        return
    else:
        # بررسی سایر منابع
        resource_map = {'gold': 12, 'iron': 13, 'stones': 14, 'wood': 15, 
                       'food': 16, 'meat': 17, 'clothes': 18}
        if goods in resource_map:
            idx = resource_map[goods]
            if country[idx] < amount:
                bot.reply_to(message, f"❌ {goods} کافی نیست!")
                return
        else:
            bot.reply_to(message, f"❌ کالای {goods} معتبر نیست!")
            return
    
    # ارسال درخواست تجارت
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ پذیرش", callback_data=f"trade_accept_{country[0]}_{target_country[0]}_{goods}_{amount}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"trade_reject_{country[0]}_{target_country[0]}")
    )
    
    bot.send_message(target_country[9], 
        f"🌐 **درخواست تجارت**\n"
        f"از: {country[2]} {country[1]}\n"
        f"کالا: {goods}\n"
        f"مقدار: {amount}\n"
        f"💰 قیمت پیشنهادی: {amount * 1000:,} پول",
        reply_markup=markup
    )
    
    bot.reply_to(message, f"📨 درخواست تجارت به {target_country[1]} ارسال شد!")


# =============================================
# ۲۹. سیستم اعلان‌ها و پیام‌های خودکار
# =============================================

def send_notification(user_id: int, message: str):
    """ارسال اعلان به کاربر"""
    try:
        bot.send_message(user_id, message, parse_mode='HTML')
    except:
        pass

def check_wars():
    """بررسی جنگ‌های فعال و ارسال اعلان"""
    cursor.execute("""
        SELECT * FROM wars WHERE status IN ('declared', 'active')
    """)
    wars = cursor.fetchall()
    
    for war in wars:
        attacker = get_country_by_id(war[1])
        defender = get_country_by_id(war[2])
        
        if attacker and defender:
            # ارسال اعلان به هر دو طرف
            send_notification(attacker[9], 
                f"⚔️ **جنگ فعال**\n"
                f"شما در جنگ با {defender[2]} {defender[1]} هستید!"
            )
            send_notification(defender[9], 
                f"⚔️ **جنگ فعال**\n"
                f"شما در جنگ با {attacker[2]} {attacker[1]} هستید!"
            )

# =============================================
# ۳۰. اجرای نهایی
# =============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🌍 WAR BOT - Telegram World War Strategy Game")
    print("=" * 60)
    print(f"👑 مالک: {ADMIN_ID}")
    print(f"🌍 تعداد کشورها: {len(get_all_countries())}")
    print(f"⭐ VIP: {len([c for c in get_all_countries() if c[3]])}")
    print(f"🏙️ تعداد شهرها: {sum(len(get_cities(c[0])) for c in get_all_countries())}")
    print("=" * 60)
    
    # شروع تردها
    start_turn_thread()
    start_suez_thread()
    
    # اجرای ربات
    try:
        print("🚀 ربات در حال اجراست...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد")
    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        conn.close()
        print("✅ دیتابیس بسته شد")
