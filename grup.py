from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from datetime import datetime, timedelta

# Variabel global
status_input_grup = {}
jumlah_beli_user = {}
pesanan_timeout = {}
user_yang_order = {}

STOK_FILE = "stok_akun.txt"
HARGA_PER_AKUN = 1000
ADMIN_IDS = [6787850468, 6057026596]  # Ganti sesuai admin bot kamu

def init_grup_handlers(app):

    # /beli di grup
    @app.on_message(filters.command("beli") & filters.group)
    def start_beli_grup(client, msg):
        user_id = msg.from_user.id
        status_input_grup[user_id] = "menunggu_jumlah"
        user_yang_order[user_id] = msg.id
        msg.reply(
            "📝 Masukkan jumlah akun yang ingin kamu beli (contoh: 2)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Batalkan Pesanan", callback_data=f"batal:{user_id}")]
            ])
        )

    # Batal pesanan
    @app.on_callback_query(filters.regex(r"^batal:(\d+)$"))
    def batal_pesanan_callback(client, callback_query):
        target_user_id = int(callback_query.data.split(":")[1])
        user_id = callback_query.from_user.id

        if user_id != target_user_id:
            return callback_query.answer("❌ Kamu tidak berhak membatalkan pesanan ini.", show_alert=True)

        jumlah_beli_user.pop(user_id, None)
        pesanan_timeout.pop(user_id, None)
        status_input_grup.pop(user_id, None)
        user_yang_order.pop(user_id, None)
        callback_query.message.edit("✅ Pesanan kamu telah dibatalkan.")
        callback_query.answer("✅ Pesanan dibatalkan.")

    # Input jumlah
    @app.on_message(filters.text & filters.group)
    def proses_jumlah_beli_grup(client, msg):
        user = msg.from_user
        user_id = user.id

        if status_input_grup.get(user_id) == "menunggu_jumlah":
            try:
                jumlah = int(msg.text.strip())
            except ValueError:
                return msg.reply("❌ Masukkan angka yang valid, contoh: `2`")

            try:
                with open(STOK_FILE, "r") as f:
                    stok_list = f.read().strip().splitlines()
            except FileNotFoundError:
                return msg.reply("⚠️ Stok belum tersedia.")

            if jumlah > len(stok_list):
                return msg.reply(f"❌ Stok hanya tersedia {len(stok_list)} akun.")

            total = jumlah * HARGA_PER_AKUN
            jumlah_beli_user[user_id] = jumlah
            pesanan_timeout[user_id] = datetime.now() + timedelta(minutes=10)
            del status_input_grup[user_id]

            try:
                client.send_message(
                    user_id,
                    f"🛍️ Kamu ingin beli {jumlah} akun\n"
                    f"💳 Total: Rp{total:,}\n\n"
                    f"Silakan pilih metode pembayaran di bawah ini:",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("QRIS", callback_data="metode:qris"),
                            InlineKeyboardButton("DANA", callback_data="metode:dana"),
                            InlineKeyboardButton("BCA", callback_data="metode:bca"),
                        ]
                    ])
                )
                msg.reply(f"✅ @{user.username or user_id}, detail telah dikirim ke DM.")
            except:
                msg.reply("⚠️ Gagal kirim DM. Silakan /start bot ini dulu di chat pribadi.")

    # Pilihan metode bayar
    @app.on_callback_query(filters.regex(r"^metode:(qris|dana|bca)$"))
    def handle_metode_bayar(client, callback_query: CallbackQuery):
        metode = callback_query.data.split(":")[1]
        user = callback_query.from_user
        user_id = user.id

        if user_id not in jumlah_beli_user:
            return callback_query.answer("❌ Kamu belum melakukan pemesanan.", show_alert=True)

        if datetime.now() > pesanan_timeout.get(user_id, datetime.min):
            return callback_query.answer("⏰ Waktu habis. Order ulang ya.", show_alert=True)

        jumlah = jumlah_beli_user[user_id]
        total = jumlah * HARGA_PER_AKUN

        gambar = {
            "qris": "https://imgur.com/a/nYC7YL3",
            "dana": "dana.jpg",
            "bca": "bca.jpg"
        }.get(metode)

        keterangan = {
            "qris": "📸 Scan QRIS berikut untuk membayar.",
            "dana": "📱 Kirim ke DANA: `083879950760` (a/n Dim*s R*dha*)",
            "bca": "🏦 Transfer ke BCA: `1570707520` a/n Dim*s R*dha*"
        }.get(metode)

        client.send_photo(
            user_id,
            photo=gambar,
            caption=f"{keterangan}\n\n💳 Total: Rp{total:,}\n📩 Kirim bukti pembayaran berupa **foto** ke sini ya kak (maks 10 menit)."
        )

        callback_query.answer("✅ Silakan lanjutkan pembayaran.")

    # Kirim bukti → auto kirim akun
    @app.on_message(filters.private & filters.photo)
    def proses_bukti_bayar(client, msg: Message):
        user = msg.from_user
        user_id = user.id

        if user_id not in jumlah_beli_user:
            return msg.reply("❌ Kamu belum melakukan pemesanan.")

        if datetime.now() > pesanan_timeout.get(user_id, datetime.min):
            return msg.reply("⏰ Waktu pembayaran habis. Silakan order ulang.")

        jumlah = jumlah_beli_user[user_id]

        try:
            with open(STOK_FILE, "r") as f:
                stok_list = f.read().strip().splitlines()
        except FileNotFoundError:
            return msg.reply("⚠️ Maaf, stok kosong.")

        if jumlah > len(stok_list):
            return msg.reply("❌ Stok tidak cukup. Hubungi admin.")

        akun_terkirim = stok_list[:jumlah]
        sisa_stok = stok_list[jumlah:]

        with open(STOK_FILE, "w") as f:
            f.write("\n".join(sisa_stok))

        akun_str = "\n".join(akun_terkirim)
        msg.reply(f"✅ Berikut akun kamu:\n\n{akun_str}")

        # Notifikasi admin
        for admin_id in ADMIN_IDS:
            try:
                client.send_message(admin_id, f"📥 @{user.username or user.id} telah mengirim bukti & menerima {jumlah} akun.")
            except:
                pass

        # Bersihkan data
        jumlah_beli_user.pop(user_id, None)
        pesanan_timeout.pop(user_id, None)
        user_yang_order.pop(user_id, None)