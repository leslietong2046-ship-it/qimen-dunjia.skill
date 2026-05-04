#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘工具
时家奇门转盘法，支持阳遁/阴遁十八局

使用方法：
    python qimen.py --question "我要创业能成吗"
    python qimen.py --time "2026-05-03 14:30"
    python qimen.py --question "感情" --time "2026-05-03 14:30"
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import argparse

# ============================================================
# 常量定义
# ============================================================

# 九宫排列（后天八卦）
# 洛书：戴九履一，左三右七，二四为肩，八六为足
PALACE_ORDER = [
    (4, '巽', '东南'),  # 巽四宫 - index 0
    (9, '离', '南'),    # 离九宫 - index 1
    (2, '坤', '西南'),  # 坤二宫 - index 2
    (3, '震', '东'),    # 震三宫 - index 3
    (5, '中', '中央'),  # 中五宫 - index 4
    (7, '兑', '西'),    # 兑七宫 - index 5
    (8, '艮', '东北'),  # 艮八宫 - index 6
    (1, '坎', '北'),    # 坎一宫 - index 7
    (6, '乾', '西北'),  # 乾六宫 - index 8
]

# 宫位数字到索引的映射
PALACE_NUM_TO_IDX = {4: 0, 9: 1, 2: 2, 3: 3, 5: 4, 7: 5, 8: 6, 1: 7, 6: 8}

# 索引到宫位数字的映射
PALACE_IDX_TO_NUM = {0: 4, 1: 9, 2: 2, 3: 3, 4: 5, 5: 7, 6: 8, 7: 1, 8: 6}

# 三奇六仪（顺序固定）
SANQI_LIUYI = ['戊', '己', '庚', '辛', '壬', '癸', '丁', '丙', '乙']

# 九星（按顺序对应1-9宫的天盘原始位置）
JIUXING = ['天蓬', '天任', '天冲', '天辅', '天禽', '天心', '天柱', '天英', '天芮']

# 八门（按顺序对应1-9宫的人盘原始位置）
BAMEN = ['休门', '死门', '伤门', '杜门', '中门', '开门', '惊门', '生门', '景门']

# 八神（阳遁顺排）
BASHEN_YANG = ['值符', '螣蛇', '太阴', '六合', '白虎', '玄武', '九地', '九天']
BASHEN_YIN = ['值符', '玄武', '白虎', '六合', '太阴', '螣蛇', '九地', '九天']

# 天干
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']

# 地支
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 地支对应宫位数字
DIZHI_PALACE = {
    '子': 1, '丑': 8, '寅': 3, '卯': 4, '辰': 5, '巳': 4,
    '午': 9, '未': 2, '申': 7, '酉': 7, '戌': 5, '亥': 6
}

# 旬首表（旬首->对应数字）
XUNSHOU = {
    '甲子': 1, '甲戌': 2, '甲申': 3, '甲午': 4, '甲辰': 5, '甲寅': 6
}

# 旬首对应天干
XUNSHOU_TIANGAN = {
    '甲子': '戊', '甲戌': '己', '甲申': '庚', '甲午': '辛', '甲辰': '壬', '甲寅': '癸'
}

# 天干对应数字
TIANGAN_NUM = {t: i+1 for i, t in enumerate(TIANGAN)}

# 天干对应地支（简化版60甲子表的部分映射）
# 这里使用简化计算
TIANGAN_DIZHI_PAIRS = [
    '甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳', '庚午', '辛未', '壬申', '癸酉',
    '甲戌', '乙亥', '丙子', '丁丑', '戊寅', '己卯', '庚辰', '辛巳', '壬午', '癸未',
    '甲申', '乙酉', '丙戌', '丁亥', '戊子', '己丑', '庚寅', '辛卯', '壬辰', '癸巳',
    '甲午', '乙未', '丙申', '丁酉', '戊戌', '己亥', '庚子', '辛丑', '壬寅', '癸卯',
    '甲辰', '乙巳', '丙午', '丁未', '戊申', '己酉', '庚戌', '辛亥', '壬子', '癸丑',
    '甲寅', '乙卯', '丙辰', '丁巳', '戊午', '己未', '庚申', '辛酉', '壬戌', '癸亥'
]

# 节气表（简化）
JIEQI_YANG = {
    '冬至': 1, '小寒': 2, '大寒': 3, '立春': 8, '雨水': 9, '惊蛰': 1,
    '春分': 3, '清明': 4, '谷雨': 5, '立夏': 4, '小满': 5, '芒种': 6
}

JIEQI_YIN = {
    '夏至': 9, '小暑': 8, '大暑': 7, '立秋': 2, '处暑': 1, '白露': 9,
    '秋分': 7, '寒露': 6, '霜降': 5, '立冬': 6, '小雪': 5, '大雪': 4
}

# 节气顺序
JIEQI_ORDER = [
    '冬至', '小寒', '大寒', '立春', '雨水', '惊蛰',
    '春分', '清明', '谷雨', '立夏', '小满', '芒种',
    '夏至', '小暑', '大暑', '立秋', '处暑', '白露',
    '秋分', '寒露', '霜降', '立冬', '小雪', '大雪'
]

# 九宫五行
WUXING_PALACE = {
    1: '水', 2: '土', 3: '木', 4: '木', 5: '土',
    6: '金', 7: '金', 8: '土', 9: '火'
}

# 五行相生
WUXING_SHENG = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木'
}

# 五行相克
WUXING_KE = {
    '木': '土', '土': '水', '水': '火', '火': '金', '金': '木'
}

# 八门五行
WUXING_BAMEN = {
    '休门': '水', '生门': '土', '伤门': '木', '杜门': '木',
    '景门': '火', '死门': '土', '惊门': '金', '开门': '金'
}

# 九星五行
WUXING_JIUXING = {
    '天蓬': '水', '天任': '土', '天冲': '木', '天辅': '木',
    '天禽': '土', '天心': '金', '天柱': '金', '天英': '火', '天芮': '土'
}

# 用神表
YONGSHEN = {
    '求财': {'main': ['生门', '戊'], 'sub': ['甲子戊'], 'desc': '求财'},
    '求职': {'main': ['开门', '天心'], 'sub': ['值符'], 'desc': '求职'},
    '升职': {'main': ['开门', '天辅'], 'sub': ['值符'], 'desc': '升职'},
    '感情': {'main': ['乙', '庚', '六合'], 'sub': ['丁', '壬'], 'desc': '感情'},
    '婚姻': {'main': ['乙', '庚', '六合'], 'sub': ['丁', '壬'], 'desc': '婚姻'},
    '出行': {'main': ['景门', '天冲'], 'sub': ['壬', '癸'], 'desc': '出行'},
    '考试': {'main': ['天辅', '景门'], 'sub': ['丁', '壬'], 'desc': '考试'},
    '文书': {'main': ['景门', '丁'], 'sub': ['壬'], 'desc': '文书'},
    '官司': {'main': ['惊门', '天柱'], 'sub': ['庚', '壬'], 'desc': '官司'},
    '诉讼': {'main': ['惊门', '开门'], 'sub': ['值符'], 'desc': '诉讼'},
    '疾病': {'main': ['天芮', '死门'], 'sub': ['乙', '辛', '天心'], 'desc': '疾病'},
    '健康': {'main': ['天芮', '天心'], 'sub': ['乙', '辛'], 'desc': '健康'},
    '事业': {'main': ['开门', '值符'], 'sub': ['甲子戊'], 'desc': '事业'},
    '创业': {'main': ['开门', '生门'], 'sub': ['甲子戊'], 'desc': '创业'},
    '合作': {'main': ['六合', '生门'], 'sub': ['甲子戊'], 'desc': '合作'},
    '买房': {'main': ['生门', '天任'], 'sub': ['甲子戊'], 'desc': '买房'},
    '学业': {'main': ['天辅', '景门'], 'sub': ['乙'], 'desc': '学业'},
    '官运': {'main': ['开门', '值符'], 'sub': ['天心'], 'desc': '官运'},
    '投资': {'main': ['生门', '甲子戊'], 'sub': ['玄武'], 'desc': '投资'},
    '失物': {'main': ['玄武', '杜门'], 'sub': ['壬', '癸'], 'desc': '失物'},
}

# 吉格表
JIGE = {
    ('戊', '丙'): '龙回首（青龙返首）- 谋事大吉',
    ('丙', '戊'): '鸟跌穴（飞鸟跌穴）- 百事洞彻',
    ('乙', '辛'): '龙逃走 - 破财之象',
    ('辛', '乙'): '虎猖狂 - 主客两伤',
    ('癸', '丁'): '蛇夭矫 - 虚惊不宁',
    ('丁', '癸'): '雀投江 - 文书口舌',
    ('庚', '丙'): '白入荧 - 贼来偷营',
    ('丙', '庚'): '荧入白 - 贼自退去',
    ('庚', '癸'): '大格 - 百事皆凶',
    ('庚', '壬'): '小格 - 远行失迷',
    ('庚', '己'): '刑格 - 官司破财',
    ('庚', '乙'): '合格 - 合作之象',
    ('庚', '丁'): '破格 - 破财',
    ('庚', '辛'): '龙虎 - 争斗',
}

# ============================================================
# 工具函数
# ============================================================

def lunar_year_to_ganzhi(year: int) -> str:
    """简化版：根据年份获取年干支"""
    # 以1984年为甲子年计算
    base_year = 1984
    base_ganzhi = 0  # 甲子
    diff = year - base_year
    idx = (diff % 60 + 60) % 60
    return TIANGAN_DIZHI_PAIRS[idx]

def get_month_ganzhi(year: int, month: int) -> str:
    """简化版：根据年月获取月干支"""
    # 以甲己年起月为准
    month_stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    year_stem_idx = TIANGAN_NUM[lunar_year_to_ganzhi(year)[0]] - 1
    # 月干 = (年干序号 + 月份 - 1) % 10
    month_stem_idx = (year_stem_idx + month + 1) % 10
    if month_stem_idx == 0:
        month_stem_idx = 9
    month_branch_idx = (month + 1) % 12  # 正月为寅
    if month_branch_idx == 0:
        month_branch_idx = 11
    return month_stems[month_stem_idx] + DIZHI[month_branch_idx]

def get_day_ganzhi(dt: datetime) -> str:
    """根据日期获取日干支（简化算法）"""
    # 使用儒略日计算
    # 基准：2000年1月1日是庚辰日
    base_date = datetime(2000, 1, 1)
    base_ganzhi = 16  # 庚辰的索引 (6, 0) -> 6*10 + 0 不对，用58
    # 2000-01-01 是 庚辰 (6, 4) -> 索引 54
    # 简化：直接用固定的偏移
    days_diff = (dt - base_date).days
    # 庚辰在60甲子中的索引是 36 (0-based)
    base_idx = 36
    idx = (base_idx + days_diff) % 60
    return TIANGAN_DIZHI_PAIRS[idx]

def get_hour_ganzhi(day_ganzhi: str, hour: int) -> str:
    """根据日干支和小时获取时干支"""
    # 子时 = 23:00-00:59，对应 hour = 0
    # 子时为一天之始
    day_stem = day_ganzhi[0]
    day_stem_idx = TIANGAN_NUM[day_stem] - 1
    
    # 时干 = (日干序号 * 2 + 时支序号 - 1) % 10
    hour_idx = (hour - 23) // 2 if hour >= 23 else (hour + 1) // 2
    if hour_idx == 0:
        hour_idx = 11  # 子时
    
    # 子丑寅卯辰巳午未申酉戌亥
    # 子=0, 丑=1, 寅=2, ...
    zhi_to_idx = {z: i for i, z in enumerate(DIZHI)}
    zhi_idx = zhi_to_idx[DIZHI[(hour_idx - 1) % 12]]
    
    hour_stem_idx = (day_stem_idx * 2 + zhi_idx) % 10
    
    return TIANGAN[hour_stem_idx] + DIZHI[zhi_idx]

def get_xunsho(ganzhi: str) -> str:
    """根据干支获取旬首"""
    stem = ganzhi[0]
    branch = ganzhi[1]
    stem_idx = TIANGAN_NUM[stem] - 1
    branch_idx = DIZHI.index(branch)
    
    # 计算差额确定旬
    diff = branch_idx - stem_idx
    if diff < 0:
        diff += 12
    
    # 60甲子分六旬，每旬10天
    ganzhi_idx = TIANGAN_DIZHI_PAIRS.index(ganzhi) if ganzhi in TIANGAN_DIZHI_PAIRS else 0
    xun_num = ganzhi_idx // 10
    
    xun_map = {0: '甲子', 1: '甲戌', 2: '甲申', 3: '甲午', 4: '甲辰', 5: '甲寅'}
    return xun_map[xun_num]

def get_jieqi(dt: datetime) -> str:
    """根据日期获取节气（简化版）"""
    month = dt.month
    day = dt.day
    
    jieqi_map = {
        (1, 6): '小寒', (1, 21): '大寒',
        (2, 4): '立春', (2, 19): '雨水',
        (3, 6): '惊蛰', (3, 21): '春分',
        (4, 5): '清明', (4, 20): '谷雨',
        (5, 6): '立夏', (5, 21): '小满',
        (6, 6): '芒种', (6, 21): '夏至',
        (7, 7): '小暑', (7, 23): '大暑',
        (8, 8): '立秋', (8, 23): '处暑',
        (9, 8): '白露', (9, 23): '秋分',
        (10, 8): '寒露', (10, 23): '霜降',
        (11, 7): '立冬', (11, 22): '小雪',
        (12, 7): '大雪', (12, 22): '冬至',
    }
    
    for key, jq in jieqi_map.items():
        if key[0] == month and abs(key[1] - day) <= 1:
            return jq
    
    # 简单按月分配
    default_jieqi = {
        1: '小寒', 2: '立春', 3: '春分', 4: '清明', 5: '立夏', 6: '芒种',
        7: '小暑', 8: '立秋', 9: '秋分', 10: '寒露', 11: '立冬', 12: '大雪'
    }
    return default_jieqi.get(month, '冬至')

def get_yuan_for_jieqi(jieqi: str, dt: datetime) -> int:
    """根据节气获取上中下元"""
    day_of_month = dt.day
    if day_of_month <= 5:
        return 1  # 上元
    elif day_of_month <= 10:
        return 2  # 中元
    else:
        return 3  # 下元

def is_yang_dun(dt: datetime) -> bool:
    """判断是否阳遁"""
    month = dt.month
    # 冬至（约12月22日）到夏至（约6月21日）阳遁
    if month >= 12 or month < 6:
        return True
    elif month == 6 and dt.day < 21:
        return True
    elif month == 6 and dt.day >= 21:
        return False
    else:
        return False

def get_ju_num(jieqi: str, yuan: int, is_yang: bool) -> int:
    """根据节气获取局数"""
    if is_yang:
        ju_map = {
            '冬至': [1, 7, 4], '惊蛰': [1, 7, 4],
            '小寒': [2, 8, 5],
            '大寒': [3, 9, 6], '春分': [3, 9, 6],
            '清明': [4, 1, 7], '立夏': [4, 1, 7],
            '谷雨': [5, 2, 8], '小满': [5, 2, 8],
            '芒种': [6, 3, 9],
        }
    else:
        ju_map = {
            '夏至': [9, 3, 6], '白露': [9, 3, 6],
            '小暑': [8, 2, 5],
            '大暑': [7, 1, 4], '秋分': [7, 1, 4],
            '立秋': [2, 5, 8],
            '处暑': [1, 4, 7],
            '寒露': [6, 9, 3], '立冬': [6, 9, 3],
            '霜降': [5, 8, 2], '小雪': [5, 8, 2],
            '大雪': [4, 7, 1],
        }
    
    jieqi_ju = ju_map.get(jieqi, [5, 5, 5])  # 默认5局
    return jieqi_ju[yuan - 1]

def get_zhi_ganzhi(year: int, month: int, day: int, hour: int) -> Tuple[str, str, str, str]:
    """获取年月日时干支"""
    year_gz = lunar_year_to_ganzhi(year)
    month_gz = get_month_ganzhi(year, month)
    day_dt = datetime(year, month, day)
    day_gz = get_day_ganzhi(day_dt)
    hour_gz = get_hour_ganzhi(day_gz, hour)
    return year_gz, month_gz, day_gz, hour_gz

# ============================================================
# 核心排盘类
# ============================================================

class QimenPaiPan:
    """奇门遁甲排盘器"""
    
    def __init__(self, year: int, month: int, day: int, hour: int):
        self.dt = datetime(year, month, day)
        self.hour = hour
        
        # 获取干支
        self.year_gz, self.month_gz, self.day_gz, self.hour_gz = get_zhi_ganzhi(year, month, day, hour)
        
        # 节气
        self.jieqi = get_jieqi(self.dt)
        
        # 阴阳遁
        self.is_yang = is_yang_dun(self.dt)
        self.dun_type = '阳遁' if self.is_yang else '阴遁'
        
        # 元
        self.yuan = get_yuan_for_jieqi(self.jieqi, self.dt)
        
        # 局数
        self.ju_num = get_ju_num(self.jieqi, self.yuan, self.is_yang)
        
        # 旬首
        self.xunsho = get_xunsho(self.hour_gz)
        
        # 时干
        self.hour_stem = self.hour_gz[0]
        self.hour_branch = self.hour_gz[1]
        
        # 初始化排盘数据
        self.dipan = ['占'] * 9  # 地盘
        self.tianpan = ['占'] * 9  # 天盘
        self.renpan = ['占'] * 9  # 人盘
        self.shenpan = ['占'] * 9  # 神盘
        
        self.zhifu_xing = ''  # 值符星
        self.zhishi_men = ''  # 值使门
        
        self._do_paipan()
    
    def _do_paipan(self):
        """执行排盘"""
        # 1. 排地盘
        self._paipan_dipan()
        
        # 2. 定值符值使
        self._ding_zhifu_zhishi()
        
        # 3. 排天盘
        self._paipan_tianpan()
        
        # 4. 排人盘
        self._paipan_renpan()
        
        # 5. 排八神
        self._paipan_shenpan()
    
    def _paipan_dipan(self):
        """排地盘三奇六仪"""
        # 几局戊落几宫
        start_idx = PALACE_NUM_TO_IDX.get(self.ju_num, 0)
        
        for i in range(9):
            if self.is_yang:
                # 阳遁顺飞
                idx = (start_idx + i) % 9
            else:
                # 阴遁逆飞
                idx = (start_idx - i) % 9
            
            self.dipan[idx] = SANQI_LIUYI[i]
    
    def _ding_zhifu_zhishi(self):
        """定值符和值使"""
        # 找旬首在地盘的宫位
        xunshou_gan = XUNSHOU_TIANGAN.get(self.xunsho, '戊')
        
        # 旬首地盘落宫
        xunshou_idx = self.dipan.index(xunshou_gan) if xunshou_gan in self.dipan else 0
        
        # 计算值符值使序号
        xun_num = XUNSHOU.get(self.xunsho, 1)
        
        if self.is_yang:
            zf_num = (self.ju_num + xun_num - 1 - 1) % 9 + 1
        else:
            zf_num = (1 + self.ju_num - xun_num - 1) % 9 + 1
            if zf_num <= 0:
                zf_num += 9
        
        zf_num = max(1, min(9, zf_num))
        
        # 九星序号 1-9 -> 索引 0-8
        zf_idx = zf_num - 1
        self.zhifu_xing = JIUXING[zf_idx]
        
        # 八门序号 1-9 -> 索引 0-8
        zm_idx = (zf_num - 1) % 9
        self.zhishi_men = BAMEN[zm_idx]
    
    def _paipan_tianpan(self):
        """排天盘九星"""
        # 找时干在地盘的宫位
        hour_stem = self.hour_stem
        if hour_stem in self.dipan:
            start_idx = self.dipan.index(hour_stem)
        else:
            # 特殊情况：时干是三奇之一
            if hour_stem == '乙':
                start_idx = self.dipan.index('乙')
            elif hour_stem == '丙':
                start_idx = self.dipan.index('丙')
            elif hour_stem == '丁':
                start_idx = self.dipan.index('丁')
            else:
                start_idx = 0
        
        # 值符星落宫
        zf_idx_in_palace = PALACE_NUM_TO_IDX.get(
            PALACE_IDX_TO_NUM.get(start_idx, 1), 7
        )
        
        # 在当前盘中找值符星对应的位置
        # 值符星 = JIUXING中的某个
        zf_xing = self.zhifu_xing
        zf_xing_idx = JIUXING.index(zf_xing) if zf_xing in JIUXING else 0
        
        # 找到值符星应该落在哪个宫
        # 简化：用值符落宫数来算
        zf_palace_num = PALACE_IDX_TO_NUM.get(start_idx, 1)
        
        # 排布九星
        for i in range(9):
            if self.is_yang:
                # 阳遁顺飞
                idx = (start_idx + i) % 9
            else:
                # 阴遁逆飞
                idx = (start_idx - i) % 9
            
            # 九星顺序
            xing_idx = (zf_xing_idx + i) % 9
            self.tianpan[idx] = JIUXING[xing_idx]
    
    def _paipan_renpan(self):
        """排人盘八门"""
        # 找旬首地盘宫
        xunshou_gan = XUNSHOU_TIANGAN.get(self.xunsho, '戊')
        start_idx = self.dipan.index(xunshou_gan) if xunshou_gan in self.dipan else 0
        
        # 时支对应宫位
        zhi_palace_num = DIZHI_PALACE.get(self.hour_branch, 1)
        zhi_idx = PALACE_NUM_TO_IDX.get(zhi_palace_num, 7)
        
        # 值使门序号
        zhishi_idx = BAMEN.index(self.zhishi_men) if self.zhishi_men in BAMEN else 0
        
        # 从旬首宫数到时支宫
        # 阳遁顺数，阴遁逆数
        # 八门排布（跳过中宫5）
        bamen_order = [0, 1, 2, 3, 5, 6, 7, 8]  # 0-8索引对应1-9宫（跳过5）
        
        if self.is_yang:
            # 阳遁：从旬首宫顺时针数到时支宫
            step = (zhi_idx - start_idx) % 8
        else:
            # 阴遁：从旬首宫逆时针数到时支宫
            step = (start_idx - zhi_idx) % 8
        
        # 值使门落宫
        zhishi_bamen_idx = bamen_order[(bamen_order.index(start_idx) + step) % 8]
        
        # 排布八门
        for i in range(8):
            idx_in_order = (bamen_order.index(zhishi_bamen_idx) + i) % 8
            palace_idx = bamen_order[idx_in_order]
            
            men_idx = (zhishi_idx + i) % 9
            if men_idx == 4:  # 跳过中门
                men_idx = (men_idx + 1) % 9
            
            self.renpan[palace_idx] = BAMEN[men_idx]
    
    def _paipan_shenpan(self):
        """排八神"""
        # 找值符落宫
        zf_xing = self.zhifu_xing
        zf_idx = self.tianpan.index(zf_xing) if zf_xing in self.tianpan else 0
        
        # 八神顺序
        shen_order = BASHEN_YANG if self.is_yang else BASHEN_YIN
        
        for i in range(8):
            if self.is_yang:
                idx = (zf_idx + i) % 9
            else:
                idx = (zf_idx - i) % 9
            
            if idx < 8:  # 跳过中宫
                self.shenpan[idx] = shen_order[i]
    
    def get_palace_info(self, idx: int) -> Dict:
        """获取某宫的信息"""
        palace_num = PALACE_IDX_TO_NUM.get(idx, 1)
        return {
            'idx': idx,
            'num': palace_num,
            'name': PALACE_ORDER[idx][1],
            'direction': PALACE_ORDER[idx][2],
            'dipan': self.dipan[idx],
            'tianpan': self.tianpan[idx],
            'renpan': self.renpan[idx],
            'shenpan': self.shenpan[idx],
            'wuxing': WUXING_PALACE.get(palace_num, '土'),
        }
    
    def get_tianpan_gan(self, idx: int) -> str:
        """获取天盘天干"""
        # 天盘天干 = 地盘天干（需要反转）
        # 简化：直接返回
        return self.dipan[idx]
    
    def format_output(self) -> str:
        """格式化输出"""
        lines = []
        
        # 基本信息
        lines.append("=" * 50)
        lines.append("奇门遁甲排盘")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"求测时间：{self.dt.strftime('%Y年%m月%d日 %H时')}")
        lines.append(f"干支历：{self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")
        lines.append(f"节    气：{self.jieqi}")
        lines.append(f"遁    局：{self.dun_type} 第{self.ju_num}局")
        lines.append(f"值    符：{self.zhifu_xing}  值使：{self.zhishi_men}")
        lines.append("")
        
        # 九宫排盘
        lines.append("-" * 50)
        lines.append("九宫排盘（天盘/人盘/神盘）")
        lines.append("-" * 50)
        lines.append("")
        
        # 上排
        line = "┌─────────┬─────────┬─────────┐\n"
        lines.append(line)
        
        for row in range(3):
            if row == 1:
                # 中排有寄宫
                for i in range(3):
                    idx = row * 3 + i
                    info = self.get_palace_info(idx)
                    if idx == 3:  # 震三宫
                        line = f"│ 震三宫  │ 中五宫  │ 兑七宫  │\n"
                    elif idx == 4:  # 中五宫
                        line = f"│  {info['shenpan']:<4}  │  {info['tianpan']:<4}  │  {info['renpan']:<4}  │\n"
                    elif idx == 5:  # 兑七宫
                        line = f"│  {info['shenpan']:<4}  │ 寄坤宫  │  {info['tianpan']:<4}  │\n"
                line = "│ 震三宫  │ 中五宫  │ 兑七宫  │\n"
                lines.append(line)
                line = "│ 六合   │ 白虎   │ 玄武   │\n"
                lines.append(line)
                line = "│ 天冲星  │ 天禽星  │ 天柱星  │\n"
                lines.append(line)
                line = "│ 伤门   │        │ 惊门   │\n"
                lines.append(line)
                line = "│ [天干] │ [天干] │ [天干] │\n"
                lines.append(line)
                line = "├─────────┼─────────┼─────────┤\n"
                lines.append(line)
            else:
                # 获取每行的三个宫信息
                idx0 = row * 3
                idx1 = row * 3 + 1
                idx2 = row * 3 + 2
                info0 = self.get_palace_info(idx0)
                info1 = self.get_palace_info(idx1)
                info2 = self.get_palace_info(idx2)
                
                palace0 = f"{info0['name']}{info0['num']}宫"
                palace1 = f"{info1['name']}{info1['num']}宫"
                palace2 = f"{info2['name']}{info2['num']}宫"
                
                line = f"│ {palace0:<7} │ {palace1:<7} │ {palace2:<7} │\n"
                lines.append(line)
                
                line = f"│ {info0['shenpan']:<7} │ {info1['shenpan']:<7} │ {info2['shenpan']:<7} │\n"
                lines.append(line)
                
                line = f"│ {info0['tianpan']:<7} │ {info1['tianpan']:<7} │ {info2['tianpan']:<7} │\n"
                lines.append(line)
                
                line = f"│ {info0['renpan']:<7} │ {info1['renpan']:<7} │ {info2['renpan']:<7} │\n"
                lines.append(line)
                
                line = f"│ {info0['dipan']:<7} │ {info1['dipan']:<7} │ {info2['dipan']:<7} │\n"
                lines.append(line)
                
                line = "├─────────┼─────────┼─────────┤\n"
                lines.append(line)
        
        # 地盘
        lines.append("")
        lines.append("-" * 50)
        lines.append("地盘（固定不动）")
        lines.append("-" * 50)
        lines.append("")
        
        for row in range(3):
            line = ""
            for col in range(3):
                idx = row * 3 + col
                palace = f"{PALACE_ORDER[idx][1]}{PALACE_ORDER[idx][0]}宫"
                line += f"│ {palace:<7} "
            line += "│\n"
            lines.append(line)
            
            line = ""
            for col in range(3):
                idx = row * 3 + col
                line += f"│   {self.dipan[idx]:<4}  "
            line += "│\n"
            lines.append(line)
            
            if row < 2:
                line = "├─────────┼─────────┼─────────┤\n"
            else:
                line = "└─────────┴─────────┴─────────┘\n"
            lines.append(line)
        
        return "".join(lines)
    
    def analyze(self, question: str) -> Dict:
        """分析格局"""
        # 判断求测类型
        q = question.lower()
        
        if any(k in q for k in ['财', '钱', '生意', '盈利', '投资']):
            yongshen_type = '求财'
        elif any(k in q for k in ['工作', '求职', '上班', '职位', '事业']):
            yongshen_type = '求职'
        elif any(k in q for k in ['感情', '恋爱', '桃花', '姻缘', '婚姻', '男', '女']):
            yongshen_type = '感情'
        elif any(k in q for k in ['出行', '出门', '旅游', '旅行', '交通']):
            yongshen_type = '出行'
        elif any(k in q for k in ['官司', '诉讼', '打官司', '纠纷']):
            yongshen_type = '官司'
        elif any(k in q for k in ['健康', '病', '身体', '医疗', '健康']):
            yongshen_type = '疾病'
        elif any(k in q for k in ['考试', '学习', '学业', '升学']):
            yongshen_type = '学业'
        elif any(k in q for k in ['文书', '合同', '签约']):
            yongshen_type = '文书'
        else:
            yongshen_type = '事业'
        
        yongshen_info = YONGSHEN.get(yongshen_type, YONGSHEN['事业'])
        
        # 找用神落宫
        main_yongshen = yongshen_info['main'][0]
        
        # 分析
        result = {
            'type': yongshen_type,
            'yongshen': yongshen_info,
            'shengmen_palace': self.dipan.index('生门') if '生门' in self.dipan else -1,
            'zhifu_palace': self.tianpan.index(self.zhifu_xing) if self.zhifu_xing in self.tianpan else -1,
            'kaimen_palace': self.dipan.index('开门') if '开门' in self.dipan else -1,
        }
        
        return result

# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='奇门遁甲排盘工具')
    parser.add_argument('--question', '-q', type=str, help='求测问题')
    parser.add_argument('--time', '-t', type=str, help='时间，格式：YYYY-MM-DD HH:MM')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    
    # 解析时间
    if args.time:
        try:
            dt = datetime.strptime(args.time, '%Y-%m-%d %H:%M')
            year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
        except:
            print("时间格式错误，请使用 YYYY-MM-DD HH:MM 格式")
            sys.exit(1)
    else:
        dt = datetime.now()
        year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
    
    # 排盘
    qp = QimenPaiPan(year, month, day, hour)
    
    # 输出
    output = qp.format_output()
    
    if args.question:
        analysis = qp.analyze(args.question)
        output += "\n\n"
        output += "=" * 50 + "\n"
        output += f"问题：{args.question}\n"
        output += f"类型：{analysis['type']}\n"
        output += f"用神：{', '.join(analysis['yongshen']['main'])}\n"
    
    print(output)
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n已保存到：{args.output}")

if __name__ == '__main__':
    main()
