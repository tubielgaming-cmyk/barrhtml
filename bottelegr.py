# bot_admin.py
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# ============================================
# KONFIGURASI - GANTI SESUAI PUNYA KAMU
# ============================================
BOT_TOKEN = "8709660311:AAFNOzQ4gVYWNy_b92ZQmGWo_AZZhmMDttw"
ADMIN_CHAT_ID = 6073817027

# File data
DATA_FILE = "data_admin.json"

# ============================================
# FUNGSI DATABASE SEDERHANA
# ============================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "orders": [],
            "topups": [],
            "last_order_id": 0,
            "last_topup_id": 0
        }
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# ============================================
# COMMAND /START - MENU UTAMA
# ============================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Maaf, bot ini hanya untuk admin.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistik", callback_data="stats")],
        [InlineKeyboardButton("👥 Daftar User", callback_data="list_users")],
        [InlineKeyboardButton("🔄 Order Pending", callback_data="pending_orders")],
        [InlineKeyboardButton("💰 Cek Saldo User", callback_data="check_saldo")],
        [InlineKeyboardButton("📦 Topup Pending", callback_data="pending_topups")],
        [InlineKeyboardButton("📝 Cara Order", callback_data="help_order")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *BOT ADMIN SMM PANEL*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Selamat datang! Pilih menu di bawah:\n\n"
        "📊 Statistik - Lihat semua data\n"
        "👥 Daftar User - Lihat semua user\n"
        "🔄 Order Pending - Konfirmasi order\n"
        "💰 Cek Saldo - Cek saldo user\n"
        "📦 Topup Pending - Konfirmasi topup\n\n"
        "Atau ketik perintah manual:\n"
        "/stats - Statistik\n"
        "/users - Daftar user\n"
        "/pending - Order pending\n"
        "/saldo username - Cek saldo\n"
        "/topup - Topup pending",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============================================
# COMMAND /STATS - STATISTIK
# ============================================
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    data = load_data()
    users = data.get("users", {})
    orders = data.get("orders", [])
    
    total_user = len(users)
    total_saldo = sum(u.get("saldo", 0) for u in users.values())
    
    pending = len([o for o in orders if o.get("status") == "pending"])
    proses = len([o for o in orders if o.get("status") == "proses"])
    selesai = len([o for o in orders if o.get("status") == "selesai"])
    gagal = len([o for o in orders if o.get("status") == "gagal"])
    
    pesan = f"""
📊 *STATISTIK SMM PANEL*
━━━━━━━━━━━━━━━━━━━
👥 *Total User*: {total_user}
💰 *Total Saldo*: {format_rupiah(total_saldo)}

📦 *ORDER*
├─ ⏳ Pending: {pending}
├─ 🔄 Proses: {proses}
├─ ✅ Selesai: {selesai}
└─ ❌ Gagal: {gagal}

📈 *Total Order*: {len(orders)}
━━━━━━━━━━━━━━━━━━━
⏰ Update: {datetime.now().strftime('%H:%M:%S')}
    """
    
    await update.message.reply_text(pesan, parse_mode='Markdown')

# ============================================
# COMMAND /USERS - DAFTAR USER
# ============================================
async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    data = load_data()
    users = data.get("users", {})
    
    if not users:
        await update.message.reply_text("📭 Belum ada user terdaftar.")
        return
    
    pesan = "👥 *DAFTAR USER*\n━━━━━━━━━━━━━━━━━━━\n"
    for username, info in users.items():
        saldo = info.get("saldo", 0)
        wa = info.get("wa", "-")
        pesan += f"├─ @{username}\n"
        pesan += f"│  ├─ Saldo: {format_rupiah(saldo)}\n"
        pesan += f"│  └─ WA: {wa}\n"
    
    pesan += f"\n📊 Total: {len(users)} user"
    
    # Kirim per bagian jika panjang
    if len(pesan) > 4000:
        for i in range(0, len(pesan), 4000):
            await update.message.reply_text(pesan[i:i+4000], parse_mode='Markdown')
    else:
        await update.message.reply_text(pesan, parse_mode='Markdown')

# ============================================
# COMMAND /PENDING - ORDER PENDING
# ============================================
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    data = load_data()
    pending_orders = [o for o in data.get("orders", []) if o.get("status") == "pending"]
    
    if not pending_orders:
        await update.message.reply_text("✅ Tidak ada order pending.")
        return
    
    # Kirim 5 order pertama
    for order in pending_orders[:5]:
        keyboard = [
            [
                InlineKeyboardButton("🔄 Proses", callback_data=f"proses_{order['id']}"),
                InlineKeyboardButton("❌ Gagal", callback_data=f"gagal_{order['id']}")
            ],
            [
                InlineKeyboardButton("✅ Selesai", callback_data=f"selesai_{order['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        pesan = f"""
📦 *ORDER #{order['id']}*
━━━━━━━━━━━━━━━━━━━
👤 *User*: @{order.get('username', '-')}
📱 *Platform*: {order.get('platform', '-')}
📋 *Layanan*: {order.get('layanan', '-')}
📊 *Jumlah*: {order.get('jumlah', 0)}
💰 *Total*: {format_rupiah(order.get('total', 0))}
🔗 *Link*: {order.get('link', '-')}
⏰ *Waktu*: {order.get('created_at', '')[:16]}
━━━━━━━━━━━━━━━━━━━
⏳ Status: Pending
        """
        
        await update.message.reply_text(
            pesan,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    if len(pending_orders) > 5:
        await update.message.reply_text(f"📦 Masih ada {len(pending_orders) - 5} order pending lainnya.")

# ============================================
# COMMAND /SALDO username - CEK SALDO
# ============================================
async def saldo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Format:* /saldo username\n"
            "Contoh: /saldo andi_aja",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0]
    data = load_data()
    user_data = data.get("users", {}).get(username, {})
    
    if not user_data:
        await update.message.reply_text(f"❌ User @{username} tidak ditemukan.")
        return
    
    pesan = f"""
💰 *SALDO USER*
━━━━━━━━━━━━━━━━━━━
👤 *Username*: @{username}
💰 *Saldo*: {format_rupiah(user_data.get('saldo', 0))}
📱 *WA*: {user_data.get('wa', '-')}
📅 *Bergabung*: {user_data.get('joined', '-')}
━━━━━━━━━━━━━━━━━━━
    """
    
    await update.message.reply_text(pesan, parse_mode='Markdown')

# ============================================
# COMMAND /TOPUP - TOPUP PENDING
# ============================================
async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Akses ditolak.")
        return
    
    data = load_data()
    pending_topups = [t for t in data.get("topups", []) if t.get("status") == "pending"]
    
    if not pending_topups:
        await update.message.reply_text("✅ Tidak ada permintaan topup pending.")
        return
    
    for topup in pending_topups[:5]:
        keyboard = [
            [
                InlineKeyboardButton("✅ Masuk", callback_data=f"topup_masuk_{topup['id']}"),
                InlineKeyboardButton("❌ Tolak", callback_data=f"topup_tolak_{topup['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        pesan = f"""
💰 *TOPUP PENDING #{topup['id']}*
━━━━━━━━━━━━━━━━━━━
👤 *User*: @{topup.get('username', '-')}
💵 *Nominal*: {format_rupiah(topup.get('nominal', 0))}
💳 *Metode*: {topup.get('metode', '-')}
📎 *Bukti*: {topup.get('bukti', 'Tidak ada')}
⏰ *Waktu*: {topup.get('created_at', '')[:16]}
━━━━━━━━━━━━━━━━━━━
⏳ Status: Menunggu Konfirmasi
        """
        
        await update.message.reply_text(
            pesan,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    if len(pending_topups) > 5:
        await update.message.reply_text(f"📦 Masih ada {len(pending_topups) - 5} topup pending lainnya.")

# ============================================
# HANDLER TOMBOL
# ============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await query.edit_message_text("❌ Akses ditolak.")
        return
    
    data = query.data
    parts = data.split("_")
    action = parts[0]
    
    # ============================================
    # MENU UTAMA
    # ============================================
    if action == "stats":
        await stats_command(update, context)
        return
    
    elif action == "list_users":
        await users_command(update, context)
        return
    
    elif action == "pending_orders":
        await pending_command(update, context)
        return
    
    elif action == "check_saldo":
        await query.edit_message_text(
            "🔍 *Cek Saldo User*\n\n"
            "Gunakan format:\n"
            "/saldo username\n\n"
            "Contoh: /saldo andi_aja",
            parse_mode='Markdown'
        )
        return
    
    elif action == "pending_topups":
        await topup_command(update, context)
        return
    
    elif action == "help_order":
        await query.edit_message_text(
            "📝 *CARA ORDER DI SMM PANEL*\n\n"
            "1. Buka website SMM Panel\n"
            "2. Login ke akun kamu\n"
            "3. Pilih layanan yang diinginkan\n"
            "4. Masukkan link dan jumlah\n"
            "5. Klik 'Pesan Sekarang'\n\n"
            "📌 Admin akan terima notifikasi dan proses order.",
            parse_mode='Markdown'
        )
        return
    
    # ============================================
    # UPDATE ORDER
    # ============================================
    elif action in ["proses", "selesai", "gagal"]:
        order_id = int(parts[1])
        data = load_data()
        
        # Cari dan update order
        found = False
        for order in data["orders"]:
            if order["id"] == order_id:
                order["status"] = action
                order["updated_at"] = datetime.now().isoformat()
                found = True
                break
        
        if found:
            save_data(data)
            status_text = {
                "proses": "🔄 Sedang Diproses",
                "selesai": "✅ Selesai",
                "gagal": "❌ Gagal"
            }
            await query.edit_message_text(
                f"✅ Order #{order_id} berhasil diupdate ke: *{status_text.get(action, action)}*",
                parse_mode='Markdown'
            )
            
            # Notifikasi ke admin
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"✅ Order #{order_id} → {status_text.get(action, action)}"
            )
        else:
            await query.edit_message_text("❌ Gagal update order. ID tidak ditemukan.")
    
    # ============================================
    # UPDATE TOPUP
    # ============================================
    elif action == "topup_masuk":
        topup_id = int(parts[1])
        data = load_data()
        
        # Cari topup
        topup = None
        for t in data["topups"]:
            if t["id"] == topup_id:
                topup = t
                break
        
        if topup:
            topup["status"] = "masuk"
            
            # Tambah saldo user
            username = topup["username"]
            nominal = topup["nominal"]
            
            if username not in data["users"]:
                data["users"][username] = {"saldo": 0, "wa": "", "joined": datetime.now().isoformat()}
            
            data["users"][username]["saldo"] = data["users"][username].get("saldo", 0) + nominal
            
            save_data(data)
            
            await query.edit_message_text(
                f"✅ Topup #{topup_id} disetujui!\n"
                f"💰 {format_rupiah(nominal)} masuk ke @{username}\n"
                f"💳 Saldo sekarang: {format_rupiah(data['users'][username]['saldo'])}",
                parse_mode='Markdown'
            )
            
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"✅ Topup #{topup_id} → Saldo @{username} +{format_rupiah(nominal)}"
            )
        else:
            await query.edit_message_text("❌ Topup tidak ditemukan.")
    
    elif action == "topup_tolak":
        topup_id = int(parts[1])
        data = load_data()
        
        for t in data["topups"]:
            if t["id"] == topup_id:
                t["status"] = "ditolak"
                save_data(data)
                await query.edit_message_text(
                    f"❌ Topup #{topup_id} ditolak.",
                    parse_mode='Markdown'
                )
                return
        
        await query.edit_message_text("❌ Topup tidak ditemukan.")

# ============================================
# HANDLER PESAN TEKS
# ============================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Maaf, bot ini hanya untuk admin.")
        return
    
    text = update.message.text
    
    # Handle /saldo username
    if text.startswith("/saldo"):
        parts = text.split()
        if len(parts) > 1:
            context.args = parts[1:]
            await saldo_command(update, context)
        else:
            await update.message.reply_text("❌ Format: /saldo username")
        return
    
    # Handle perintah langsung
    if text == "/stats" or text == "/statistik":
        await stats_command(update, context)
    elif text == "/users" or text == "/user":
        await users_command(update, context)
    elif text == "/pending" or text == "/order":
        await pending_command(update, context)
    elif text == "/topup":
        await topup_command(update, context)
    elif text == "/start":
        await start_command(update, context)
    else:
        await update.message.reply_text(
            "❓ *Perintah tidak dikenal*\n\n"
            "Perintah yang tersedia:\n"
            "/start - Menu utama\n"
            "/stats - Statistik\n"
            "/users - Daftar user\n"
            "/pending - Order pending\n"
            "/saldo username - Cek saldo\n"
            "/topup - Topup pending",
            parse_mode='Markdown'
        )

# ============================================
# FUNGSI UNTUK DIPANGGIL DARI WEBSITE
# ============================================
def add_order_from_website(username, platform, layanan, jumlah, total, link):
    """Fungsi ini dipanggil dari website saat user order"""
    data = load_data()
    
    # Increment ID
    data["last_order_id"] = data.get("last_order_id", 0) + 1
    order_id = data["last_order_id"]
    
    order = {
        "id": order_id,
        "username": username,
        "platform": platform,
        "layanan": layanan,
        "jumlah": jumlah,
        "total": total,
        "link": link,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    data["orders"].append(order)
    save_data(data)
    
    return order_id

def add_topup_from_website(username, nominal, metode, bukti):
    """Fungsi ini dipanggil dari website saat user topup"""
    data = load_data()
    
    data["last_topup_id"] = data.get("last_topup_id", 0) + 1
    topup_id = data["last_topup_id"]
    
    topup = {
        "id": topup_id,
        "username": username,
        "nominal": nominal,
        "metode": metode,
        "bukti": bukti,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    data["topups"].append(topup)
    save_data(data)
    
    return topup_id

def get_user_saldo(username):
    """Ambil saldo user"""
    data = load_data()
    return data.get("users", {}).get(username, {}).get("saldo", 0)

# ============================================
# MAIN
# ============================================
def main():
    print("=" * 50)
    print("🤖 BOT ADMIN SMM PANEL")
    print("=" * 50)
    print(f"📱 Bot Token: {BOT_TOKEN[:15]}...")
    print(f"👑 Admin ID: {ADMIN_CHAT_ID}")
    print(f"📁 Data File: {DATA_FILE}")
    print("=" * 50)
    
    # Buat file data jika belum ada
    if not os.path.exists(DATA_FILE):
        save_data({
            "users": {},
            "orders": [],
            "topups": [],
            "last_order_id": 0,
            "last_topup_id": 0
        })
        print("✅ File data.json dibuat!")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("saldo", saldo_command))
    app.add_handler(CommandHandler("topup", topup_command))
    
    # Callback handler (tombol)
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Bot is running...")
    print("📱 Kirim /start ke bot untuk mulai")
    print("=" * 50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()