from flask import Flask, render_template, jsonify, request
import requests
import datetime
import os

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/reservations")
def reservations():
    today = datetime.date.today()
    target_dates = []

    # ✅ 기간 지정 파라미터 (start_date, end_date) 확인
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if start_date_str and end_date_str:
        # 👉 [B] 기간이 지정된 경우: 요일 상관없이 해당 기간의 모든 날짜를 탐색
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            delta = end_date - start_date
            for i in range(delta.days + 1):
                day = start_date + datetime.timedelta(days=i)
                target_dates.append(day.strftime("%Y%m%d"))
            
            print(f"[API] 기간 지정 조회: {start_date_str} ~ {end_date_str} / 조회일자수={len(target_dates)}")

        except Exception as e:
            print(f"[API] 날짜 파싱 오류: {e}")
            target_dates = []

    # 기간 지정 파라미터가 없으면 기존 로직(주, 요일) 사용
    if not target_dates:
        # 👉 [A] 기간이 지정되지 않은 경우: n주 이내의 선택된 요일만 탐색
        try:
            weeks = int(request.args.get("weeks", "8"))
        except Exception:
            weeks = 8
        if weeks < 1 or weeks > 10:
            weeks = 8
        total_days = weeks * 7

        raw_days = request.args.get("days", "5")
        try:
            selected_days = {int(x) for x in raw_days.split(",") if x != ""}
            selected_days = {d for d in selected_days if 0 <= d <= 6}
        except Exception:
            selected_days = {5}
        if not selected_days:
            selected_days = {5}
        
        target_dates = [
            (today + datetime.timedelta(days=i)).strftime("%Y%m%d")
            for i in range(total_days)
            if (today + datetime.timedelta(days=i)).weekday() in selected_days
        ]
        print(f"[API] 주/요일 조회: 주수={weeks}, 요일={sorted(selected_days)} / 조회일자수={len(target_dates)}")

    # 시설 파라미터 (공통)
    raw_types = request.args.get("types", "특화야영장,카라반")
    selected_types = {x.strip() for x in raw_types.split(",") if x.strip()}
    if not selected_types:
        selected_types = {"특화야영장", "카라반"}

    # 이하 API 호출 로직은 동일
    filtered_results = []
    for date in target_dates:
        try:
            url = "https://reservation.knps.or.kr/reservation/selectCampRemainSiteList.do"
            data = {"prd_sal_ymd": date, "park": ""}
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            }
            resp = requests.post(url, data=data, headers=headers, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            filtered = [
                {**item, "query_date": date}
                for item in result.get("list", [])
                if item.get("prdCtgNm") in selected_types
                and (item.get("cntN") or 0) > 0
                and item.get("officeNm")
                not in ("북한산", "한려해상", "다도해해상", "지리산경남", "무등산동부")
            ]
            filtered_results.extend(filtered)
        except Exception as e:
            print(f"[{date}] 호출 실패: {e}")

    return jsonify(filtered_results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)