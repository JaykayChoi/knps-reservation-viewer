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

    # ✅ 주수 파라미터 (1~10), 기본 8주
    try:
        weeks = int(request.args.get("weeks", "8"))
    except Exception:
        weeks = 8
    if weeks < 1 or weeks > 10:
        weeks = 8
    total_days = weeks * 7

    # ✅ 요일 파라미터: Python weekday() 기준 (월=0 ... 일=6). 기본값: 토요일(5)
    raw_days = request.args.get("days", "5")
    try:
        selected_days = {int(x) for x in raw_days.split(",") if x != ""}
        selected_days = {d for d in selected_days if 0 <= d <= 6}
    except Exception:
        selected_days = {5}
    if not selected_days:
        selected_days = {5}

    # ✅ 시설 파라미터: 기본값 세 가지 모두
    default_types = {"특화야영장", "카라반", "자동차야영장"}
    raw_types = request.args.get("types", ",".join(default_types))
    selected_types = {x.strip() for x in raw_types.split(",") if x.strip()}
    if not selected_types:
        selected_types = set(default_types)

    # ✅ 조회 대상 날짜 구성
    target_dates = [
        (today + datetime.timedelta(days=i)).strftime("%Y%m%d")
        for i in range(total_days)
        if (today + datetime.timedelta(days=i)).weekday() in selected_days
    ]

    print(f"[API] 주수={weeks}, 요일={sorted(selected_days)}, 시설={sorted(selected_types)} / 조회일자수={len(target_dates)}")

    filtered_results = []

    for date in target_dates:
        try:
            url = "https://reservation.knps.or.kr/reservation/selectCampRemainSiteList.do"
            data = {"prd_sal_ymd": date, "park": ""}
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest"
            }

            resp = requests.post(url, data=data, headers=headers, timeout=10)
            resp.raise_for_status()
            result = resp.json()

            filtered = [
                {**item, "query_date": date}
                for item in result.get("list", [])
                if item.get("prdCtgNm") in selected_types
                and (item.get("cntN") or 0) > 0
                and item.get("officeNm") not in ("북한산", "한려해상", "다도해해상", "지리산경남", "무등산동부")
            ]

            filtered_results.extend(filtered)

        except Exception as e:
            print(f"[{date}] 호출 실패: {e}")

    return jsonify(filtered_results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
