import joblib

# Load Model
tm = joblib.load("models/ticket_classifier.pkl")
nm = joblib.load("models/network_classifier.pkl")

# Keyword Rules
GANGGUAN_KW = ["lemot", "rto", "putus", "rusak", "error", "gagal", "tidak bisa", "mati", "down", "404", "500", "lambat", "trouble", "kendala"]
REQUEST_KW = ["minta", "mohon", "pasang", "buat", "pemasangan", "reset", "pengajuan", "tambah", "peminjaman", "setting"]

def predict_smart(text):
    t = text.lower()
    
    # Predict Ticket Type
    if any(k in t for k in GANGGUAN_KW):
        tt = "Gangguan"
    elif any(k in t for k in REQUEST_KW):
        tt = "Request"
    else:
        tt = tm.predict([t])[0]

    # Predict Network Component
    if any(k in t for k in ["website", "web", "portal", "url", "http", "https", "404", "500"]):
        nc = "Website Access"
    elif any(k in t for k in ["vpn", "forticlient", "openvpn"]):
        nc = "VPN"
    elif any(k in t for k in ["wifi", "kabel", "lan", "port"]):
        nc = "LAN Infrastructure"
    elif any(k in t for k in ["ip address", "ip", "dhcp"]):
        nc = "IP Address"
    else:
        nc = nm.predict([t])[0]

    return tt, nc

if __name__ == "__main__":
    test_cases = [
        "wifi lantai 3 sangat lemot dan sering rto",
        "forticlient vpn gagal terhubung ke server pusat",
        "minta tolong pasangkan kabel lan baru",
        "website portal internal tidak bisa diakses error 404",
        "minta reset password akun wifi"
    ]

    print("=" * 60)
    print("HASIL PENGUJIAN MODEL HYBRID AI + RULES")
    print("=" * 60)
    for kalimat in test_cases:
        tt, nc = predict_smart(kalimat)
        print(f"Kalimat : '{kalimat}'")
        print(f"  ├─ Ticket Type   : {tt}")
        print(f"  └─ Network Compo : 🎯 {nc}\n")