import streamlit as st
from datetime import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase başlat
def initialize_firebase():
    service_account_json = st.secrets["firebase"]["firebase_service_account"]
    cred_dict = json.loads(service_account_json)
    cred = credentials.Certificate(cred_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# Kullanıcı işlemleri
def kullanici_var_mi(username):
    return db.collection("users").document(username).get().exists

def kullanici_kaydet(username, data):
    db.collection("users").document(username).set(data)

def kullanici_getir(username):
    doc = db.collection("users").document(username).get()
    return doc.to_dict() if doc.exists else None

# Giriş fonksiyonu
def login():
    st.subheader("Giriş Yap")
    username = st.text_input("Kullanıcı Adı", key="login_user")
    password = st.text_input("Şifre", type="password", key="login_pass")
    if st.button("Giriş Yap"):
        user = kullanici_getir(username)
        if user and user.get("password") == password:
            st.session_state["logged_in_user"] = username
            st.success(f"Hoşgeldin {username}!")
            st.experimental_rerun()
        else:
            st.error("Kullanıcı adı veya şifre yanlış.")

# Kayıt fonksiyonu
def register():
    st.subheader("Kayıt Ol")
    username = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
    password = st.text_input("Yeni Şifre", type="password", key="reg_pass")
    if st.button("Kayıt Ol"):
        if not username or not password:
            st.error("Kullanıcı adı ve şifre boş olamaz.")
            return
        if kullanici_var_mi(username):
            st.error("Bu kullanıcı adı zaten alınmış.")
            return
        data = {"password": password, "ihaleler": [], "operasyonel_giderler": [], "profile": {}}
        kullanici_kaydet(username, data)
        st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
        st.experimental_rerun()

# Profil bilgisi güncelle
def get_profile_info():
    st.subheader("Profil Bilgilerinizi Girin")
    username = st.session_state["logged_in_user"]
    user = kullanici_getir(username)
    profil = user.get("profile", {})

    garage_level = st.number_input("Garaj Seviyeniz", min_value=1, max_value=100, value=profil.get("garage_level",1))
    vehicle_count = st.number_input("Araç Sayınız", min_value=0, max_value=100, value=profil.get("vehicle_count",0))
    trailer_count = st.number_input("Toplam Dorse Sayınız", min_value=0, max_value=100, value=profil.get("trailer_count",0))
    vehicle_names = profil.get("vehicle_names", [])
    yeni_vehicle_names = []

    for i in range(vehicle_count):
        default_name = vehicle_names[i] if i < len(vehicle_names) else ""
        name = st.text_input(f"{i+1}. Araç Adı", value=default_name, key=f"vehicle_{i}")
        yeni_vehicle_names.append(name)

    if st.button("Profil Bilgilerini Kaydet"):
        if vehicle_count > 0 and any(name.strip() == "" for name in yeni_vehicle_names):
            st.error("Tüm araç isimlerini doldurmalısınız.")
            return
        yeni_profil = {
            "garage_level": garage_level,
            "vehicle_count": vehicle_count,
            "vehicle_names": yeni_vehicle_names,
            "trailer_count": trailer_count
        }
        user["profile"] = yeni_profil
        kullanici_kaydet(username, user)
        st.success("Profil bilgileri kaydedildi.")

# İhale girişi
def ihale_girisi():
    st.subheader("İhale Girişi")

    ihale_turu = st.text_input("İhale Türü (örneğin: Kimyasal)")
    ihale_bedeli = st.number_input("İhalenin Toplam Bedeli (Dolar)", min_value=0.0, step=0.01)
    urun_birim_maliyeti = st.number_input("Birim Ürün Maliyeti (Dolar)", min_value=0.0, step=0.01)
    urun_sayisi = st.number_input("Ürün Sayısı (Adet)", min_value=0)

    if st.button("İhale Kaydet"):
        if ihale_turu == "":
            st.error("İhale türü boş olamaz.")
            return
        username = st.session_state["logged_in_user"]
        user = kullanici_getir(username)

        yeni_ihale = {
            "ihale_turu": ihale_turu,
            "ihale_bedeli": ihale_bedeli,
            "urun_birim_maliyeti": urun_birim_maliyeti,
            "urun_sayisi": urun_sayisi,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        user.setdefault("ihaleler", []).append(yeni_ihale)
        kullanici_kaydet(username, user)
        st.success("İhale kaydedildi.")

# Operasyonel giderler
def operasyonel_giderler():
    st.subheader("Operasyonel Giderler")
    username = st.session_state["logged_in_user"]
    user = kullanici_getir(username)

    kategori = st.selectbox("Gider Kategorisi", [
        "Garaj Bakımı",
        "Garaj Seviye Yükseltmesi",
        "Maaş Ödemesi",
        "Araç Bakımı",
        "Araç Alımı",
        "Araç Satımı",
        "Dorse Alımı",
        "Emeklilik ve İşten Kovma",
        "Araç Yükseltme Bedeli"
    ])

    gider_detay = {}
    if kategori == "Garaj Bakımı":
        tutar = st.number_input("Garaj Bakım Tutarı (Dolar)", min_value=0.0, step=0.01)
        gider_detay["tutar"] = tutar
    elif kategori == "Garaj Seviye Yükseltmesi":
        yeni_seviye = st.number_input("Yeni Garaj Seviyesi", min_value=1, max_value=100, step=1)
        maliyet = st.number_input("Yükseltme Maliyeti (Dolar)", min_value=0.0, step=0.01)
        gider_detay["yeni_seviye"] = yeni_seviye
        gider_detay["tutar"] = maliyet
    elif kategori == "Maaş Ödemesi":
        sofor_adi = st.text_input("Şoför Adı")
        maas = st.number_input("Maaş Tutarı (Dolar)", min_value=0.0, step=0.01)
        gider_detay["sofor_adi"] = sofor_adi
        gider_detay["tutar"] = maas
    elif kategori == "Araç Bakımı":
        arac_listesi = user.get("profile", {}).get("vehicle_names", [])
        if not arac_listesi:
            st.warning("Önce profil bilgilerini doldurun.")
            return
        arac_secimi = st.selectbox("Araç Seçin", arac_listesi)
        bakim_tutari = st.number_input("Bakım Maliyeti (Dolar)", min_value=0.0, step=0.01)
        gider_detay["arac_adi"] = arac_secimi
        gider_detay["tutar"] = bakim_tutari
    elif kategori == "Araç Alımı":
        arac_adi = st.text_input("Alınan Araç Adı")
        maliyet = st.number_input("Araç Maliyeti (Dolar)", min_value=0.0, step=0.01)
        gider_detay["arac_adi"] = arac_adi
        gider_detay["tutar"] = maliyet
    elif kategori == "Araç Satımı":
        arac_listesi = user.get("profile", {}).get("vehicle_names", [])
        if not arac_listesi:
            st.warning("Önce profil bilgilerini doldurun.")
            return
        arac_secimi = st.selectbox("Satılan Araç", arac_listesi)
        satis_tutari = st.number_input("Satış Tutarı (Dolar)", min_value=0.0, step=0.01)
        gider_detay["arac_adi"] = arac_secimi
        gider_detay["tutar"] = -satis_tutari
    elif kategori == "Dorse Alımı":
        dorse_tipi = st.text_input("Dorse Tipi")
        maliyet = st.number_input("Dorse Maliyeti (Dolar)", min_value=0.0, step=0.01)
        gider_detay["dorse_tipi"] = dorse_tipi
        gider_detay["tutar"] = maliyet
    elif kategori == "Emeklilik ve İşten Kovma":
        sofor_adi = st.text_input("Şoför Adı")
        tazminat = st.number_input("Tazminat Tutarı (Dolar)", min_value=0.0, step=0.01)
        gider_detay["sofor_adi"] = sofor_adi
        gider_detay["tutar"] = tazminat
    elif kategori == "Araç Yükseltme Bedeli":
        arac_listesi = user.get("profile", {}).get("vehicle_names", [])
        if not arac_listesi:
            st.warning("Önce profil bilgilerini doldurun.")
            return
        arac_secimi = st.selectbox("Araç Seçin", arac_listesi)
        tutar = st.number_input("Yükseltme Bedeli (Dolar)", min_value=0.0, step=0.01)
        gider_detay["arac_adi"] = arac_secimi
        gider_detay["tutar"] = tutar

    if st.button("Gider Kaydet"):
        if "tutar" not in gider_detay:
            st.error("Lütfen tutar bilgisi girin.")
            return
        user.setdefault("operasyonel_giderler", []).append({
            "kategori": kategori,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **gider_detay
        })
        # Garaj seviyesi yükseltme varsa güncelle
        if kategori == "Garaj Seviye Yükseltmesi":
            user["profile"]["garage_level"] = gider_detay["yeni_seviye"]
        # Araç alımıysa araç listesine ekle ve araç sayısını artır
        if kategori == "Araç Alımı":
            user["profile"].setdefault("vehicle_names", []).append(gider_detay["arac_adi"])
            user["profile"]["vehicle_count"] = len(user["profile"]["vehicle_names"])
        kullanici_kaydet(username, user)
        st.success("Operasyonel gider kaydedildi.")
        st.experimental_rerun()

# Rapor görüntüle
def rapor_goruntule():
    st.subheader("Raporlar")
    username = st.session_state["logged_in_user"]
    user = kullanici_getir(username)

    ihaleler = user.get("ihaleler", [])
    giderler = user.get("operasyonel_giderler", [])

    st.write("İhaleler")
    st.dataframe(ihaleler if ihaleler else [])

    st.write("Operasyonel Giderler")
    st.dataframe(giderler if giderler else [])

    toplam_gelir = sum(i.get("ihale_bedeli", 0) for i in ihaleler)
    toplam_gider = sum(g.get("tutar", 0) for g in giderler)
    kar = toplam_gelir - toplam_gider

    st.write(f"Toplam İhale Geliri: {toplam_gelir:.2f} $")
    st.write(f"Toplam Gider: {toplam_gider:.2f} $")
    st.write(f"Toplam Kar: {kar:.2f} $")

# Çıkış yap
def cikis_yap():
    if "logged_in_user" in st.session_state:
        del st.session_state["logged_in_user"]
    st.success("Çıkış yapıldı.")
    st.experimental_rerun()

# Ana uygulama
def main():
    st.title("İhale Takip Uygulaması")
    if "logged_in_user" not in st.session_state:
        secim = st.selectbox("Giriş veya Kayıt Ol", ["Giriş Yap", "Kayıt Ol"])
        if secim == "Giriş Yap":
            login()
        else:
            register()
    else:
        st.sidebar.write(f"Hoşgeldin, {st.session_state['logged_in_user']}")
        menu = st.sidebar.radio("Menü", ["Profil", "İhale Girişi", "Operasyonel Giderler", "Raporlar", "Çıkış Yap"])
        if menu == "Profil":
            get_profile_info()
        elif menu == "İhale Girişi":
            ihale_girisi()
        elif menu == "Operasyonel Giderler":
            operasyonel_giderler()
        elif menu == "Raporlar":
            rapor_goruntule()
        elif menu == "Çıkış Yap":
            cikis_yap()

if __name__ == "__main__":
    main()
