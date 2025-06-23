import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase credential bilgilerini secrets'ten alıyoruz
firebase_config = st.secrets["firebase"]

cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred)

db = firestore.client()

# Artık db ile istediğin işlemi yapabilirsin


# Kullanıcı Girişi
def login():
    st.subheader("Giriş Yap")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        user_ref = db.collection("users").document(username)
        user = user_ref.get()
        if user.exists and user.to_dict().get("password") == password:
            st.session_state["username"] = username
            st.success("Giriş Başarılı!")
            st.experimental_rerun()
        else:
            st.error("Kullanıcı adı veya şifre hatalı.")

# Kayıt Olma
def register():
    st.subheader("Kayıt Ol")
    username = st.text_input("Yeni Kullanıcı Adı")
    password = st.text_input("Yeni Şifre", type="password")
    if st.button("Kayıt Ol"):
        user_ref = db.collection("users").document(username)
        if user_ref.get().exists:
            st.error("Bu kullanıcı adı zaten alınmış.")
        else:
            user_ref.set({
                "password": password,
                "created_at": datetime.now().isoformat(),
                "ihaleler": [],
                "giderler": []
            })
            st.success("Kayıt başarılı, giriş yapabilirsiniz.")
            st.experimental_rerun()

# İhale Ekle
def ihale_ekle():
    st.subheader("Yeni İhale")
    tur = st.text_input("İhale Türü")
    bedel = st.number_input("İhale Bedeli ($)", min_value=0.0)
    urun_maliyet = st.number_input("Ürün Birim Maliyeti ($)", min_value=0.0)
    adet = st.number_input("Ürün Sayısı", min_value=0)
    if st.button("Kaydet"):
        yeni_ihale = {
            "tur": tur,
            "bedel": bedel,
            "urun_maliyet": urun_maliyet,
            "adet": adet,
            "tarih": datetime.now().isoformat()
        }
        doc_ref = db.collection("users").document(st.session_state["username"])
        doc = doc_ref.get().to_dict()
        doc["ihaleler"].append(yeni_ihale)
        doc_ref.set(doc)
        st.success("İhale kaydedildi.")

# Rapor Göster
def rapor():
    st.subheader("İhale Raporu")
    doc = db.collection("users").document(st.session_state["username"]).get().to_dict()
    ihaleler = doc.get("ihaleler", [])
    if not ihaleler:
        st.warning("Henüz ihale kaydı yok.")
        return
    df = pd.DataFrame(ihaleler)
    df["tarih"] = pd.to_datetime(df["tarih"])
    df["toplam_maliyet"] = df["urun_maliyet"] * df["adet"]
    df["kar"] = df["bedel"] - df["toplam_maliyet"]
    st.dataframe(df[["tur", "bedel", "toplam_maliyet", "kar", "tarih"]])
    st.line_chart(df.set_index("tarih")[["bedel", "toplam_maliyet", "kar"]])

# Ana Ekran
def main():
    st.title("📦 İhale Takip Uygulaması")
    if "username" not in st.session_state:
        secim = st.radio("Lütfen seçin", ["Giriş Yap", "Kayıt Ol"])
        if secim == "Giriş Yap":
            login()
        else:
            register()
    else:
        st.sidebar.success(f"Hoş geldin {st.session_state['username']}")
        sayfa = st.sidebar.selectbox("Sayfa Seç", ["İhale Girişi", "Rapor", "Çıkış"])
        if sayfa == "İhale Girişi":
            ihale_ekle()
        elif sayfa == "Rapor":
            rapor()
        elif sayfa == "Çıkış":
            del st.session_state["username"]
            st.experimental_rerun()

if __name__ == "__main__":
    main()
