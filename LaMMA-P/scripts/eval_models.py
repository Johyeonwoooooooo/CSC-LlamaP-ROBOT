"""LaMMA-P 모델 비교 평가 하니스 (GPT vs Llama 등).

execute_plan.py(3단계, 무료)를 task 폴더마다 N회 돌려서, 실행 끝에 출력되는
LaMMA-P 지표 줄(SR/TC/GCR/Exec/RU)을 파싱·집계한다.

⚠️ 이 하니스는 '실행/집계'만 한다. 유료 생성 단계(1·2단계)는 건드리지 않으므로
   GPT/Llama 플랜을 미리 만들어 둔 폴더 이름을 넘겨줘야 한다.

전형적 사용 흐름
----------------
  # (사전) GPT로 플랜 생성 → 폴더 A,B,C / Llama로 생성 → 폴더 D,E,F  (모델별 따로 생성)

  # GPT 폴더들 평가 (각 3회 반복)
  python scripts/eval_models.py --model gpt --runs 3 A B C

  # Llama 폴더들 평가 (각 3회 반복)
  python scripts/eval_models.py --model llama --runs 3 D E F

  # 누적된 결과로 비교표 출력
  python scripts/eval_models.py --summarize

결과는 eval_results.csv 에 누적되고, 모델별 평균표를 콘솔에 찍는다.
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)

# end_thread.py 가 찍는 줄:  "SR:1, TC:1, GCR:1.0, Exec:0.875, RU:1"
METRIC_RE = re.compile(
    r"SR:([\d.]+),\s*TC:([\d.]+),\s*GCR:([\d.]+),\s*Exec:([\d.]+),\s*RU:([\d.]+)"
)
METRICS = ["SR", "TC", "GCR", "Exec", "RU"]


def parse_metrics(text: str):
    """실행 출력에서 마지막 지표 줄을 찾아 dict 로. 없으면 None."""
    matches = METRIC_RE.findall(text)
    if not matches:
        return None
    last = matches[-1]  # 여러 번 찍히면 마지막 것 사용
    return {k: float(v) for k, v in zip(METRICS, last)}


def run_once(command: str, timeout: int):
    """execute_plan.py 를 1회 실행하고 (metrics_dict 또는 None, status) 반환."""
    cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "execute_plan.py"),
           "--command", command]
    try:
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as e:
        # 무한루프(로봇 막힘 등)로 안 끝난 경우
        out = (e.stdout or "") + (e.stderr or "")
        m = parse_metrics(out if isinstance(out, str) else out.decode(errors="ignore"))
        return m, ("TIMEOUT" if m is None else "TIMEOUT_BUT_GOT_METRIC")
    out = proc.stdout + "\n" + proc.stderr
    m = parse_metrics(out)
    if m is None:
        return None, "NO_METRIC"  # 크래시 등으로 지표를 못 찍음
    return m, "OK"


def zero_metrics():
    return {k: 0.0 for k in METRICS}


def evaluate(model: str, commands, runs: int, timeout: int, out_csv: str):
    rows = []
    print(f"\n=== 평가: model={model}, tasks={len(commands)}, runs/task={runs}, "
          f"timeout={timeout}s ===\n")
    for command in commands:
        for r in range(1, runs + 1):
            print(f"[{model}] {command}  (run {r}/{runs}) ... ", end="", flush=True)
            metrics, status = run_once(command, timeout)
            if metrics is None:
                # 실패: 모든 지표 0 으로 기록 (성공률 계산에 반영)
                metrics = zero_metrics()
            print(f"{status}  " + ", ".join(f"{k}={metrics[k]}" for k in METRICS))
            row = {"model": model, "command": command, "run": r,
                   "status": status, **metrics}
            rows.append(row)

    # CSV 누적 (헤더는 파일 없을 때만)
    fieldnames = ["model", "command", "run", "status"] + METRICS
    write_header = not os.path.exists(out_csv)
    with open(out_csv, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerows(rows)
    print(f"\n[저장] {out_csv} 에 {len(rows)}행 추가")

    print_model_avg(model, rows)
    return rows


def print_model_avg(model: str, rows):
    if not rows:
        return
    n = len(rows)
    avg = {k: sum(r[k] for r in rows) / n for k in METRICS}
    n_ok = sum(1 for r in rows if r["status"].startswith("OK"))
    print(f"\n--- {model} 평균 (n={n} runs, 정상종료={n_ok}) ---")
    print("  " + " | ".join(f"{k}={avg[k]:.3f}" for k in METRICS))


def summarize(out_csv: str):
    if not os.path.exists(out_csv):
        print(f"결과 파일 없음: {out_csv}. 먼저 평가를 돌리세요.")
        return
    by_model = defaultdict(list)
    with open(out_csv, newline="") as f:
        for row in csv.DictReader(f):
            for k in METRICS:
                row[k] = float(row[k])
            by_model[row["model"]].append(row)

    print(f"\n================ 모델 비교 (출처: {out_csv}) ================\n")
    header = f"| {'model':<12} | {'runs':>4} | {'정상종료':>6} | " + \
             " | ".join(f"{k:>6}" for k in METRICS) + " |"
    sep = "|" + "-" * (len(header) - 2) + "|"
    print(header)
    print(sep)
    for model, rows in by_model.items():
        n = len(rows)
        n_ok = sum(1 for r in rows if str(r["status"]).startswith("OK"))
        avg = {k: sum(r[k] for r in rows) / n for k in METRICS}
        line = f"| {model:<12} | {n:>4} | {n_ok:>6} | " + \
               " | ".join(f"{avg[k]:>6.3f}" for k in METRICS) + " |"
        print(line)
    print("\n지표: SR=최종성공, TC=과제완료, GCR=목표조건달성률, Exec=액션성공률, RU=자원효율")


def main():
    p = argparse.ArgumentParser(description="LaMMA-P 모델 비교 평가 하니스")
    p.add_argument("commands", nargs="*",
                   help="평가할 logs/ 하위 폴더 이름들 (해당 모델로 미리 생성된 것)")
    p.add_argument("--model", type=str, default=None,
                   help="이 폴더들의 모델 라벨 (예: gpt, llama3.1:8b)")
    p.add_argument("--runs", type=int, default=3,
                   help="task당 반복 횟수 (랜덤 위치 보정, 기본 3)")
    p.add_argument("--timeout", type=int, default=600,
                   help="한 실행 최대 초 (무한루프 방지, 기본 600)")
    p.add_argument("--out", type=str, default=os.path.join(REPO_ROOT, "eval_results.csv"),
                   help="결과 CSV 경로")
    p.add_argument("--summarize", action="store_true",
                   help="실행 없이 기존 CSV로 비교표만 출력")
    args = p.parse_args()

    if args.summarize:
        summarize(args.out)
        return

    if not args.model or not args.commands:
        p.error("평가하려면 --model 과 폴더 이름(들)이 필요합니다. "
                "(비교표만 보려면 --summarize)")

    evaluate(args.model, args.commands, args.runs, args.timeout, args.out)
    print("\n비교표를 보려면:  python scripts/eval_models.py --summarize")


if __name__ == "__main__":
    main()
