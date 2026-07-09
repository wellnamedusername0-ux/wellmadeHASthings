import importlib
import time

import pandas as pd
import streamlit as st


# ============================================================
# 기존 시간표 알고리즘 파일 불러오기
# GitHub 저장소에 "시간표_알고리즘2.py"가 같이 있어야 함
# ============================================================
solver = importlib.import_module("시간표_알고리즘2")


# ============================================================
# Streamlit 기본 설정
# ============================================================
st.set_page_config(
    page_title="시간표 자동 생성기",
    page_icon="📅",
    layout="wide",
)

st.title("📅 시간표 자동 생성기")
st.caption("과목을 선택하고, 필요하면 블록 고정/공강 지정/추천 기준을 설정해 시간표를 생성합니다.")


# ============================================================
# 데이터 검증
# ============================================================
try:
    solver.validate_course_options(solver.ALL_COURSE_OPTIONS)
except Exception as e:
    st.error(f"데이터 오류가 있습니다: {e}")
    st.stop()


# ============================================================
# 시간표를 DataFrame 표로 바꾸는 함수
# ============================================================
def schedule_to_dataframe(schedule):
    """
    schedule: {"과목명": "블록코드"} 형태의 딕셔너리
    return: 요일 x 교시 형태의 pandas DataFrame
    """
    grid = solver.schedule_to_grid(schedule)

    periods = list(range(1, 8))
    df = pd.DataFrame(index=periods, columns=solver.WEEKDAYS)

    for period in periods:
        for weekday_index, weekday_name in enumerate(solver.WEEKDAYS):
            df.loc[period, weekday_name] = grid.get((weekday_index, period), "공강")

    df.index.name = "교시"
    return df


# ============================================================
# 시간표 구조 선호도 점수 계산
# 점수가 낮을수록 좋은 시간표로 취급
# ============================================================
def score_schedule(schedule, preference):
    grid = solver.schedule_to_grid(schedule)

    score = 0

    if preference == "기본":
        return 0

    elif preference == "월요일 가볍게":
        # 월요일 수업 칸이 적을수록 좋음
        for period in range(1, 8):
            if (0, period) in grid:
                score += 2

    elif preference == "금요일 일찍 끝나기":
        # 금요일 늦은 교시에 수업이 있을수록 큰 벌점
        for period in range(1, 8):
            if (4, period) in grid:
                score += period

    elif preference == "7교시 최소화":
        # 어느 요일이든 7교시 수업이 있으면 벌점
        for weekday in range(5):
            if (weekday, 7) in grid:
                score += 5

    elif preference == "공강 몰기":
        # 한 요일에 공강이 많이 몰려 있을수록 좋음
        daily_free_counts = []

        for weekday in range(5):
            free_count = 0
            for period in range(1, 8):
                if (weekday, period) not in grid:
                    free_count += 1
            daily_free_counts.append(free_count)

        score -= max(daily_free_counts)

    elif preference == "수학·과학 분산":
        # 수학/과학/AP 과목이 하루에 몰릴수록 벌점
        heavy_keywords = [
            "미적분", "확률", "통계", "수학", "선형대수",
            "물리", "화학", "생물", "생명", "지구",
            "역학", "에너지", "AP"
        ]

        daily_heavy_counts = [0, 0, 0, 0, 0]

        for (weekday, period), course in grid.items():
            if any(keyword in course for keyword in heavy_keywords):
                daily_heavy_counts[weekday] += 1

        for count in daily_heavy_counts:
            score += count * count

    return score


# ============================================================
# 시간표 계산 함수
# 같은 조건으로 반복 실행하면 캐시 사용
# required_free_tuple: 반드시 공강으로 둘 교시 목록
# ============================================================
@st.cache_data(show_spinner=False)
def cached_solve(chosen_courses_tuple, fixed_tuple, required_free_tuple, max_solutions):
    chosen_courses = list(chosen_courses_tuple)
    fixed = dict(fixed_tuple)
    required_free = set(required_free_tuple)

    chosen_options = {}

    for course in chosen_courses:
        filtered_blocks = []

        for block in solver.ALL_COURSE_OPTIONS[course]:
            block_time_set = solver.block_times(block)

            # 지정 공강과 겹치는 블록은 후보에서 제외
            if block_time_set & required_free:
                continue

            filtered_blocks.append(block)

        chosen_options[course] = filtered_blocks

    return solver.solve_all(
        chosen_options,
        fixed=fixed,
        max_solutions=max_solutions,
    )


# ============================================================
# 1. 과목 선택
# ============================================================
all_courses = sorted(solver.ALL_COURSE_OPTIONS.keys())

st.subheader("1. 들을 과목 선택")

chosen_courses = st.multiselect(
    "들을 과목을 모두 선택하세요.",
    options=all_courses,
    placeholder="과목을 선택하세요",
)

if not chosen_courses:
    st.info("먼저 들을 과목을 선택하세요.")
    st.stop()


# ============================================================
# 2. 고정 블록 선택
# ============================================================
st.subheader("2. 고정할 과목 선택")

st.write(
    "반드시 특정 블록으로 듣고 싶은 과목만 선택하세요. "
    "고정하지 않을 과목은 '고정 안 함'으로 두면 됩니다."
)

fixed = {}

with st.expander("고정 블록 설정 열기", expanded=False):
    cols = st.columns(2)

    for i, course in enumerate(chosen_courses):
        available_blocks = solver.ALL_COURSE_OPTIONS[course]
        options = ["고정 안 함"] + available_blocks

        selected_block = cols[i % 2].selectbox(
            label=course,
            options=options,
            key=f"fixed_{course}",
        )

        if selected_block != "고정 안 함":
            fixed[course] = selected_block


# ============================================================
# 3. 공강 지정
# ============================================================
st.subheader("3. 공강 지정")

st.write(
    "반드시 비우고 싶은 교시를 선택하세요. "
    "선택한 교시와 겹치는 블록은 자동으로 제외됩니다."
)

time_options = []

for weekday_index, weekday_name in enumerate(solver.WEEKDAYS):
    for period in range(1, 8):
        label = f"{weekday_name}{period}교시"
        time_options.append((label, (weekday_index, period)))

label_to_time = dict(time_options)

required_free_labels = st.multiselect(
    "반드시 공강으로 둘 교시",
    options=list(label_to_time.keys()),
    placeholder="예: 월7교시, 금6교시",
)

required_free_times = tuple(
    sorted(label_to_time[label] for label in required_free_labels)
)


# ============================================================
# 4. 생성 설정
# ============================================================
st.subheader("4. 생성 설정")

preference = st.selectbox(
    "시간표 추천 기준",
    options=[
        "기본",
        "월요일 가볍게",
        "금요일 일찍 끝나기",
        "7교시 최소화",
        "공강 몰기",
        "수학·과학 분산",
    ],
)

display_count = st.slider(
    "화면에 보여줄 시간표 개수",
    min_value=1,
    max_value=150,
    value=5,
)

max_solutions = st.slider(
    "내부 탐색 상한",
    min_value=100,
    max_value=20000,
    value=5000,
    step=100,
)

st.caption(
    "내부 탐색 상한은 앱이 멈추지 않도록 시간표 후보를 최대 몇 개까지 찾을지 정하는 안전장치입니다. "
    "값이 높을수록 더 많은 후보를 보지만, 앱이 느려질 수 있습니다."
)


# ============================================================
# 버튼 연타 방지
# ============================================================
if "last_run_time" not in st.session_state:
    st.session_state.last_run_time = 0


# ============================================================
# 5. 시간표 생성
# ============================================================
st.subheader("5. 시간표 생성")

if st.button("시간표 생성", type="primary"):
    now = time.time()

    if now - st.session_state.last_run_time < 2:
        st.warning("너무 빠르게 다시 실행하고 있습니다. 2초 뒤에 다시 시도하세요.")
        st.stop()

    st.session_state.last_run_time = now

    try:
        with st.spinner("시간표를 계산하는 중입니다..."):
            sols = cached_solve(
                tuple(chosen_courses),
                tuple(sorted(fixed.items())),
                required_free_times,
                max_solutions,
            )

    except Exception as e:
        st.error(f"시간표 생성 중 오류가 발생했습니다: {e}")
        st.stop()

    if not sols:
        st.error(
            "조건을 만족하는 시간표가 없습니다. "
            "고정 블록이나 지정 공강을 줄여 보세요."
        )
        st.stop()

    # 추천 기준 적용
    if preference != "기본":
        sols = sorted(
            sols,
            key=lambda schedule: score_schedule(schedule, preference)
        )

    st.success(
        f"조건을 만족하는 시간표를 {len(sols)}개 찾았습니다. "
        f"(탐색 상한: {max_solutions})"
    )

    if required_free_labels:
        st.info(f"지정 공강: {', '.join(required_free_labels)}")

    st.info(f"추천 기준: {preference}")

    show_n = min(display_count, len(sols))

    tabs = st.tabs([f"{i + 1}번" for i in range(show_n)])

    for i in range(show_n):
        with tabs[i]:
            st.write(f"### {i + 1}번 시간표")

            schedule = sols[i]
            df = schedule_to_dataframe(schedule)

            st.dataframe(df, use_container_width=True)

csv_data = df.to_csv(encoding="utf-8-sig")

st.download_button(
    label="이 시간표를 CSV로 저장",
    data=csv_data,
    file_name=f"timetable_{i + 1}.csv",
    mime="text/csv",
    key=f"download_csv_{i}",
)
            
            st.write("#### 과목별 배정 블록")
            block_df = pd.DataFrame(
                {
                    "과목": list(schedule.keys()),
                    "블록": list(schedule.values()),
                }
            )
            st.dataframe(block_df, use_container_width=True)
