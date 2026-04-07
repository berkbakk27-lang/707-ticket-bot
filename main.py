import discord
from discord.ext import commands
import os
import json
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Ticket V6 ID-LOCK Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

AKTIF_KATEGORI = "tickets"
LOG_KATEGORI = "tickets log"
DATA_FILE = "ticket_data.json"

# --- SIRALAMA SİSTEMİ (KALICI) ---
def get_next_number():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {"last_number": 0}
        
        data["last_number"] += 1
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        return data["last_number"]
    except:
        return 1

# --- ETKİLEŞİM DİNLEYİCİ ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id")
    guild = interaction.guild
    user = interaction.user

    # --- TICKET AÇMA ---
    if custom_id == "open_ticket":
        active_cat = discord.utils.get(guild.categories, name=AKTIF_KATEGORI)
        if not active_cat:
            return await interaction.response.send_message(f"❌ '{AKTIF_KATEGORI}' kategorisi yok!", ephemeral=True)

        # 🚨 ID TABANLI KONTROL (En Garanti Yöntem)
        # Aktif kategorideki kanalların açıklama (topic) kısmına bakıyoruz
        for channel in active_cat.text_channels:
            if channel.topic == str(user.id):
                return await interaction.response.send_message("⚠️ Zaten aktif bir biletin var! Onu kapatmadan yenisini açamazsın.", ephemeral=True)

        # KANAL OLUŞTURMA
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Kanalın 'topic' kısmına kullanıcının ID'sini gömüyoruz
        new_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=active_cat,
            topic=str(user.id) 
        )

        embed = discord.Embed(title="🎫 Destek Talebi", description=f"Selam {user.mention}, talebin oluşturuldu. Kapatmak için aşağıdaki butona basabilirsin.", color=0x3498db)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒"))
        
        await new_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Kanalın açıldı: {new_channel.mention}", ephemeral=True)

    # --- TICKET KAPATMA ---
    elif custom_id == "close_ticket":
        log_cat = discord.utils.get(guild.categories, name=LOG_KATEGORI)
        if not log_cat:
            return await interaction.response.send_message(f"❌ '{LOG_KATEGORI}' kategorisi bulunamadı!", ephemeral=True)

        num = get_next_number()
        new_name = f"closed-{num}"
        
        # Kapatırken ID kilidini kaldır (topic'i temizle) ve taşı
        await interaction.channel.edit(name=new_name, category=log_cat, sync_permissions=True, topic=None)
        await interaction.response.send_message(f"✅ Ticket arşivlendi: `{new_name}`", ephemeral=True)
        
        log_embed = discord.Embed(title="🔒 Arşivlendi", description=f"**Sıra:** {num}\n**Kapatan:** {user.mention}", color=0x7f8c8d)
        await interaction.channel.send(embed=log_embed)

# --- !TICKET KOMUTU ---
@bot.command()
@commands.has_role("bot permission")
async def ticket(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="✨ 707 Destek Sistemi", description="Aşağıdaki butona basarak bilet açabilirsiniz.", color=0x2ecc71)
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Destek Talebi Aç", style=discord.ButtonStyle.green, custom_id="open_ticket", emoji="📩"))
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'{bot.user.name} | V6 ID-LOCK & SIRALAMA AKTİF!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
