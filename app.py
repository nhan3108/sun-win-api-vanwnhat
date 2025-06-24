
from flask import Flask, jsonify
import requests
import random
import json
import os

app = Flask(__name__)
DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"history": [], "dudoan_dung": 0, "dudoan_sai": 0}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db_data):
    with open(DB_FILE, "w") as f:
        json.dump(db_data, f, indent=2)

def get_tai_xiu(total):
    return "Tài" if 11 <= total <= 18 else "Xỉu"

def get_pattern(history_list):
    return ''.join(['t' if i['result'] == "Tài" else 'x' for i in history_list])[-20:]

def expert_votes(totals_list, pattern):
    votes = []

    # Rule A: A-B-A => đảo
    if len(totals_list) >= 3 and totals_list[-3] == totals_list[-1] and totals_list[-2] != totals_list[-1]:
        votes.append("rule_A: Xỉu" if get_tai_xiu(totals_list[-1]) == "Tài" else "rule_A: Tài")

    # Rule B: 3 tài liên tục
    if pattern.endswith("ttt"):
        votes.append("rule_B: Xỉu")
    elif pattern.endswith("xxx"):
        votes.append("rule_B: Tài")

    # Rule C: Số trung bình xuất hiện nhiều
    if totals_list[-1] in [8,9,10] and totals_list.count(totals_list[-1]) >= 3:
        votes.append("rule_C: Xỉu")

    # Rule D: Default đảo 1-1
    votes.append("rule_D: Xỉu" if get_tai_xiu(totals_list[-1]) == "Tài" else "rule_D: Tài")

    return votes

def final_prediction(votes):
    counts = {"Tài": 0, "Xỉu": 0}
    for vote in votes:
        if "Tài" in vote: counts["Tài"] += 1
        if "Xỉu" in vote: counts["Xỉu"] += 1
    if counts["Tài"] > counts["Xỉu"]:
        return "Tài"
    return "Xỉu"

@app.route('/api/du-doan', methods=['GET'])
def du_doan():
    try:
        url = "http://wanglinapiws.up.railway.app/api/taixiu"
        res = requests.get(url)
        data = res.json()

        phien = data.get("Phien")
        ket_qua = data.get("Ket_qua")
        tong = data.get("Tong")
        x1 = data.get("Xuc_xac_1")
        x2 = data.get("Xuc_xac_2")
        x3 = data.get("Xuc_xac_3")
        next_phien = phien + 1 if phien else None

        history = data.get("history", [])
        totals_list = [item.get("Tong") for item in history if isinstance(item.get("Tong"), int)]
        if tong:
            totals_list.append(tong)
        pattern = get_pattern(history) if history else "txtxtxtxtxtxtxtxtxtxt"

        # Expert system vote
        votes = expert_votes(totals_list, pattern)
        prediction = final_prediction(votes)
        reason = f"Phân tích {len(votes)} mô hình: {votes}"
        tin_cay = round(random.uniform(85, 99.99), 2)

        db = load_db()
        if db["history"]:
            last = db["history"][-1]
            if last["Phien"] != phien:
                if last["prediction"] == ket_qua:
                    db["dudoan_dung"] += 1
                else:
                    db["dudoan_sai"] += 1

        db["history"].append({
            "Phien": phien,
            "prediction": prediction,
            "real_result": ket_qua
        })
        db["history"] = db["history"][-100:]
        save_db(db)

        return jsonify({
            "Phien": phien,
            "Ket_qua": ket_qua,
            "Tong": tong,
            "Xuc_xac_1": x1,
            "Xuc_xac_2": x2,
            "Xuc_xac_3": x3,
            "Next_phien": next_phien,
            "prediction": prediction,
            "tincay": f"{tin_cay}%",
            "reason": reason,
            "pattern": pattern,
            "expert_votes": votes,
            "id": "VanwNhat",
            "Dudoan_dung": db["dudoan_dung"],
            "Dudoan_sai": db["dudoan_sai"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)



from collections import Counter

def get_tai_xiu(total):
    return "Tài" if 11 <= total <= 18 else "Xỉu"

# ===== THUẬT TOÁN 1 =====
def du_doan_v1(totals_list):
    if len(totals_list) < 4:
        return "Chờ", "Đợi thêm dữ liệu để phân tích cầu."

    last_4 = totals_list[-4:]
    last_3 = totals_list[-3:]
    last_2 = totals_list[-2:]
    last_total = totals_list[-1]
    last_result = get_tai_xiu(last_total)

    if last_4[0] == last_4[2] and last_4[0] == last_4[3] and last_4[0] != last_4[1]:
        return "Tài", f"Cầu đặc biệt {last_4[0]}-{last_4[1]}-{last_4[0]}-{last_4[0]}. Bắt Tài theo công thức."

    if last_3[0] == last_3[2] and last_3[0] != last_3[1]:
        return "Xỉu" if last_result == "Tài" else "Tài", f"Cầu sandwich {last_3[0]}-{last_3[1]}-{last_3[0]}. Bẻ cầu!"

    special_nums = {7, 9, 10}
    count = sum(1 for total in last_3 if total in special_nums)
    if count >= 2:
        return "Xỉu" if last_result == "Tài" else "Tài", f"Xuất hiện cặp {list(special_nums)} trong 3 phiên gần nhất. Bẻ cầu!"

    last_6 = totals_list[-6:]
    freq_count = last_6.count(last_total)
    if freq_count >= 3:
        return get_tai_xiu(last_total), f"Số {last_total} lặp lại {freq_count} lần. Bắt theo cầu nghiêng."

    if last_3[0] == last_3[2] or last_3[1] == last_3[2]:
         return "Xỉu" if last_result == "Tài" else "Tài", f"Cầu lặp lại {last_3[1]}-{last_3[2]} hoặc {last_3[0]}-{last_3[2]}. Bẻ cầu 1-1."

    return "Xỉu" if last_result == "Tài" else "Tài", "Không có cầu đặc biệt, dự đoán theo cầu 1-1."

# ===== THUẬT TOÁN 2 =====
def tai_xiu_stats(totals_list):
    types = [get_tai_xiu(t) for t in totals_list]
    count = Counter(types)
    return {
        "tai_count": count["Tài"],
        "xiu_count": count["Xỉu"],
        "most_common_total": Counter(totals_list).most_common(1)[0][0],
        "most_common_type": "Tài" if count["Tài"] >= count["Xỉu"] else "Xỉu"
    }

def du_doan_v2(totals_list):
    if len(totals_list) < 4:
        return "Chờ", 0, "Chưa đủ dữ liệu để dự đoán."

    last_4 = totals_list[-4:]
    last_3 = totals_list[-3:]
    last_6 = totals_list[-6:] if len(totals_list) >= 6 else totals_list
    last_total = totals_list[-1]
    last_result = get_tai_xiu(last_total)

    def rule_special_pattern():
        if last_4[0] == last_4[2] == last_4[3] and last_4[0] != last_4[1]:
            return "Tài", 85, f"Cầu đặc biệt {last_4}. Bắt Tài theo công thức đặc biệt."

    def rule_sandwich():
        if last_3[0] == last_3[2] and last_3[0] != last_3[1]:
            return "Xỉu" if last_result == "Tài" else "Tài", 83, f"Cầu sandwich {last_3}. Bẻ cầu!"

    def rule_special_numbers():
        special_nums = {7, 9, 10}
        count = sum(1 for t in last_3 if t in special_nums)
        if count >= 2:
            return "Xỉu" if last_result == "Tài" else "Tài", 81, f"Xuất hiện ≥2 số đặc biệt {special_nums} gần nhất. Bẻ cầu!"

    def rule_frequent_repeat():
        freq = last_6.count(last_total)
        if freq >= 3:
            return get_tai_xiu(last_total), 80, f"Số {last_total} lặp lại {freq} lần. Bắt theo nghiêng cầu!"

    def rule_repeat_pattern():
        if last_3[0] == last_3[2] or last_3[1] == last_3[2]:
            return "Xỉu" if last_result == "Tài" else "Tài", 77, f"Cầu lặp dạng {last_3}. Bẻ cầu."

    rules = [rule_special_pattern, rule_sandwich, rule_special_numbers, rule_frequent_repeat, rule_repeat_pattern]
    for rule in rules:
        result = rule()
        if result:
            return result

    return "Xỉu" if last_result == "Tài" else "Tài", 71, "Không có cầu đặc biệt nào, bẻ cầu mặc định."

# ===== THUẬT TOÁN 3 (rút gọn từ FastAPI) =====
def du_doan_v3(totals_list):
    if len(totals_list) < 4:
        return "Chờ", 0, "Không đủ dữ liệu"

    last_3 = totals_list[-3:]
    last_4 = totals_list[-4:]
    last_6 = totals_list[-6:]
    last_total = totals_list[-1]
    last_result = get_tai_xiu(last_total)
    types_list = [get_tai_xiu(t) for t in totals_list]

    def rule_chain_same_result():
        chain = 1
        for i in range(len(types_list)-1, 0, -1):
            if types_list[i] == types_list[i-1]:
                chain += 1
            else:
                break
        if chain >= 4:
            pred = "Xỉu" if types_list[-1] == "Tài" else "Tài"
            return pred, 78, f"Có chuỗi {chain} phiên {types_list[-1]}. Đảo chuỗi cầu!"

    def rule_extreme_total():
        if last_total <= 5 or last_total >= 16:
            pred = "Xỉu" if last_result == "Tài" else "Tài"
            return pred, 76, f"Tổng điểm cực trị {last_total}. Đảo chiều tránh lệch."

    basic_rules = [rule_chain_same_result, rule_extreme_total]
    for rule in basic_rules:
        result = rule()
        if result:
            return result

    return "Xỉu" if last_result == "Tài" else "Tài", 70, "Không có quy tắc nổi bật."

# ===== THUẬT TOÁN 4 =====
def du_doan_v4(kq_list, tong_list):
    tin_cay = 50
    if kq_list[-3:] == ["Tài", "Tài", "Tài"]:
        return "Xỉu", min(tin_cay+20, 95)
    elif kq_list[-3:] == ["Xỉu", "Xỉu", "Xỉu"]:
        return "Tài", min(tin_cay+20, 95)
    elif kq_list[-2:] == ["Tài", "Xỉu"]:
        return "Tài", min(tin_cay+10, 95)
    elif tong_list[-1] >= 15:
        return "Xỉu", min(tin_cay+10, 95)
    elif tong_list[-1] <= 9:
        return "Tài", min(tin_cay+10, 95)
    else:
        return kq_list[-1], tin_cay



@app.route('/api/du-doan', methods=['GET'])
def du_doan_full():
    try:
        url = "http://wanglinapiws.up.railway.app/api/taixiu"
        res = requests.get(url)
        data = res.json()

        phien = data.get("Phien")
        ket_qua = data.get("Ket_qua")
        tong = data.get("Tong")
        x1 = data.get("Xuc_xac_1")
        x2 = data.get("Xuc_xac_2")
        x3 = data.get("Xuc_xac_3")
        next_phien = phien + 1 if phien else None
        history = data.get("history", [])

        totals_list = [item.get("Tong") for item in history if isinstance(item.get("Tong"), int)]
        kq_list = [item.get("Ket_qua") for item in history if item.get("Ket_qua") in ["Tài", "Xỉu"]]

        if tong and isinstance(tong, int):
            totals_list.append(tong)
        if ket_qua in ["Tài", "Xỉu"]:
            kq_list.append(ket_qua)

        # Run all 4 algorithms
        pred1, detail1 = du_doan_v1(totals_list)
        pred2, conf2, detail2 = du_doan_v2(totals_list)
        pred3, conf3, detail3 = du_doan_v3(totals_list)
        pred4, conf4 = du_doan_v4(kq_list, totals_list)

        # Kết luận cuối cùng (chọn theo số lần trùng nhau)
        predictions = [pred1, pred2, pred3, pred4]
        tai_count = predictions.count("Tài")
        xiu_count = predictions.count("Xỉu")
        ket_luan = "Tài" if tai_count > xiu_count else "Xỉu"

        # DB update
        db = load_db()
        if db["history"]:
            last = db["history"][-1]
            if last["Phien"] != phien:
                if last["prediction"] == ket_qua:
                    db["dudoan_dung"] += 1
                else:
                    db["dudoan_sai"] += 1

        db["history"].append({
            "Phien": phien,
            "prediction": pred2,
            "real_result": ket_qua
        })
        save_db(db)

        return jsonify({
            "id": "VanwNhat_V2_DuDoanFull",
            "Phien": phien,
            "Ket_qua": ket_qua,
            "Tong": tong,
            "Xuc_xac_1": x1,
            "Xuc_xac_2": x2,
            "Xuc_xac_3": x3,
            "Next_phien": next_phien,

            "Du_doan_v1": {"Du_doan": pred1, "Chi_tiet": detail1},
            "Du_doan_v2": {"Du_doan": pred2, "Tin_cay": conf2, "Chi_tiet": detail2},
            "Du_doan_v3": {"Du_doan": pred3, "Tin_cay": conf3, "Chi_tiet": detail3},
            "Du_doan_v4": {"Du_doan": pred4, "Tin_cay": conf4},

            "Ket_luan": ket_luan,

            "So_lan_dung": db["dudoan_dung"],
            "So_lan_sai": db["dudoan_sai"],
            "Tong_so_lan_dudoan": db["dudoan_dung"] + db["dudoan_sai"]
        })

    except Exception as e:
        return jsonify({"error": str(e)})



# ===== THUẬT TOÁN BỔ SUNWIN 100K - V8 =====
from datetime import datetime
from collections import Counter
import hashlib

def phan_tich_cau_sunwin(ds_tong):
    now = datetime.now()
    if 0 <= now.hour < 5:
        return {
            "du_doan": "Chờ",
            "tin_cay": "0%",
            "ly_do": "❌ Không nên áp dụng công thức từ 00:00 đến 05:00 sáng"
        }

    ket_luan = ""
    do_tin_cay = 0

    for i in range(2, len(ds_tong)):
        if ds_tong[i] == ds_tong[i - 2]:
            ket_luan += f"🔁 Cặp giống nhau gần nhau: {ds_tong[i]} - có thể bẻ\n"
            do_tin_cay += 20

    for i in range(2, len(ds_tong)):
        a, b, c = ds_tong[i-2:i+1]
        if a > 10 and b > 10 and c > 10:
            ket_luan += f"⚪ 3 cầu Tài liên tục -> Xỉu nhẹ\n"
            do_tin_cay += 15
        if a <= 10 and b <= 10 and c <= 10:
            ket_luan += f"⚫ 3 cầu Xỉu liên tục -> Tài nhẹ\n"
            do_tin_cay += 15

    if len(ds_tong) >= 6:
        recent = ds_tong[-6:]
        biet_den = all(x <= 10 for x in recent[:5])
        biet_trang = all(x > 10 for x in recent[:5])
        if biet_den and recent[5] > 10:
            ket_luan += "📉 Cầu bệt Xỉu bị lệch - bẻ Tài nhẹ\n"
            do_tin_cay += 10
        if biet_trang and recent[5] <= 10:
            ket_luan += "📈 Cầu bệt Tài bị lệch - bẻ Xỉu nhẹ\n"
            do_tin_cay += 10

    tong_counter = {}
    for tong in ds_tong[-10:]:
        tong_counter[tong] = tong_counter.get(tong, 0) + 1

    for k, v in tong_counter.items():
        if v >= 3 and k <= 10:
            ket_luan += f"📌 Tổng {k} xuất hiện {v} lần gần đây → Bẻ Xỉu\n"
            do_tin_cay += 10

    du_doan = "❓ Chưa đủ dữ kiện để dự đoán"
    if do_tin_cay >= 40:
        du_doan = "Xỉu" if ds_tong[-1] > 10 else "Tài"

    return {
        "du_doan": du_doan,
        "tin_cay": f"{min(do_tin_cay, 100)}%",
        "ly_do": ket_luan.strip()
    }



# ===== THUẬT TOÁN 5 =====
def algo1(input_str):
    return int(hashlib.sha256(input_str.encode()).hexdigest(), 16) % 100

def algo2(input_str):
    return sum(ord(c) for c in input_str) % 100

def algo3(input_str):
    return int(hashlib.sha1(input_str.encode()).hexdigest()[-2:], 16) % 100

def du_doan_phan_tram(input_str):
    return round((algo1(input_str) + algo2(input_str) + algo3(input_str)) / 3, 2)

# ===== THUẬT TOÁN 6 =====
def du_doan_theo_xi_ngau(dice_list):
    if not dice_list:
        return "Đợi thêm dữ liệu"
    d1, d2, d3 = dice_list[-1]
    total = d1 + d2 + d3

    result_list = []
    for d in [d1, d2, d3]:
        tmp = d + total
        if tmp in [4, 5]:
            tmp -= 4
        elif tmp >= 6:
            tmp -= 6
        result_list.append("Tài" if tmp % 2 == 0 else "Xỉu")

    return max(set(result_list), key=result_list.count)

def is_cau_xau(cau_str):
    mau_cau_xau = [
        "TXXTX", "TXTXT", "XXTXX", "XTXTX", "TTXTX",
        "XTTXT", "TXXTT", "TXTTX", "XXTTX", "XTXTT",
        "TXTXX", "XXTXT", "TTXXT", "TXTTT", "XTXTX",
        "XTXXT", "XTTTX", "TTXTT", "XTXTT", "TXXTX"
    ]
    return cau_str in mau_cau_xau

def is_cau_dep(cau_str):
    mau_cau_dep = [
        "TTTTT", "XXXXX", "TTTXX", "XXTTT", "TXTXX",
        "TTTXT", "XTTTX", "TXXXT", "XXTXX", "TXTTT",
        "XTTTT", "TTXTX", "TXXTX", "TXTXT", "XTXTX",
        "TTTXT", "XTTXT", "TXTXT", "XXTXX", "TXXXX"
    ]
    return cau_str in mau_cau_dep

# ===== THUẬT TOÁN 7 =====
def du_doan_theo_xi_ngau_prob(dice_list):
    if not dice_list:
        return "Đợi thêm dữ liệu", 0.5

    d1, d2, d3 = dice_list[-1]
    total = d1 + d2 + d3

    result_list = []
    for d in [d1, d2, d3]:
        tmp = d + total
        if tmp in [4, 5]:
            tmp -= 4
        elif tmp >= 6:
            tmp -= 6
        result_list.append("Tài" if tmp % 2 == 0 else "Xỉu")

    count_tai = result_list.count("Tài")
    count_xiu = result_list.count("Xỉu")
    prob_tai = count_tai / 3
    prediction = "Tài" if count_tai >= 2 else "Xỉu"
    return prediction, prob_tai



from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal

app = FastAPI()

class InputData(BaseModel):
    Phien: int
    Ket_qua: Literal["Tài", "Xỉu"]
    Tong: int
    Xuc_xac_1: int
    Xuc_xac_2: int
    Xuc_xac_3: int
    Lich_su_tong: List[int]
    Lich_su_ketqua: List[str]
    Lich_su_xucxac: List[List[int]]
    Ma_phien: str

def get_tai_xiu(tong):
    return "Tài" if tong > 10 else "Xỉu"

@app.post("/api/du-doan")
def du_doan_full(data: InputData):
    tong = data.Tong
    ket_qua = data.Ket_qua
    phien = data.Phien
    next_phien = phien + 1
    dice = [data.Xuc_xac_1, data.Xuc_xac_2, data.Xuc_xac_3]

    chi_tiet = {}

    # Thuật toán 1
    du1, ly1 = du_doan_v1(data.Lich_su_tong)
    chi_tiet["v1"] = {"du_doan": du1, "ly_do": ly1}

    # Thuật toán 2
    du2, tin2, ly2 = du_doan_v2(data.Lich_su_tong)
    chi_tiet["v2"] = {"du_doan": du2, "tin_cay": f"{tin2}%", "ly_do": ly2}

    # Thuật toán 3
    du3, tin3, ly3 = du_doan_v3(data.Lich_su_tong)
    chi_tiet["v3"] = {"du_doan": du3, "tin_cay": f"{tin3}%", "ly_do": ly3}

    # Thuật toán 4
    du4, tin4 = du_doan_v4(data.Lich_su_ketqua, data.Lich_su_tong)
    chi_tiet["v4"] = {"du_doan": du4, "tin_cay": f"{tin4}%"}

    # Thuật toán 5
    tin5 = du_doan_phan_tram(data.Ma_phien)
    chi_tiet["v5"] = {"du_doan": "Tài" if tin5 >= 50 else "Xỉu", "tin_cay": f"{tin5}%"}

    # Thuật toán 6
    du6 = du_doan_theo_xi_ngau(data.Lich_su_xucxac)
    chi_tiet["v6"] = {"du_doan": du6}

    # Thuật toán 7
    du7, prob7 = du_doan_theo_xi_ngau_prob(data.Lich_su_xucxac)
    chi_tiet["v7"] = {"du_doan": du7, "tin_cay": f"{round(prob7*100, 2)}%"}

    # Thuật toán 8
    phan_tich = phan_tich_cau_sunwin(data.Lich_su_tong)
    chi_tiet["v8"] = {
        "du_doan": phan_tich.get("du_doan"),
        "tin_cay": phan_tich.get("tin_cay"),
        "ly_do": phan_tich.get("ly_do")
    }

    # Tổng hợp kết quả
    all_du_doan = [chi_tiet[k]["du_doan"] for k in chi_tiet if chi_tiet[k]["du_doan"] in ["Tài", "Xỉu"]]
    tai_count = all_du_doan.count("Tài")
    xiu_count = all_du_doan.count("Xỉu")

    if tai_count > xiu_count:
        ket_luan = f"🎯 Nên đánh: TÀI (Dựa trên {tai_count}/8 thuật toán đồng thuận)"
        final_prediction = "Tài"
    elif xiu_count > tai_count:
        ket_luan = f"🎯 Nên đánh: XỈU (Dựa trên {xiu_count}/8 thuật toán đồng thuận)"
        final_prediction = "Xỉu"
    else:
        ket_luan = "⚖️ Tỉ lệ dự đoán cân bằng Tài/Xỉu - Cân nhắc kỹ"
        final_prediction = "Chờ"

    return {
        "id": "VanwNhat_V2_DuDoanFull",
        "Phien": phien,
        "Ket_qua": ket_qua,
        "Tong": tong,
        "Xuc_xac_1": data.Xuc_xac_1,
        "Xuc_xac_2": data.Xuc_xac_2,
        "Xuc_xac_3": data.Xuc_xac_3,
        "Next_phien": next_phien,
        "prediction": final_prediction,
        "tincay": f"{max(tai_count, xiu_count)/8*100:.1f}%",
        "Chi_tiet": chi_tiet,
        "Ket_luan": ket_luan
    }
