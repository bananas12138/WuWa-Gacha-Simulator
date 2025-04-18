#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gacha Simulator
----------------
新增功能：
1. 多轮模拟模式：输入轮数，每轮独立计算平均抽数
2. 统计去除极值后的区间
3. 生成散点图
"""
import random
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体（SimHei）
matplotlib.rcParams['axes.unicode_minus'] = False    # 正确显示负号


def build_probability_schedule():
    """构建出五星概率表（长度为80），按抽数递增概率。"""
    p = [0.0] * 80
    for i in range(1, 81):
        if i <= 65:
            p[i-1] = 0.008
        elif 66 <= i <= 70:
            p[i-1] = p[i-2] + 0.04
        elif 71 <= i <= 75:
            p[i-1] = p[i-2] + 0.08
        elif 76 <= i <= 79:
            p[i-1] = p[i-2] + 0.10
        else:
            p[i-1] = 1.0  # 第80抽必出五星
        if p[i-1] > 1.0:
            p[i-1] = 1.0
    return p

def simulate_one_run(p_schedule, up_guarantee_counter):
    """单次模拟，使用概率表决定何时出五星，考虑歪机制。"""
    for draw_count, p in enumerate(p_schedule, start=1):
        if random.random() < p or draw_count == 80:
            if up_guarantee_counter > 0:
                return draw_count, True, up_guarantee_counter - 1
            is_up = (random.random() < 0.5)
            if not is_up:
                return draw_count, False, 2
            return draw_count, True, 0
    return 80, True, max(0, up_guarantee_counter - 1)

def simulate_with_numpy(n, p_schedule, up_guarantee_counter_start=0):
    """大规模模拟，使用NumPy向量化随机数，提升效率。"""
    results = []
    up_guarantee_counter = up_guarantee_counter_start
    for _ in range(n):
        rand = np.random.random(80)
        for draw_count, p in enumerate(p_schedule, start=1):
            if rand[draw_count-1] < p or draw_count == 80:
                if up_guarantee_counter > 0:
                    results.append((draw_count, True))
                    up_guarantee_counter -= 1
                else:
                    is_up = np.random.random() < 0.5
                    if not is_up:
                        results.append((draw_count, False))
                        up_guarantee_counter = 2
                    else:
                        results.append((draw_count, True))
                break
    return results


# ---------------------------- 新增多轮模拟相关函数 ----------------------------
def simulate_single_round(total_simulations):
    """单轮模拟：连续获得total_simulations次五星，返回平均抽数"""
    p_schedule = build_probability_schedule()
    up_guarantee_counter = 0  # 每轮初始保底计数器归零
    total_draws = 0

    for _ in range(total_simulations):
        # 模拟单次出金过程并更新保底状态
        draws, _, up_guarantee_counter = simulate_one_run(p_schedule, up_guarantee_counter)
        total_draws += draws

    return total_draws / total_simulations  # 本轮平均抽数


def multi_round_simulation():
    """处理多轮模拟的输入输出和统计"""
    try:
        rounds = int(input("请输入模拟轮数（整数）："))
        per_round = int(input("请输入每轮要获得的五星次数（整数）："))
    except ValueError:
        print("输入必须为整数！")
        sys.exit(1)

    averages = []
    print("\n开始模拟...")
    for i in range(rounds):
        avg = simulate_single_round(per_round)
        averages.append(avg)
        print(f"第 {i + 1}/{rounds} 轮完成，平均抽数：{avg:.2f}")

    # 去除极值处理
    if len(averages) >= 2:
        sorted_avg = sorted(averages)
        trimmed = sorted_avg[1:-1]  # 去掉一个最小和一个最大
    else:
        trimmed = averages

    # 结果输出
    print("\n=== 统计结果 ===")
    if trimmed:
        print(f"有效数据区间：[{min(trimmed):.2f} ~ {max(trimmed):.2f}]")
    else:
        print("数据不足无法去除极值")
    print(f"原始极值区间：[{min(averages):.2f} ~ {max(averages):.2f}]")

    # 绘制散点图
    plt.figure(figsize=(12, 6))
    plt.scatter(range(1, rounds + 1), averages, alpha=0.6,
                c='royalblue', edgecolors='black')
    plt.title(f'各轮平均抽数分布（共{rounds}轮，每轮{per_round}次五星）')
    plt.xlabel('轮次编号')
    plt.ylabel('平均抽数')
    plt.grid(linestyle='--', alpha=0.6)
    plt.savefig('轮次散点图.png', dpi=300)
    print("\n散点图已保存为 轮次散点图.png")

def original_main():
    # -------- 用户输入：总模拟次数和历史出金记录 --------
    try:
        total_simulations = int(input("请输入总模拟次数（整数）："))
        real_count = int(input("请输入你在游戏中已抽取的五星次数（如 3）："))
        if total_simulations <= real_count:
            print("总模拟次数必须大于你已抽取的次数。")
            sys.exit(1)
    except ValueError:
        print("无效输入，请输入整数。")
        sys.exit(1)

    real_history = []
    up_guarantee_counter = 0
    print("请依次输入每次五星的抽数和是否歪（如：58 不歪 或 44 歪）：")
    for i in range(real_count):
        while True:
            entry = input(f"第 {i+1} 次出五星：").strip()
            try:
                draw, result = entry.split()
                draw = int(draw)
                is_up = (result == "不歪")
                real_history.append((draw, is_up))
                if not is_up:
                    up_guarantee_counter = 2
                elif up_guarantee_counter > 0:
                    up_guarantee_counter -= 1
                break
            except:
                print("格式错误，请输入格式如：58 不歪 或 44 歪")

    # -------- 模拟抽卡 --------
    n = total_simulations - real_count
    p_schedule = build_probability_schedule()
    results = real_history.copy()
    enable_console_output = total_simulations <= 10000

    if n > 10000:
        simulated = simulate_with_numpy(n, p_schedule, up_guarantee_counter)
    else:
        simulated = []
        for i in range(1, n + 1):
            draws, is_up, up_guarantee_counter = simulate_one_run(p_schedule, up_guarantee_counter)
            simulated.append((draws, is_up))
            if enable_console_output:
                status = "UP" if is_up else "非UP"
                print(f"模拟第 {real_count + i} 次: 抽数 = {draws}, 结果 = {status}")

    results.extend(simulated)

    # -------- 统计分析 --------
    total_draws = sum(d for d, _ in results)
    up_draws = [d for d, u in results if u]
    non_up_draws = [d for d, u in results if not u]
    total_up = len(up_draws)
    total_non_up = len(non_up_draws)
    max_draws_up = max(up_draws) if up_draws else 0
    max_draws_non_up = max(non_up_draws) if non_up_draws else 0
    prob_up = total_up / total_simulations
    prob_non_up = total_non_up / total_simulations
    average_draws_per_five_star = total_draws / total_simulations
    average_draws_per_five_up = sum(up_draws) / total_up if total_up > 0 else 0
    average_total_draws_per_up = total_draws / total_up if total_up > 0 else 0

    over_70 = [(d, u) for d, u in results if d >= 70]
    under_10 = [(d, u) for d, u in results if d <= 10]

    # -------- 写入结果文件 --------
    with open("results.txt", "w", encoding="utf-8") as f:
        if enable_console_output:
            f.write("模拟序号, 抽数, 是否UP\n")
            for idx, (draws, is_up) in enumerate(results, start=1):
                status = "UP" if is_up else "非UP"
                f.write(f"{idx}, {draws}, {status}\n")
            f.write("\n")
        f.write("统计结果:\n")
        f.write(f"总 UP 次数: {total_up}, 最大花费抽数: {max_draws_up}\n")
        f.write(f"总 非UP 次数: {total_non_up}, 最大花费抽数: {max_draws_non_up}\n")
        f.write(f"UP 概率: {prob_up:.5f}\n")
        f.write(f"非UP 概率: {prob_non_up:.5f}\n")
        f.write(f"平均每次出五星所需抽数: {average_draws_per_five_star:.5f}\n")
        f.write(f"\n高于70抽出五星次数: {len(over_70)}，其中为UP的次数: {len([1 for d, u in over_70 if u])}\n")
        f.write(f"低于等于10抽出五星次数: {len(under_10)}，其中为UP的次数: {len([1 for d, u in under_10 if u])}\n")

    # -------- 输出统计到终端 --------
    print(f"\n已将所有结果保存至当前目录下的 results.txt")
    print("\n统计结果：")
    print(f"总 UP 次数: {total_up}, 最大花费抽数: {max_draws_up}")
    print(f"总 非UP 次数: {total_non_up}, 最大花费抽数: {max_draws_non_up}")
    print(f"UP 概率: {prob_up:.5f}")
    print(f"非UP 概率: {prob_non_up:.5f}")
    print(f"平均每次出五星所需抽数: {average_draws_per_five_star:.5f}")
    print(f"高于70抽出五星次数: {len(over_70)}，其中为UP的次数: {len([1 for d, u in over_70 if u])}")
    print(f"低于等于10抽出五星次数: {len(under_10)}，其中为UP的次数: {len([1 for d, u in under_10 if u])}")

    # -------- 绘制中间 80% 抽数分布直方图 --------
    mid_start = int(total_simulations * 0.1)
    mid_end = int(total_simulations * 0.9)
    middle_range_draws = [results[i][0] for i in range(mid_start, mid_end)]

    plt.figure(figsize=(10, 6))
    plt.hist(middle_range_draws, bins=range(1, 82), color='skyblue', edgecolor='black')
    plt.title(f'中间 80% 模拟（第 {mid_start+1}~{mid_end} 次）出金抽数分布')
    plt.xlabel('抽数')
    plt.ylabel('出现次数')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    image_path = "抽数直方图.png"
    plt.savefig(image_path, dpi=300)
    plt.show()
    print(f" 直方图已保存为：{image_path}")

def main():
    """模式选择入口"""
    print("请选择运行模式：")
    print("1. 单次模拟（含历史记录功能）")
    print("2. 多轮模拟（新增统计功能）")
    choice = input("请输入数字选择：").strip()

    if choice == '1':
        original_main()
    elif choice == '2':
        multi_round_simulation()
    else:
        print("无效输入！")

if __name__ == "__main__":
    main()
