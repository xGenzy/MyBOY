from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS = [6787850468, 6057026596]

STOK_FILE = "stok_akun.txt"
RIWAYAT_FOLDER = "riwayat"
MAINTENANCE_FILE = "maintenance.txt"
BANNED_FILE = "banned.txt"
NOTIF_AUDIO = "notifikasi.ogg"

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

admin_state = {}
jumlah_beli_user = {}
refund_state = {}
pesanan_timeout = {}
user_list = set()
HARGA_PER_AKUN = 1000

server = Flask('')

@server.route('/')
def home():
    return "Bot aktif!"

def keep_alive():
    Thread(target=lambda: server.run(host="0.0.0.0", port=8080)).start()

def get_stok():
    if not os.path.exists(STOK_FILE): return []
    with open(STOK_FILE) as f: return [x.strip() for x in f if x.strip()]

def save_stok(stok_list):
    with open(STOK_FILE, "w") as f: f.write("\n".join(stok_list))

def log_riwayat(user_id, akun):
    if not os.path.exists(RIWAYAT_FOLDER): os.makedirs(RIWAYAT_FOLDER)
    with open(f"{RIWAYAT_FOLDER}/{user_id}.txt", "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {akun}\n")

def is_maintenance():
    return os.path.exists(MAINTENANCE_FILE)

def is_banned(user_id):
    if not os.path.exists(BANNED_FILE): return False
    with open(BANNED_FILE) as f:
        return str(user_id) in f.read()

def get_keyboard(user_id):
    if user_id in ADMIN_IDS:
        return ReplyKeyboardMarkup([
            ["➕ Add stock"],
            ["🔁 check stock"],
            ["🗑️ Reset Stok"],
            ["🚫 Ban User"],
            ["📋 Cek Pesanan", "📣 Broadcast"],
            ["📊 Statistik"],
            ["🛠️ Maintenance"],
            ["💰 Ubah Harga"], 
            ["🗑️ Clear messages"]
        ], resize_keyboard=True)
    return ReplyKeyboardMarkup([
        ["🛍️ Buy G-Mail"],
        ["🔁 check stock"],
        ["📬 History ", "🆘 Refund"],
        ["🗑️ Clear messages"]
    ], resize_keyboard=True)

@app.on_message(filters.command("start") & filters.private)
def start(client, msg):
    user_id = msg.from_user.id
    if is_banned(user_id):
        return msg.reply("🚫 Kamu telah dibanned dari bot ini.")
    user_list.add(user_id)
    if is_maintenance() and user_id not in ADMIN_IDS:
        return msg.reply("🔧 Bot sedang maintenance.")
    msg.reply("👋 Selamat datang di Bot Jual Akun Gmail\n\n✅ Stok update tiap hari\n⚡ Proses instan\n🛡️ Garansi akun\n\nGunakan tombol di bawah ini:", reply_markup=get_keyboard(user_id))

@app.on_message(filters.text & filters.private)
def handle_text(client, msg):
    user_id = msg.from_user.id
    text = msg.text.strip()
    state = admin_state.get(user_id)
    if is_banned(user_id):
        return msg.reply("🚫 Kamu telah dibanned dari bot ini.")
    if is_maintenance() and user_id not in ADMIN_IDS and text not in ["/start", "🗑️ Clear messages"]:
        return msg.reply("🔧 Bot sedang maintenance.")

    if text == "🗑️ Clear messages":
        for i in range(20):
            try: client.delete_messages(user_id, msg.id - i)
            except: continue
        return

    if text == "🔁 check stock":
        stok = get_stok()
        return msg.reply(f"📦 Stok tersedia: {len(stok)} akun")

    if text == "🛍️ Buy G-Mail":
        stok = get_stok()
        if not stok:
            return msg.reply("❌ Maaf, stok habis.")
        msg.reply(f"📦 Stok: {len(stok)} akun\nMasukkan jumlah akun yang ingin dibeli:")
        admin_state[user_id] = "input_jumlah_beli"
        return

    if text == "📬 History ":
        path = f"{RIWAYAT_FOLDER}/{user_id}.txt"
        if os.path.exists(path):
            with open(path) as f:
                return msg.reply("📬 History  kamu:\n\n" + f.read()[-4000:])
        return msg.reply("❌ Belum ada riwayat pembelian")

    if text == "🆘 Refund":
        refund_state[user_id] = "wait_rekening"
        return msg.reply("🔁 Kirim data refund kamu:\n\nBank:\nNama:\nRekening:\nNominal:\nAlasan:")

    if text == "🔗 Share Bot":
        username = client.get_me().username
        return msg.reply("🔗 Bagikan bot ini:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Sekarang", url=f"https://t.me/{username}?start=share")]
        ]))

    if text == "➕ Add stock" and user_id in ADMIN_IDS:
        admin_state[user_id] = "tambah_stok"
        return msg.reply("📥 Kirim daftar akun (1 akun per baris).")

    if text == "🗑️ Reset Stok" and user_id in ADMIN_IDS:
        save_stok([])
        return msg.reply("🗑️ Stok berhasil direset.")

    if text == "📊 Statistik" and user_id in ADMIN_IDS:
        total_user = len(user_list)
        total_riwayat = sum(len(open(f"{RIWAYAT_FOLDER}/{f}").readlines()) for f in os.listdir(RIWAYAT_FOLDER))
        return msg.reply(f"📊 Statistik:\n👤 User: {total_user}\n📦 Penjualan: {total_riwayat}")

    if text == "🛠️ Maintenance" and user_id in ADMIN_IDS:
        if os.path.exists(MAINTENANCE_FILE):
            os.remove(MAINTENANCE_FILE)
            return msg.reply("✅ Maintenance dimatikan.")
        open(MAINTENANCE_FILE, "w").close()
        return msg.reply("✅ Maintenance diaktifkan.")

    if text == "📋 Cek Pesanan" and user_id in ADMIN_IDS:
        laporan = ""
        for f in os.listdir(RIWAYAT_FOLDER):
            with open(os.path.join(RIWAYAT_FOLDER, f)) as riw:
                jumlah = len(riw.readlines())
                laporan += f"- {f.replace('.txt','')}: {jumlah} akun\n"
        return msg.reply("📋 Pesanan:\n" + (laporan or "Belum ada."))

    if text == "📣 Broadcast" and user_id in ADMIN_IDS:
        admin_state[user_id] = "broadcast"
        return msg.reply("📝 Kirim pesan broadcast:")

    if text == "💰 Ubah Harga" and user_id in ADMIN_IDS:
        admin_state[user_id] = "ubah_harga"
        return msg.reply("💰 Masukkan harga baru per akun:")

    if text == "🚫 Ban User" and user_id in ADMIN_IDS and msg.reply_to_message:
        banned_id = msg.reply_to_message.from_user.id
        with open(BANNED_FILE, "a") as f:
            f.write(str(banned_id) + "\n")
        return msg.reply("✅ User dibanned.")

    if text == "✅ Unban User" and user_id in ADMIN_IDS and msg.reply_to_message:
        banned_id = str(msg.reply_to_message.from_user.id)
        if os.path.exists(BANNED_FILE):
            with open(BANNED_FILE) as f:
                lines = f.readlines()
            with open(BANNED_FILE, "w") as f:
                f.writelines([x for x in lines if x.strip() != banned_id])
        return msg.reply("✅ User diunban.")

    if state == "broadcast" and user_id in ADMIN_IDS:
        for uid in user_list:
            try: client.send_message(uid, f"📢 {text}")
            except: continue
        admin_state.pop(user_id, None)
        return msg.reply("✅ Broadcast dikirim.")

    if state == "ubah_harga" and user_id in ADMIN_IDS:
        try:
            harga_baru = int(text)
            global HARGA_PER_AKUN
            HARGA_PER_AKUN = harga_baru
            admin_state.pop(user_id, None)
            return msg.reply(f"✅ Harga diperbarui: Rp{HARGA_PER_AKUN:,}")
        except:
            return msg.reply("❌ Masukkan angka valid.")

    if state == "input_jumlah_beli":
        try:
            jumlah = int(text)
            if jumlah <= 0: return msg.reply("❌ Minimal 1 akun")
            total = jumlah * HARGA_PER_AKUN
            jumlah_beli_user[user_id] = jumlah
            pesanan_timeout[user_id] = datetime.now() + timedelta(minutes=10)
            admin_state.pop(user_id, None)
            return client.send_photo(
                user_id,
                photo="https://imgur.com/a/nYC7YL3",
                caption=f"""🔗 QRIS:

🏦 BCA:
Nama: Dimas Ramdhan S
No: 1570707520

📱 DANA:
Nama: Dimas Ramdhan S
No: 083877950760

💳 Total: Rp{total:,}
⏳ Bayar sebelum 10 menit. Kirim bukti transfer."""
            )
        except:
            return msg.reply("❌ Masukkan angka valid.")

    if state == "tambah_stok" and user_id in ADMIN_IDS:
        akun_baru = text.strip().splitlines()
        stok = get_stok()
        save_stok(stok + akun_baru)
        admin_state.pop(user_id, None)
        return msg.reply(f"✅ {len(akun_baru)} akun ditambahkan.")

    if refund_state.get(user_id) == "wait_rekening":
        for admin_id in ADMIN_IDS:
            client.send_message(
                admin_id,
                f"📥 Permintaan REFUND dari @{msg.from_user.username or user_id}:\n\n{text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Refund Sukses", callback_data=f"refund_sukses_{user_id}")]])
            )
        refund_state.pop(user_id, None)
        return msg.reply("✅ Refund dikirim ke admin. Tunggu 1x24 jam.")

@app.on_message(filters.photo & filters.private)
def handle_bukti(client, msg):
    user_id = msg.from_user.id
    jumlah = jumlah_beli_user.get(user_id)
    batas = pesanan_timeout.get(user_id)

    if not jumlah:
        return msg.reply("❌ Kamu belum melakukan pemesanan.")
    if batas and datetime.now() > batas:
        jumlah_beli_user.pop(user_id, None)
        pesanan_timeout.pop(user_id, None)
        return msg.reply("❌ Waktu pembayaran habis.")

    total = jumlah * HARGA_PER_AKUN
    for admin_id in ADMIN_IDS:
        try:
            client.send_photo(
                admin_id,
                photo=msg.photo.file_id,
                caption=f"📩 Bukti dari @{msg.from_user.username or user_id}\nJumlah: {jumlah}\nTotal: Rp{total:,}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Konfirmasi", callback_data=f"konfirmasi_{user_id}_{jumlah}"),
                     InlineKeyboardButton("❌ Tolak", callback_data=f"tolak_{user_id}")]
                ])
            )
        except: continue
    msg.reply("✅ Bukti dikirim. Tunggu konfirmasi admin.")

@app.on_callback_query()
def callback_handler(client, cb):
    user_id = cb.from_user.id
    data = cb.data

    if data.startswith("konfirmasi_") and user_id in ADMIN_IDS:
        _, uid, jumlah = data.split("_")
        uid = int(uid)
        jumlah = int(jumlah)
        stok = get_stok()
        if len(stok) < jumlah:
            client.send_message(uid, "❌ Maaf, stok tidak cukup. Silakan ulangi.")
            return cb.message.reply("❌ Stok tidak cukup.")
        akun_dikirim = stok[:jumlah]
        save_stok(stok[jumlah:])
        for idx, akun in enumerate(akun_dikirim, 1):
            log_riwayat(uid, akun)
        akun_format = "\n".join([f"{i+1}. {a}" for i, a in enumerate(akun_dikirim)])
        client.send_message(uid, f"📦 Berikut akun kamu:\n{akun_format}")
        client.send_audio(uid, NOTIF_AUDIO, caption="✅ Terima kasih, akun berhasil dikirim.")
        return cb.message.reply("✅ Akun berhasil dikirim.")

    elif data.startswith("tolak_") and user_id in ADMIN_IDS:
        uid = int(data.split("_")[1])
        client.send_message(uid, "❌ Bukti tidak valid. Silakan kirim ulang.")
        return cb.message.reply("⛔ Ditolak.")

keep_alive()
app.run()