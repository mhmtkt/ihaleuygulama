import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import json
import os

# Firebase başlat (secrets üzerinden)
if not firebase_admin._apps:
    firebase_info = {
        "type": st.secrets["FIREBASE"]["type"],
        "project_id": st.secrets["FIREBASE"]["project_id"],
        "private_key_id": st.secrets["FIREBASE"]["private_key_id"],
        "private_key": st.secrets["FIREBASE"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["FIREBASE"]["client_email"],
        "client_id": st.secrets["FIREBASE"]["client_id"],
        "auth_uri": st.secrets["FIREBASE"]["auth_uri"],
        "token_uri": st.secrets["FIREBASE"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["FIREBASE"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["FIREBASE"]["client_x509_cert_url"]
    }
    cred = credentials.Certificate(firebase_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ------------------- Yardımcı Fonksiyon -------------------
def sayi_formatla(sayi):
    if sayi >= 1_000_000:
        return f"{sayi/1_000_000:.2f}M"
    elif sayi >= 1000:
        return f"{sayi/1000:.1f}K"
    else:
        return str(sayi)

# ------------------- Giriş & Kayıt -------------------
def login():
    st.subheader("Giriş Yap")
    username = st.text_input("Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        doc_ref = db.collection("users").document(username)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict()["password"] == password:
            st.session_state["user"] = username
            st.experimental_rerun()
        else:
            st.error("Hatalı giriş.")

def register():
    st.subheader("Kayıt Ol")
    username = st.text_input("Yeni Kullanıcı Adı")
    password = st.text_input("Şifre", type="password")
    if st.button("Kayıt Ol"):
        doc_ref = db.collection("users").document(username)
        if doc_ref.get().exists:
            st.error("Bu kullanıcı zaten var.")
        else:
            doc_ref.set({
                "password": password,
                "profile": {},
                "ihaleler": [],
                "giderler": []
            })
            st.success("Kayıt başarılı!")
            st.experimental_rerun()

# ------------------- Profil Ayarı -------------------
def profil():
    st.subheader("Profil Bilgileri")
    doc_ref = db.collection("users").document(st.session_state["user"])
    data = doc_ref.get().to_dict()
    profil = data.get("profile", {})

    garage = st.number_input("Garaj Seviyesi", value=profil.get("garage", 1), step=1)
    vehicles = st.number_input("Araç Sayısı", value=profil.get("vehicles", 0), step=1)
    names = []
    for i in range(vehicles):
        names.append(st.text_input(f"Araç {i+1}", value=profil.get("names", [""]*vehicles)[i] if len(profil.get("names", [])) > i else ""))

    if st.button("Kaydet"):
        doc_ref.update({
            "profile": {
                "garage": garage,
                "vehicles": vehicles,
                "names": names
            }
        })
        st.success("Profil güncellendi.")

# ------------------- İhale Ekle -------------------
def ihale():
    st.subheader("İhale Girişi")
    tur = st.text_input("İhale Türü")
    bedel = st.number_input("İhale Bedeli ($)", min_value=0.0)
    maliyet = st.number_input("Birim Maliyet ($)", min_value=0.0)
    adet = st.number_input("Ürün Adedi", min_value=0)
    if st.button("İhale Kaydet"):
        yeni = {
            "tur": tur,
            "bedel": bedel,
            "maliyet": maliyet,
            "adet": adet,
            "tarih": datetime.now().isoformat()
        }
        ref = db.collection("users").document(st.session_state["user"])
        doc = ref.get().to_dict()
        ihaleler = doc.get("ihaleler", [])
        ihaleler.append(yeni)
        ref.update({"ihaleler": ihaleler})
        st.success("İhale kaydedildi.")

# ------------------- Gider Ekle -------------------
def gider():
    st.subheader("Gider Ekle")
    kategori = st.selectbox("Kategori", ["Araç Bakımı", "Maaş", "Dorse", "Diğer"])
    tutar = st.number_input("Tutar ($)", min_value=0.0)
    if st.button("Gider Kaydet"):
        yeni = {
            "kategori": kategori,
            "tutar": tutar,
            "tarih": datetime.now().isoformat()
        }
        ref = db.collection("users").document(st.session_state["user"])
        doc = ref.get().to_dict()
        giderler = doc.get("giderler", [])
        giderler.append(yeni)
        ref.update({"giderler": giderler})
        st.success("Gider kaydedildi.")

# ------------------- Rapor -------------------
def rapor():
    st.subheader("Günlük Rapor")
    doc = db.collection("users").document(st.session_state["user"]).get().to_dict()
    today = datetime.now().date()

    ihaleler = [i for i in doc.get("ihaleler", []) if datetime.fromisoformat(i["tarih"]).date() == today]
    giderler = [g for g in doc.get("giderler", []) if datetime.fromisoformat(g["tarih"]).date() == today]

    gelir = sum(i["bedel"] for i in ihaleler)
    maliyet = sum(i["maliyet"] * i["adet"] for i in ihaleler)
    gider_toplam = sum(g["tutar"] for g in giderler)
    kar = gelir - maliyet - gider_toplam

    st.write(f"Toplam Gelir: {sayi_formatla(gelir)} $")
    st.write(f"Toplam Maliyet: {sayi_formatla(maliyet)} $")
    st.write(f"Gider: {sayi_formatla(gider_toplam)} $")
    st.write(f"Kar: {sayi_formatla(kar)} $")

# ------------------- Ana -------------------
def main():
    st.title("İhale Takip Sistemi (Firebase)")
    if "user" not in st.session_state:
        secim = st.radio("Seçim yapınız:", ["Giriş", "Kayıt Ol"])
        if secim == "Giriş":
            login()
        else:
            register()
    else:
        st.sidebar.success(f"👋 Hoşgeldin {st.session_state['user']}")
        sayfa = st.sidebar.radio("Sayfa Seç", ["Profil", "İhale", "Gider", "Rapor", "Çıkış"])
        if sayfa == "Profil":
            profil()
        elif sayfa == "İhale":
            ihale()
        elif sayfa == "Gider":
            gider()
        elif sayfa == "Rapor":
            rapor()
        elif sayfa == "Çıkış":
            del st.session_state["user"]
            st.experimental_rerun()

if __name__ == "__main__":
    main()
