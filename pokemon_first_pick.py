import numpy as np
import pandas as pd
import streamlit as st
# import matplotlib.pyplot as plt
import altair as alt

# 日本語フォント対応
plt.rcParams['font.family'] = 'Meiryo'

# ---- 関数 ----
def simulate_hand(deck, hand_size):
    return np.random.choice(deck, hand_size, replace=False)

def contains_target(hand):
    return np.sum(hand == 'target') > 0

def contains_basic_without_target(hand):
    return np.sum(hand == 'basic') > 0

def contains_basic_pokemon(hand):
    return np.sum((hand == 'basic') | (hand == 'target')) > 0

def run_simulation(deck_size, hand_size, total_basic_pokemon, target_num, num_simulations, mode):
    # デッキ作成
    deck = np.array(
        ['target'] * target_num
        + ['basic'] * (total_basic_pokemon - target_num)
        + ['other'] * (deck_size - total_basic_pokemon)
    )

    success_count = 0
    trials = 0
    probabilities = []

    for _ in range(num_simulations):
        hand = simulate_hand(deck, hand_size)

        # マリガン処理（たねポケモンが出るまで引き直す）
        while not contains_basic_pokemon(hand):
            hand = simulate_hand(deck, hand_size)
            # この引き直しは試行回数に含めない

        # 成功判定
        has_basic = contains_basic_pokemon(hand)
        has_target = contains_target(hand)
        has_basic_without_target = contains_basic_without_target(hand)

        if mode == "ひきたい":
            if has_basic and has_target:
                success_count += 1
        else:  # ひきたくない
            if has_target and not has_basic_without_target:
                success_count += 1

        trials += 1  # マリガン後の有効手札のみカウント
        probabilities.append(success_count / trials)

    return probabilities, trials

# ---- Streamlit UI ----
st.title("ポケモンカード 初手確率シミュレータ")

st.markdown("""
- 本シミュレータは、任意のポケモンが初手7枚に入る確率を計算します
- 設定項目
  - 「デッキ枚数」：基本的には60枚ですが、シールド戦用などに調整も可能です
  - 「初手手札枚数」：7枚（基本固定）
  - 「デッキ内のたねポケモンの枚数」：たねポケモン（スタートできるポケモン）の枚数を記入してください
  - 「ひきたい（ひきたくない）対象ポケモンの枚数：確率を出したい、ひきたいorひきたくないポケモンの枚数を記入してください
  - 「シミュレーション回数」：何回シミュレーションするかを記入できます。基本はそのままでOKです
- モードは2種類あります：
  - **「ひきたい」**：初手に任意のポケモンを前に出せる確率
    - 例：サーナイトデッキにおいて、バトル準備段階にラルトス（4枚）からスタートできる確率
    - バトル準備段階で、ラルトス以外のたねポケモンが入っていてもOK
  - **「ひきたくない」**：初手に任意のポケモンしか前に出せない確率
    - 例：ドラパルトデッキにおいて、初手にガチグマ（1枚）からスタートせざるを得ない確率
""")

# パラメータ入力
deck_size = st.number_input("デッキ枚数", min_value=40, max_value=60, value=60)
hand_size = st.number_input("初手手札枚数", min_value=1, max_value=7, value=7)
total_basic_pokemon = st.number_input("たねポケモンの総数", min_value=1, max_value=20, value=11)
target_num = st.number_input("ひきたい対象ポケモンの枚数", min_value=0, max_value=10, value=4)
num_simulations = st.number_input("シミュレーション回数", min_value=1000, max_value=200000, value=50000, step=1000)

mode = st.radio("モード選択", ["ひきたい", "ひきたくない"])

# 実行ボタン
if st.button("シミュレーション実行"):
    probabilities, trials = run_simulation(deck_size, hand_size, total_basic_pokemon, target_num, num_simulations, mode)
    final_estimated_probability = probabilities[-1]

    # 結果表示
    if mode == "ひきたい":
        label_text = "任意のポケモンを引ける確率"
    else:
        label_text = "任意のポケモンしか出せない確率"

    st.metric(label=label_text, value=f"{final_estimated_probability:.4%}")



    # データフレームに変換
    df = pd.DataFrame({
        "試行回数": range(1, trials + 1),
        "推定確率": probabilities
    })

    # 確率推移ライン
    line_chart = alt.Chart(df).mark_line(color='blue').encode(
        x='試行回数',
        y='推定確率'
    )

    # 最終確率の赤破線
    final_line = alt.Chart(pd.DataFrame({"y": [final_estimated_probability]})).mark_rule(
        color='red', strokeDash=[5,5]
    ).encode(
        y='y'
    )

    # チャートを重ねる
    chart = alt.layer(line_chart, final_line).properties(
        width=800,
        height=400,
        title=f'初手に任意のたねポケモンを引く確率の推移\n_target {target_num}枚 / 全体 {total_basic_pokemon}枚'
    )

    st.altair_chart(chart, use_container_width=True)

