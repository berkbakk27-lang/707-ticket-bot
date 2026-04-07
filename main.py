import discord
from discord.ext import commands
import os
import json
import random
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Ticket V5 STABİL!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

AKTIF_KATEGORI = "tickets"
LOG_KATEGORI = "tickets log"
DATA_FILE = "ticket_data.json"

# --- SIRALAMA SİSTEMİ ---
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
        return random.randint(100, 999) # Hata olursa rastgele atmasın diye yedek

# --- ETKİLEŞİM DİNLEYİCİ (ÇİFT AÇILMAYI ÖNLEYEN ANA YAPI) ---
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id")
    guild = interaction.guild
    user = interaction.user

    # --- TICKET AÇMA İŞLEMİ ---
    if custom_id == "open_ticket":
        active_cat = discord.utils.get(guild.categories, name=AKTIF_KATEGORI)
        if not active_cat:
            return await interaction.response.send_message(f"❌ '{AKTIF_KATEGORI}' kategorisi yok!", ephemeral=True)

        # KONTROL: Kullanıcının zaten açık ticketı var mı?
        # (Kanal isminde kullanıcı adını arıyoruz)
        for channel in active_cat.channels:
            if user.name.lower() in channel.name.lower():
                return await interaction.response.send_message("⚠️ Zaten bir biletin açık! Onu kapatmadan yenisini açamazsın.", ephemeral=True)

        # KANAL OLUŞTURMA
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        new_channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            overwrites=overwrites,
            category=active_cat
        )

        # Kanal içi mesaj ve KAPAT butonu
        embed = discord.Embed(title="🎫 Destek Talebi", description=f"Selam {user.mention}, yetkililer gelene kadar sorununu yazabilirsin.", color=0x3498db)
        
        # KAPAT BUTONU TANIMLAMA
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒"))
        
        await new_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Kanalın açıldı: {new_channel.mention}", ephemeral=True)

    # --- TICKET KAPATMA İŞLEMİ ---
    elif custom_id == "close_ticket":
        log_cat = discord.utils.get(guild.categories, name=LOG_KATEGORI)
        if not log_cat:
            return await interaction.response.send_message(f"❌ '{LOG_KATEGORI}' kategorisi yok!", ephemeral=True)

        # Sıra numarasını al ve taşı
        num = get_next_number()
        new_name = f"closed-{num}"
        
        await interaction.channel.edit(name=new_name, category=log_cat, sync_permissions=True)
        await interaction.response.send_message(f"✅ Ticket arşivlendi: `{new_name}`", ephemeral=True)
        
        log_embed = discord.Embed(title="🔒 Arşivlendi", description=f"**Sıra:** {num}\n**Kapatan:** {user.mention}", color=0x7f8c8d)
        await interaction.channel.send(embed=log_embed)

# --- !TICKET KOMUTU ---
@bot.command()
@commands.has_role("bot permission")
async def ticket(ctx):
    await ctx.message.delete()
    
    embed = discord.Embed(title="✨ 707 Destek Sistemi", description="Aşağıdaki butona basarak yeni bir destek talebi oluşturabilirsiniz.", color=0x2ecc71)
    
    view = discord.ui.View(timeout=None)
    view.add_item(discord.ui.Button(label="Destek Talebi Aç", style=discord.ButtonStyle.green, custom_id="open_ticket", emoji="📩"))
    
    await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'{bot.user.name} | V5 Stabil Sürüm Aktif!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
