import discord
from discord.ext import commands
from discord.ui import View
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "707 Sıralı Ticket Aktif!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

AKTIF_KATEGORI = "tickets"
LOG_KATEGORI = "tickets log"

# --- TICKET KAPATMA BUTONU (SIRALI ARŞİV) ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="archive_btn", emoji="🔒")
    async def archive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        log_cat = discord.utils.get(guild.categories, name=LOG_KATEGORI)
        
        if not log_cat:
            return await interaction.response.send_message(f"❌ '{LOG_KATEGORI}' kategorisi bulunamadı!", ephemeral=True)

        # Log kategorisindeki kanal sayısını bul ve 1 ekle
        ticket_count = len(log_cat.channels) + 1
        new_name = f"closed-{ticket_count}"
        
        # Kanalı taşı ve ismini değiştir
        await interaction.channel.edit(name=new_name, category=log_cat, sync_permissions=True)
        await interaction.response.send_message(f"✅ Ticket arşivlendi: `{new_name}`", ephemeral=True)
        
        embed = discord.Embed(
            title="🔒 Ticket Arşivlendi",
            description=f"**Sıra No:** {ticket_count}\n**Kapatan:** {interaction.user.mention}",
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

        # Aynı isimde kanal varsa açma (Spam engelleme)
        clean_name = f"ticket-{user.name.lower()}".replace(" ", "-")
        existing = discord.utils.get(guild.channels, name=clean_name)
        if existing:
            return await interaction.response.send_message("⚠️ Zaten açık bir biletin var!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=active_cat)
        
        embed = discord.Embed(title="🎫 Destek Talebi", description=f"Hoş geldin {user.mention}. Sorununu yazabilirsin.", color=discord.Color.blue())
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Kanal açıldı: {channel.mention}", ephemeral=True)

@bot.command()
@commands.has_role("bot permission")
async def ticket(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="✨ Sunucu Destek", description="Talep oluşturmak için butona basın.", color=discord.Color.green())
    await ctx.send(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    if not hasattr(bot, 'view_set'):
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())
        bot.view_set = True
    print(f'{bot.user.name} Sıralı Sistem Hazır!')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
