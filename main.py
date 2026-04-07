import discord
from discord.ext import commands
from discord.ui import View
import os
import asyncio
import random
from flask import Flask
from threading import Thread

# --- 7/24 AKTİF TUTMA ---
app = Flask('')
@app.route('/')
def home(): return "TICKET SİSTEMİ AKTİF!"
def run_flask(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run_flask).start()

# --- AYARLAR ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

# KATEGORİ İSİMLERİ (Discord'da bunları birebir aynı açmalısın)
AKTIF_KATEGORI = "tickets"
LOG_KATEGORI = "tickets log"

# --- TICKET KAPATMA VE TAŞIMA BUTONU ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="archive_ticket", emoji="🔒")
    async def archive_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        
        # Hedef "tickets log" kategorisini bul
        log_category = discord.utils.get(guild.categories, name=LOG_KATEGORI)
        
        if not log_category:
            return await interaction.response.send_message(f"❌ HATA: '{LOG_KATEGORI}' kategorisi bulunamadı!", ephemeral=True)

        # Kanal ismini değiştir ve LOG kategorisine taşı
        ticket_num = random.randint(1000, 9999)
        new_name = f"closed-{ticket_num}"

        await channel.edit(
            name=new_name,
            category=log_category,
            sync_permissions=True # Log kategorisinin (yetkililere özel) izinlerini alır
        )

        await interaction.response.send_message(f"✅ Ticket kapatıldı ve {LOG_KATEGORI} kısmına taşındı.", ephemeral=True)
        
        embed = discord.Embed(
            title="🔒 Talep Arşivlendi",
            description=f"Bu bilet **{interaction.user.name}** tarafından kapatılmıştır.",
            color=discord.Color.dark_grey()
        )
        await channel.send(embed=embed)

# --- ANA TICKET AÇMA BUTONU ---
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Destek Talebi Aç", style=discord.ButtonStyle.green, custom_id="open_ticket", emoji="📩")
    async def ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        
        # Aktif "tickets" kategorisini bul
        active_category = discord.utils.get(guild.categories, name=AKTIF_KATEGORI)
        
        if not active_category:
            return await interaction.response.send_message(f"❌ HATA: '{AKTIF_KATEGORI}' kategorisi bulunamadı!", ephemeral=True)

        # Kanal izinleri
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Kanalı "tickets" kategorisi altında aç
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}", 
            overwrites=overwrites, 
            category=active_category
        )
        
        embed = discord.Embed(
            title="🎫 Destek Talebi",
            description=f"Hoş geldin {user.mention}. Yetkililer birazdan burada olacak.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Kanal oluşturuldu: {channel.mention}", ephemeral=True)

# --- KOMUT: !ticket ---
@bot.command()
@commands.has_role("bot permission")
async def ticket(ctx):
    await ctx.message.delete() # !ticket mesajını siler
    
    embed = discord.Embed(
        title="✨ Destek Sistemi",
        description="Talep oluşturmak için aşağıdaki butona tıklayın.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print(f'{bot.user.name} Giriş Yaptı! Çift kategori sistemi hazır.')

if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
