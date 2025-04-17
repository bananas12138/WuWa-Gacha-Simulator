#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gacha Simulator
----------------
基于指定的分段保底概率规则，模拟抽取五星角色的过程，优化为支持大规模模拟时使用 NumPy 向量化生成随机数以提升性能。

功能：
1. 构建每一发抽卡获得五星的概率表（长度80）。
2. 重复模拟若干次抽卡，记录每次抽到五星所需抽数及是否为当期UP。
3. 将结果打印到终端，并保存至 results.txt 文件。
4. 统计总UP/非UP次数，并分别输出各自花费最多的抽数。
5. 计算UP与非UP出现的模拟概率，保留小数点后五位。
6. 若模拟次数大于10000，则仅在 results.txt 中输出统计摘要，省略每次模拟过程。
7. 若第 n 次出金歪（非UP），则第 n+1 和第 n+2 次出金必定为UP。
8. 显示抽出五星的平均抽数，以及抽出五次UP的平均数。
9. 使用 NumPy 向量化方式加快大批量模拟。
10. 支持用户输入已实际抽取的历史记录，并从当前状态继续模拟。
11. 统计出金在70抽及以上和10抽及以下的情况（包含UP与非UP），并输出至终端及txt文件。
"""
import random
import sys
import numpy as np

def build_probability_schedule():
    """构建从第1抽到第80抽的出五星概率表，符合分段提升机制。"""
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
            p[i-1] = 1.0
        if p[i-1] > 1.0:
            p[i-1] = 1.0
    return p

def simulate_one_run(p_schedule, up_guarantee_counter):
    """
    单次模拟抽取过程，返回：
    - 抽数 draw_count
    - 是否为UP角色 is_up
    - 更新后的UP保底计数器 up_guarantee_counter
    """
    for draw_count, p in enumerate(p_schedule, start=1):
        if random.random() < p or draw_count == 80:  # 强制第80抽必中
            if up_guarantee_counter > 0:
                return draw_count, True, up_guarantee_counter - 1
            is_up = (random.random() < 0.5)
            if not is_up:
                return draw_count, False, 2  # 歪了则接下来2次必定为UP
            return draw_count, True, 0
    return 80, True, max(0, up_guarantee_counter - 1)  # 理论不会执行到这

def simulate_with_numpy(n, p_schedule, up_guarantee_counter_start=0):
    """
    使用 NumPy 向量化模拟多次抽卡
    返回一个 (抽数, 是否为UP) 的结果列表
    """
    results = []
    up_guarantee_counter = up_guarantee_counter_start
    for _ in range(n):
        rand = np.random.random(80)
        for draw_count, p in enumerate(p_schedule, start=1):
            if rand[draw_count-1] < p or draw_count == 80:  # 第80抽强制命中
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

def main():
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

    # 新增统计：高抽数出金/低抽数出金
    over_70 = [(d, u) for d, u in results if d >= 70]
    over_70_total = len(over_70)
    over_70_up = len([1 for d, u in over_70 if u])

    under_10 = [(d, u) for d, u in results if d <= 10]
    under_10_total = len(under_10)
    under_10_up = len([1 for d, u in under_10 if u])

    output_file = "results.txt"
    with open(output_file, "w", encoding="utf-8") as f:
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
        f.write(f"平均出一个UP五星所需抽数: {average_draws_per_five_up:.5f}\n")
        f.write("\n高于70抽出五星次数: {}，其中为UP的次数: {}\n".format(over_70_total, over_70_up))
        f.write("低于等于10抽出五星次数: {}，其中为UP的次数: {}\n".format(under_10_total, under_10_up))

    print(f"\n已将所有结果保存至当前目录下的 {output_file}")
    print("\n统计结果：")
    print(f"总 UP 次数: {total_up}, 最大花费抽数: {max_draws_up}")
    print(f"总 非UP 次数: {total_non_up}, 最大花费抽数: {max_draws_non_up}")
    print(f"UP 概率: {prob_up:.5f}")
    print(f"非UP 概率: {prob_non_up:.5f}")
    print(f"平均每次出五星所需抽数: {average_draws_per_five_star:.5f}")
    print(f"平均抽到一个UP五星所需总抽数（含歪）: {average_total_draws_per_up:.5f}")
    print(f"高于70抽出五星次数: {over_70_total}，其中为UP的次数: {over_70_up}")
    print(f"低于等于10抽出五星次数: {under_10_total}，其中为UP的次数: {under_10_up}")

if __name__ == "__main__":
    main()