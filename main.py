import discord
from discord.ext import commands
from discord.ui import View
import os
import json
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Ticket V4 Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

AKTIF_KATEGORI = "tickets"
LOG_KATEGORI = "tickets log"
DATA_FILE = "ticket_data.json"

# --- VERİ YÖNETİMİ (Sıra Numarası İçin) ---
def get_next_number():
    if not os.path.exists(DATA_FILE):
        data = {"last_number": 0}
    else:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    
    data["last_number"] += 1
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)
    return data["last_number"]

# --- TICKET KAPATMA BUTONU ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="archive_btn", emoji="🔒")
    async def archive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        log_cat = discord.utils.get(guild.categories, name=LOG_KATEGORI)
        
        if not log_cat:
            return await interaction.response.send_message(f"❌ '{LOG_KATEGORI}' kategorisi bulunamadı!", ephemeral=True)

        # Sıradaki numarayı al ve ismi değiştir
        num = get_next_number()
        new_name = f"closed-{num}"
        
        await interaction.channel.edit(name=new_name, category=log_cat, sync_permissions=True)
        await interaction.response.send_message(f"✅ Ticket arşivlendi: `{new_name}`", ephemeral=True)
        
        embed = discord.Embed(
            title="🔒 Ticket Arşivlendi",
            description=f"**Sıra No:** {num}\n**Kapatan:** {interaction.user.mention}",
            color=discord.Color.dark_grey()
        )
        await interaction.channel.send(embed=embed)

# --- ANA TICKET AÇMA BUTONU ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Aç", style=discord.ButtonStyle.green, custom_id="open_btn", emoji="📩")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        active_cat = discord.utils.get(guild.categories, name=AKTIF_KATEGORI)
        
        if not active_cat:
            return await interaction.response.send_message(f"❌ '{AKTIF_KATEGORI}' kategorisi yok!", ephemeral=True)

        # KRİTİK KONTROL: Aktif kategoride bu kullanıcının kanalı var mı?
        # Kullanıcının adını içeren kanalları tickets kategorisinde ara
        has_active = False
        for channel in active_cat.channels:
            if user.name.lower() in channel.name.lower():
                has_active = True
                break
        
        if has_active:
            return await interaction.response.send_message("⚠️ Mevcut biletin kapanmadan yenisini açamazsın!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=active_cat)
        
        embed = discord.Embed(title="🎫 Destek", description=f"Selam {user.mention}, sorunun nedir?", color=discord.Color.blue())
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Kanal açıldı: {channel.mention}", ephemeral=True)

@bot.command()
@commands.has_role("bot permission")
async def ticket(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="✨ Destek", description="Butona tıkla!", color=discord.Color.green())
    await ctx.send(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    if not hasattr(bot, 'view_set'):
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())
        bot.view_set = True
    print(f'{bot.user.name} Hazır! Sıra ve Tekil Kontrol Aktif.')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
