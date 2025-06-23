import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Admin başlat (secrets.toml'dan al)
def init_firebase():
    firebase_config = {
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        # Buradaki \n karakterlerini gerçek satıra çevir
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
    }

    try:
        app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(firebase_config)
        app = firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

def kayitlari_yukle():
    users_ref = db.collection('users')
    users = {}
    for doc in users_ref.stream():
        users[doc.id] = doc.to_dict()['password']
    return users

def kayit_ekle(username, password):
    doc_ref = db.collection('users').document(username)
    doc_ref.set({"password": password})

def main():
    st.title("İhale Takip Uygulaması")

    if 'users' not in st.session_state:
        st.session_state['users'] = kayitlari_yukle()
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ""

    if st.session_state['logged_in']:
        st.write(f"Hoşgeldin, {st.session_state['username']}!")
        if st.button("Çıkış Yap"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
    else:
        menu = st.selectbox("Seçim yap", ["Giriş Yap", "Kayıt Ol"])

        if menu == "Kayıt Ol":
            st.subheader("Kayıt Ol")
            new_username = st.text_input("Kullanıcı Adı (Yeni)")
            new_password = st.text_input("Şifre (Yeni)", type="password")
            if st.button("Kayıt Ol"):
                if new_username.strip() == "" or new_password.strip() == "":
                    st.error("Boş bırakmayınız.")
                elif new_username in st.session_state['users']:
                    st.error("Bu kullanıcı zaten var.")
                else:
                    kayit_ekle(new_username, new_password)
                    st.success("Kayıt başarılı!")
                    st.session_state['users'][new_username] = new_password

        else:
            st.subheader("Giriş Yap")
            username = st.text_input("Kullanıcı Adı", key="login_username")
            password = st.text_input("Şifre", type="password", key="login_password")
            if st.button("Giriş Yap"):
                if username in st.session_state['users'] and st.session_state['users'][username] == password:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success(f"Hoşgeldin {username}!")
                else:
                    st.error("Kullanıcı adı veya şifre yanlış.")

if __name__ == "__main__":
    main()
