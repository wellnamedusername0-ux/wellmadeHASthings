# timetable_final.py
# Python 3.9+ 권장
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional

# -----------------------------
# 0) 기본 타입
# -----------------------------
WEEKDAYS = ["월", "화", "수", "목", "금"]
Time = Tuple[int, int]  # (weekday_index:0~4, period:1~7)

@dataclass(frozen=True)
class Block:
    code: str
    times: Tuple[Time, ...]

Schedule = Dict[str, str]  # course -> block_code



# ============================================================
BLOCKS: Dict[str, Block] = {


    "4A2": Block("4A2", ((0, 1), (0, 2), (3, 5), (3, 6))),                  # 화12, 목34
    "4B2": Block("4B2", ((1, 5), (1, 6), (3, 3), (3, 4))),                  # 수34, 금12
    "4C2": Block("4C2", ((0, 6), (0, 7), (2, 1), (2, 2))),                  # 월34, 수12
    "4D2": Block("4D2", ((1, 3), (1, 4), (3, 1), (3, 2))),                  # 월12, 목7, 금5
    "4E2": Block("4E2", ((2, 5), (2, 6), (4, 1), (4, 2))),                  # 화67, 금67
    "4F2": Block("4F2", ((0, 3), (0, 4), (2, 3), (2, 4))),                  # 월67, 목12
    "4G2": Block("4G2", ((1, 1), (1, 2), (3, 7), (4, 5))),                  # 수56, 금34
    "4H2": Block("4H2", ((0, 5), (1, 7), (4, 3), (4, 4))),                  # 월5, 화5, 목56

    "2A2": Block("2A2", ((4, 6), (4, 7))),                                  # 화34
    "2D2": Block("2D2", ((4, 1), (4, 2))),                                  # 목12
    "2F2": Block("2F2", ((2, 1), (2, 2))),                                  # 금67
    "2B2": Block("2B2", ((0, 3), (0, 4))),                                  # 월67
    "2C2": Block("2C2", ((0, 6), (0, 7))),                                  # 화67
    "2E2": Block("2E2", ((4, 3), (4, 4))),                                  # 목34


    # TODO: 학교 표에 있는 다른 블록 코드들도 여기에 전부 추가
}



ALL_COURSE_OPTIONS: Dict[str, List[str]] = {

    "문학": ["4B2", "4C2", "4D2", "4E2",  "4F2", "4H2"],
    "세계 문화와 영어": ["4G2", "4B2", "4C2"],
    "미적분1": ["4D2", "4A2", "4B2"],
    "기하": ["4A2", "4B2", "4C2", "4E2"],
    "화학 실험": ["4B2", "4D2"],
    "AP 일반화학 1": ["4A2","4C2", "4E2", "4G2", "4H2"],
    "고급 물리학": ["4C2", "4G2", "4H2"],
    "체육2": ["2A2", "2D2"],
    "음악과 미디어": ["2A2","2F2"],
    "일본어 회화1" : ["4A2"],
    "물리학" : ["4A2", "4B2", "4D2", "4F2"],
    "화학" : ["4F2"],
    "지구과학" : ["4D2"],
    "생명과학" : ["4B2"],
    "윤리와 사상" : ["4B2"],
    "경제" : ["4C2"],
    "중국어 회화 1" : ["4C2"],
    "생명과학 실험" : ["4C2"],
    "AP 미시경제" : ["4C2", "4D2", "4H2"],
    "독서 토론과 글쓰기" : ["4D2"],
    "정치" : ["4D2", "4F2"],
    "영미 문학 읽기" : ["4D2", "4F2", "4H2"],
    "AP 일반생물학 1" : ["4B2", "4D2", "4E2", "4H2"],
    "함수론 과제연구" : ["4F2"],
    "AP 프로그래밍과 문제해결" : ["4G2"],
    "AP 세계사 1" : ["4G2"],
    "AP 통계학 1" : ["4G2", "4H2"],
    "미술 감상과 비평" : ["2A2"],
    "주제 탐구(R&E) 기초" : ["2A2", "2F2"],
    "미술 창작" : ["2B2", "2C2", "2F2"],
    "영어 비판적 사고와 토의 및 토론" : ["2F2"],
    "인공지능을 위한 이산수학" : ["4D2"]
    

    # TODO: 2-1 전체 과목을 여기에 전부 추가
}


# -----------------------------
# 3) 내부 유틸: 충돌/검증
# -----------------------------
def block_times(code: str) -> Set[Time]:
    if code not in BLOCKS:
        raise ValueError(f"알 수 없는 블록 코드: {code} (BLOCKS에 정의 필요)")
    return set(BLOCKS[code].times)

def schedule_to_grid(schedule: Schedule) -> Dict[Time, str]:
    grid: Dict[Time, str] = {}
    for course, bcode in schedule.items():
        for t in BLOCKS[bcode].times:
            if t in grid:
                w, p = t
                raise ValueError(f"시간 충돌: {WEEKDAYS[w]}{p}교시에 {grid[t]} 와 {course}")
            grid[t] = course
    return grid

def validate_course_options(course_options: Dict[str, List[str]]) -> None:
    # 과목 옵션이 BLOCKS에 정의된 코드만 쓰는지 체크
    for c, ops in course_options.items():
        if not ops:
            raise ValueError(f"과목 '{c}'의 가능한 블록이 비어 있습니다.")
        for b in ops:
            if b not in BLOCKS:
                raise ValueError(f"과목 '{c}'의 블록 '{b}'가 BLOCKS에 없습니다. BLOCKS에 먼저 추가하십시오.")

def print_timetable(schedule: Schedule) -> None:
    grid = schedule_to_grid(schedule)
    header = ["교시"] + WEEKDAYS
    print("\n" + " | ".join(f"{h:>10}" for h in header))
    print("-" * (13 * len(header)))
    for period in range(1, 8):
        row = [f"{period:>10}"]
        for w in range(5):
            cell = grid.get((w, period), "공강")
            row.append(f"{cell:>10}")
        print(" | ".join(row))


# -----------------------------
# 4) 백트래킹 + 가지치기(MRV + forward checking)
# -----------------------------
def solve_all(
    course_options: Dict[str, List[str]],
    fixed: Optional[Schedule] = None,
    max_solutions: Optional[int] = 20000
) -> List[Schedule]:
    fixed = fixed or {}

    # fixed 검증
    used_times: Set[Time] = set()
    used_blocks: Set[str] = set()
    for c, b in fixed.items():
        if c not in course_options:
            raise ValueError(f"고정 오류: '{c}'는 선택된 과목 목록에 없습니다.")
        if b not in course_options[c]:
            raise ValueError(f"고정 오류: '{c}'는 '{b}' 블록을 선택할 수 없습니다.")
        if b in used_blocks:
            raise ValueError(f"고정 오류: 블록 '{b}'가 중복 사용되었습니다.")
        tset = block_times(b)
        if used_times & tset:
            raise ValueError(f"고정 오류: '{c}={b}'가 기존 고정과 시간 충돌입니다.")
        used_blocks.add(b)
        used_times |= tset

    courses = list(course_options.keys())
    remaining = [c for c in courses if c not in fixed]

    # 도메인 초기화 + 고정과 충돌나는 블록 제거
    domains: Dict[str, List[str]] = {}
    for c in remaining:
        domains[c] = [b for b in course_options[c] if b not in used_blocks and not (block_times(b) & used_times)]

    # MRV(선택지 최소 과목부터)
    def pick_next(rem: List[str]) -> str:
        return min(rem, key=lambda x: len(domains[x]))

    sols: List[Schedule] = []
    cur: Schedule = dict(fixed)

    def bt(rem: List[str], cur_used_times: Set[Time], cur_used_blocks: Set[str]):
        if max_solutions is not None and len(sols) >= max_solutions:
            return
        if not rem:
            sols.append(dict(cur))
            return

        c = pick_next(rem)
        if not domains[c]:
            return

        for b in domains[c]:
            if b in cur_used_blocks:
                continue
            tset = block_times(b)
            if tset & cur_used_times:
                continue

            # 배정
            cur[c] = b
            new_times = cur_used_times | tset
            new_blocks = cur_used_blocks | {b}

            new_rem = [x for x in rem if x != c]

            # forward checking
            changed: Dict[str, List[str]] = {}
            ok = True
            for x in new_rem:
                old = domains[x]
                new = [bb for bb in old if bb not in new_blocks and not (block_times(bb) & new_times)]
                if len(new) != len(old):
                    changed[x] = old
                    domains[x] = new
                if not domains[x]:
                    ok = False
                    break

            if ok:
                bt(new_rem, new_times, new_blocks)

            # 복구
            for x, old in changed.items():
                domains[x] = old
            del cur[c]

    bt(remaining, used_times, used_blocks)
    return sols


# -----------------------------
# 5) 입력(친구용 UI)
# -----------------------------
def ask_int(prompt: str, default: Optional[int] = None, min_v: Optional[int] = None, max_v: Optional[int] = None) -> int:
    while True:
        s = input(prompt).strip()
        if not s and default is not None:
            return default
        try:
            v = int(s)
            if min_v is not None and v < min_v:
                print(f"값이 너무 작습니다. (최소 {min_v})")
                continue
            if max_v is not None and v > max_v:
                print(f"값이 너무 큽니다. (최대 {max_v})")
                continue
            return v
        except ValueError:
            print("정수를 입력하십시오.")

def ask_courses(all_courses: List[str]) -> List[str]:
    print("\n[과목 선택]")
    print("듣는 과목 번호를 쉼표로 입력하세요. 예: 1,3,7,10")
    for i, c in enumerate(all_courses, start=1):
        print(f"{i:>2}. {c}")

    while True:
        s = input("선택: ").strip()
        if not s:
            print("아무것도 선택되지 않았습니다.")
            continue
        try:
            idxs = [int(x.strip()) for x in s.split(",") if x.strip()]
            chosen = []
            for idx in idxs:
                if idx < 1 or idx > len(all_courses):
                    raise ValueError
                chosen.append(all_courses[idx - 1])
            # 중복 제거(입력 중복 대비)
            chosen = list(dict.fromkeys(chosen))
            return chosen
        except ValueError:
            print("형식 오류입니다. 예: 1,3,7 형태로 입력하십시오.")

def ask_fixed(chosen_courses: List[str], chosen_options: Dict[str, List[str]]) -> Schedule:
    print("\n[고정 블록 입력(선택)]")
    print("고정할 과목이 있으면 입력하세요. 없으면 엔터.")
    print("형식: 과목=블록코드  (예: 미적분1=4D2)")
    print("여러 개면 쉼표로: 미적분1=4D2, 문학=4H2")
    print("\n참고: 선택된 과목별 가능한 블록")
    for c in chosen_courses:
        print(f"- {c}: {', '.join(chosen_options[c])}")

    s = input("고정 입력: ").strip()
    if not s:
        return {}

    fixed: Schedule = {}
    parts = [x.strip() for x in s.split(",") if x.strip()]
    for part in parts:
        if "=" not in part:
            raise ValueError("형식 오류: '='가 필요합니다.")
        course, block = [x.strip() for x in part.split("=", 1)]
        if course not in chosen_options:
            raise ValueError(f"고정 오류: '{course}'는 선택된 과목이 아닙니다.")
        fixed[course] = block
    return fixed


def main():
    print("=== 시간표 자동 생성기 (입력형) ===")

    # (관리자용) 데이터 무결성 체크
    validate_course_options(ALL_COURSE_OPTIONS)

    all_courses = sorted(ALL_COURSE_OPTIONS.keys())
    chosen_courses = ask_courses(all_courses)

    # 선택된 과목의 옵션만 추출
    chosen_options: Dict[str, List[str]] = {c: ALL_COURSE_OPTIONS[c] for c in chosen_courses}

    # 탐색 상한(너무 크면 오래 걸릴 수 있어 제한 권장)
    max_solutions = ask_int("\n최대 몇 개 시간표까지 탐색할까요? (기본 20000): ", default=20000, min_v=1, max_v=200000)

    # 고정 입력
    try:
        fixed = ask_fixed(chosen_courses, chosen_options)

        sols = solve_all(chosen_options, fixed=fixed, max_solutions=max_solutions)
        print(f"\n가능한 시간표 개수(탐색 상한 {max_solutions} 기준): {len(sols)}")

        if not sols:
            print("조건을 만족하는 시간표가 없습니다.")
            return

        # 첫 번째 결과 출력
        print("\n[1번 시간표]")
        print_timetable(sols[0])

        # 다른 해 보기
        while True:
            if len(sols) <= 1:
                break
            ans = input(f"\n다른 시간표를 볼까요? (1~{len(sols)} 중 번호 / q 종료): ").strip().lower()
            if ans in ("q", "quit", "exit"):
                break
            if not ans:
                continue
            try:
                idx = int(ans)
                if 1 <= idx <= len(sols):
                    print(f"\n[{idx}번 시간표]")
                    print_timetable(sols[idx - 1])
                else:
                    print("범위를 벗어났습니다.")
            except ValueError:
                print("숫자 또는 q를 입력하십시오.")

    except Exception as e:
        print("\n[오류]", e)


if __name__ == "__main__":
    main()
