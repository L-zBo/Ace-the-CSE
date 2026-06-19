#!/usr/bin/env python3
"""全面审计项目 - 国考/省考/事业编"""
import json
import glob

def audit_source(source_name, pattern):
    """审计指定来源的数据"""
    print(f"\n{'='*70}")
    print(f"{source_name} 数据审计")
    print('='*70)

    files = sorted(glob.glob(pattern))

    # 按年份级别分组
    by_year_level = {}
    total_questions = 0
    total_incomplete_options = 0

    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)

            if not data:
                continue

            # 提取年份和级别
            sample = data[0]
            year = sample.get('year', 'unknown')
            level = sample.get('level', 'unknown')
            key = f"{year}_{level}"

            if key not in by_year_level:
                by_year_level[key] = {
                    'total': 0,
                    'opt_0': 0,
                    'opt_1': 0,
                    'opt_2': 0,
                    'opt_3': 0,
                    'opt_4': 0,
                }

            for q in data:
                by_year_level[key]['total'] += 1
                total_questions += 1

                opts = len(q.get('options', []))
                if opts == 0:
                    by_year_level[key]['opt_0'] += 1
                    total_incomplete_options += 1
                elif opts == 1:
                    by_year_level[key]['opt_1'] += 1
                    total_incomplete_options += 1
                elif opts == 2:
                    by_year_level[key]['opt_2'] += 1
                    total_incomplete_options += 1
                elif opts == 3:
                    by_year_level[key]['opt_3'] += 1
                    total_incomplete_options += 1
                elif opts == 4:
                    by_year_level[key]['opt_4'] += 1

    # 输出结果
    print(f"\n年份_级别 | 总题数 | 4选项 | <4选项 | 完整率")
    print("-" * 70)

    for key in sorted(by_year_level.keys(), reverse=True):
        s = by_year_level[key]
        complete = s['opt_4']
        incomplete = s['opt_0'] + s['opt_1'] + s['opt_2'] + s['opt_3']
        rate = complete / s['total'] * 100 if s['total'] > 0 else 0

        status = "[OK]" if rate >= 95 else "[WARN]"
        print(f"{key:20} | {s['total']:6} | {complete:6} | {incomplete:7} | {rate:5.1f}% {status}")

        # 显示详细问题
        if incomplete > 0:
            details = []
            if s['opt_0'] > 0:
                details.append(f"0选项:{s['opt_0']}")
            if s['opt_1'] > 0:
                details.append(f"1选项:{s['opt_1']}")
            if s['opt_2'] > 0:
                details.append(f"2选项:{s['opt_2']}")
            if s['opt_3'] > 0:
                details.append(f"3选项:{s['opt_3']}")
            if details:
                print(f"{'':20}   {', '.join(details)}")

    print("-" * 70)
    print(f"总计: {total_questions} 题，选项不全 {total_incomplete_options} 题 ({total_incomplete_options/total_questions*100:.1f}%)")

    return total_questions, total_incomplete_options

# 审计国考
national_total, national_incomplete = audit_source(
    "国考",
    "src/data/xingce/*/national_*.json"
)

# 审计省考
provincial_total, provincial_incomplete = audit_source(
    "省考",
    "src/data/xingce/*/provincial_*.json"
)

# 审计事业编
institution_total, institution_incomplete = audit_source(
    "事业编",
    "src/data/xingce/*/institution_*.json"
)

# 总结
print(f"\n{'='*70}")
print("全库总结")
print('='*70)
print(f"国考: {national_total} 题，选项不全 {national_incomplete} 题")
print(f"省考: {provincial_total} 题，选项不全 {provincial_incomplete} 题")
print(f"事业编: {institution_total} 题，选项不全 {institution_incomplete} 题")
print(f"总计: {national_total + provincial_total + institution_total} 题")
print(f"选项不全: {national_incomplete + provincial_incomplete + institution_incomplete} 题")
