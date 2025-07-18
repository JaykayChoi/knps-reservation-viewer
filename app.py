from flask import Flask, render_template, jsonify
import requests
import datetime
import os

# https://chatgpt.com/c/6879d68b-0568-8007-9fa0-1bf3f5c05cb4

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/reservations")
def reservations():
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=60)

    # ✅ 오늘부터 60일 동안의 모든 토요일 구하기
    saturdays = [
        (today + datetime.timedelta(days=i)).strftime("%Y%m%d")
        for i in range((end_date - today).days + 1)
        if (today + datetime.timedelta(days=i)).weekday() == 5
    ]

    print(f"조회할 토요일 날짜 목록: {saturdays}")

    filtered_results = []

    for date in saturdays:
        try:
            url = "https://reservation.knps.or.kr/reservation/selectCampRemainSiteList.do"
            data = {
                "prd_sal_ymd": date,
                "park": ""
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest"
            }

            resp = requests.post(url, data=data, headers=headers)
            result = resp.json()

            filtered = [
                {**item, "query_date": date}  # 날짜도 함께 반환
                for item in result.get("list", [])
                if item["prdCtgNm"] in ("특화야영장", "카라반")
                and item["cntN"] > 0
                and item["officeNm"] not in ("북한산", "한려해상")  # 제외할 공원
            ]

            filtered_results.extend(filtered)

        except Exception as e:
            print(f"[{date}] 호출 실패: {e}")

    return jsonify(filtered_results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Starting server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
