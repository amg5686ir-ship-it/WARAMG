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

