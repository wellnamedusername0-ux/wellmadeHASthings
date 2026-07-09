import importlib
import time

import pandas as pd
import streamlit as st


# ------------------------------------------------------------
# 기존 시간표 알고리즘 파일 불러오기
# 파일 이름: 시간표_알고리즘2.py
# ------------------------------------------------------------
solver = importlib.import_module("시간표_알고리즘2")


st.set_page_config(
    page_title="시간표 자동 생성기",
    page_icon="📅",
    layout="wide",
)

st.title("📅 시간표 자동 생성기")
st.caption("과목을 선택하고, 필요한 경우에만 일부 과목의 블록을 고정한 뒤 시간표를 생성합니다.")


# ------------------------------------------------------------
# 데이터 검증
# ------------------------------------------------------------
try:
    solver.validate_course_options(solver.ALL_COURSE_OPTIONS)
except Exception as e:
    st.error(f"데이터 오류가 있습니다: {e}")
    st.stop()


# ------------------------------------------------------------
# 시간표를 표(DataFrame)로 바꾸는 함수
# ------------------------------------------------------------
def schedule_to_dataframe(schedule):
    grid = solver.schedule_to_grid(schedule)

    periods = list(range(1, 8))
    df = pd.DataFrame(index=periods, columns=solver.WEEKDAYS)

    for period in periods:
        for weekday_index, weekday_name in enumerate(solver.WEEKDAYS):
            df.loc[period, weekday_name] = grid.get((weekday_index, period), "공강")

    df.index.name = "교시"
    return df


# ------------------------------------------------------------
# 캐싱된 시간표 계산 함수
# 같은 조건으로 여러 번 눌러도 매번 새로 계산하지 않게 함
# ------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cached_solve(chosen_courses_tuple, fixed_tuple, max_solutions):
    chosen_courses = list(chosen_courses_tuple)
    fixed = dict(fixed_tuple)

    chosen_options = {
        course: solver.ALL_COURSE_OPTIONS[course]
        for course in chosen_courses
    }

    return solver.solve_all(
        chosen_options,
        fixed=fixed,
        max_solutions=max_solutions,
    )


# ------------------------------------------------------------
# 과목 선택
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# 고정 블록 선택
# ------------------------------------------------------------
st.subheader("2. 고정할 과목 선택")

st.write(
    "고정하고 싶은 과목만 블록을 선택하세요. "
    "고정하지 않아도 됩니다."
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


# ------------------------------------------------------------
# 출력 개수 / 탐색 제한
# ------------------------------------------------------------
st.subheader("3. 생성 설정")

display_count = st.slider(
    "화면에 보여줄 시간표 개수",
    min_value=1,
    max_value=20,
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
    "내부 탐색 상한이 클수록 더 많은 경우를 찾을 수 있지만, "
    "앱이 느려질 수 있습니다."
)


# ------------------------------------------------------------
# 버튼 연타 방지
# ------------------------------------------------------------
if "last_run_time" not in st.session_state:
    st.session_state.last_run_time = 0


# ------------------------------------------------------------
# 시간표 생성
# ------------------------------------------------------------
st.subheader("4. 시간표 생성")

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
                max_solutions,
            )

    except Exception as e:
        st.error(f"시간표 생성 중 오류가 발생했습니다: {e}")
        st.stop()

    if not sols:
        st.error("조건을 만족하는 시간표가 없습니다. 고정 조건을 줄여 보세요.")
        st.stop()

    st.success(
        f"조건을 만족하는 시간표를 {len(sols)}개 찾았습니다. "
        f"(탐색 상한: {max_solutions})"
    )

    show_n = min(display_count, len(sols))

    tabs = st.tabs([f"{i + 1}번" for i in range(show_n)])

    for i in range(show_n):
        with tabs[i]:
            st.write(f"### {i + 1}번 시간표")

            schedule = sols[i]
            df = schedule_to_dataframe(schedule)

            st.dataframe(df, use_container_width=True)

            st.write("#### 과목별 배정 블록")
            block_df = pd.DataFrame(
                {
                    "과목": list(schedule.keys()),
                    "블록": list(schedule.values()),
                }
            )
            st.dataframe(block_df, use_container_width=True)
