
import streamlit as st
import random
import requests
from collections import Counter, defaultdict

st.set_page_config(page_title="개파의 매직로또 AI", layout="centered")

st.markdown(
    """
    <style>
    .main {
        background-color: #f5f7fa;
        font-family: 'Segoe UI', sans-serif;
    }
    h1 {
        color: #2c3e50;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎯 개파의 매직로또 AI")

def get_ball_color(n):
    if 1 <= n <= 10: return "#fbc400"
    elif 11 <= n <= 20: return "#69c8f2"
    elif 21 <= n <= 30: return "#ff7272"
    elif 31 <= n <= 40: return "#aaa"
    else: return "#b0d840"

def render_numbers(numbers):
    return " ".join([
        f"<span style='display:inline-block;width:32px;height:32px;border-radius:50%;background-color:{get_ball_color(n)};color:#000;text-align:center;line-height:32px;font-weight:bold;margin-right:5px;'>{n}</span>"
        for n in numbers
    ])

def get_draw_result(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
    except:
        return None

def get_latest_draw_no():
    no = 1100
    while True:
        data = get_draw_result(no)
        if data and data.get("returnValue") == "success":
            no += 1
        else:
            break
    return no - 1

@st.cache_data
def get_all_history():
    latest = get_latest_draw_no()
    records = []
    for i in range(1, latest + 1):
        data = get_draw_result(i)
        if data and data.get("returnValue") == "success":
            win_nums = [data[f"drwtNo{j}"] for j in range(1, 7)]
            bonus = data["bnusNo"]
            records.append({"round": i, "numbers": win_nums, "bonus": bonus})
    return records

def get_method_explanation(method):
    return {
        "AI추천번호": "최근 100회에서 가장 자주 등장한 숫자 30개 중 무작위로 선택된 조합입니다.",
        "많이 나오는 연속번호": "최근 회차에서 연속 등장한 번호를 우선으로 뽑은 조합입니다.",
        "AI추천번호+무작위": "AI추천번호 상위 30 중 3개 + 나머지 무작위 3개로 혼합된 조합입니다.",
        "수동선택": "사용자가 직접 입력한 조합입니다."
    }.get(method, "")

def get_past_rank_count(recommended, history):
    result_count = defaultdict(int)
    rset = set(recommended)
    for draw in history:
        win = set(draw["numbers"])
        inter = rset & win
        match = len(inter)
        bonus = draw["bonus"]
        if match == 6:
            result_count["1등"] += 1
        elif match == 5 and bonus in rset:
            result_count["2등"] += 1
        elif match == 5:
            result_count["3등"] += 1
        elif match == 4:
            result_count["4등"] += 1
        elif match == 3:
            result_count["5등"] += 1
    return result_count

def generate_numbers(method, history, exclude_set, user_input=None):
    while True:
        if method == "무작위":
            nums = sorted(random.sample(range(1, 46), 6))
        elif method == "AI추천번호":
            flat = [n for row in history for n in row["numbers"]]
            freq = Counter(flat)
            top = [n for n, _ in freq.most_common(30)]
            nums = sorted(random.sample(top, 6))
        elif method == "많이 나오는 연속번호":
            candidates = []
            for row in history:
                nums = sorted(row["numbers"])
                for i in range(5):
                    if nums[i] + 1 == nums[i + 1]:
                        candidates.extend([nums[i], nums[i + 1]])
            base = list(set(candidates))
            nums = sorted(random.sample(base, 6)) if len(base) >= 6 else sorted(random.sample(range(1, 46), 6))
        elif method == "AI추천번호+무작위":
            flat = [n for row in history for n in row["numbers"]]
            freq = Counter(flat)
            top = [n for n, _ in freq.most_common(30)]
            nums = sorted(random.sample(top, 3) + random.sample(range(1, 46), 3))
        elif method == "수동선택":
            nums = sorted(user_input)
        else:
            return []
        if tuple(nums) not in exclude_set:
            return nums

methods = ["AI추천번호", "많이 나오는 연속번호", "AI추천번호+무작위", "수동선택"]
method = st.selectbox("🎯 추천 방식 선택", methods)

user_numbers = []
if method == "수동선택":
    input_text = st.text_input("숫자 6개를 쉼표로 입력 (예: 3,11,25,33,40,44)")
    try:
        user_numbers = [int(x.strip()) for x in input_text.split(",")]
        if len(user_numbers) != 6 or not all(1 <= n <= 45 for n in user_numbers):
            st.warning("정확히 6개의 숫자를 입력해주세요.")
            user_numbers = []
    except:
        st.warning("입력이 잘못되었습니다.")
        user_numbers = []

if st.button("🎁 추천 번호 받기"):
    with st.spinner("번호 분석 중..."):
        full_history = get_all_history()
        exclude = set(tuple(sorted(row["numbers"])) for row in full_history)
        result = generate_numbers(method, full_history, exclude, user_numbers)
        st.markdown("## 🎉 추천 번호")
        st.markdown(render_numbers(result), unsafe_allow_html=True)
        st.markdown(f"🧠 추천 방식 설명: *{get_method_explanation(method)}*")
        past_rank = get_past_rank_count(result, full_history)
        if past_rank:
            st.markdown("📊 과거 당첨 이력:")
            for rank, count in past_rank.items():
                st.markdown(f"- {rank}: {count}회")

st.markdown("# AI가 말해주는 이번 주 가장 주목할 번호")
# 📩 이번 주 AI가 말하는 주목할 번호
st.markdown("## 📩 이번 주 주목할 번호 (AI 분석 뉴스레터)")
try:
    history = get_all_history()
    flat = [n for row in history[-100:] for n in row["numbers"]]
    freq = Counter(flat)
    top_numbers = [num for num, _ in freq.most_common(6)]
    st.markdown("**🎯 가장 자주 나온 상위 6개 번호:**")
    st.markdown(render_numbers(sorted(top_numbers)), unsafe_allow_html=True)
    st.info("이 번호들은 최근 100회 중 출현 빈도가 가장 높은 번호입니다. 전략적 선택에 참고해보세요!")
except:
    st.warning("뉴스레터 정보를 불러오는 데 문제가 발생했습니다.")


# 📅 최근 1등 당첨번호")
if st.button("🔄 새로고침"):
    full_history = get_all_history()
    for row in full_history[-5:][::-1]:
        st.markdown(f"**{row['round']}회차**: " + render_numbers(row["numbers"]), unsafe_allow_html=True)
