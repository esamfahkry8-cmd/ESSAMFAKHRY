import os
import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def get_eurusd_analysis():
    url = "https://api.binance.com/api/v3/klines?symbol=EURUSDT&interval=1m&limit=50"
    response = requests.get(url)
    
    if response.status_code != 200:
        return "❌ خطأ في جلب بيانات السوق."
        
    data = response.json()
    df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'c1', 'c2', 'c3', 'c4', 'c5'])
    df['close'] = df['close'].astype(float)
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['sma20'] = df['close'].rolling(window=20).mean()
    
    last_price = df['close'].iloc[-1]
    last_rsi = round(df['rsi'].iloc[-1], 2)
    sma = df['sma20'].iloc[-1]
    
    if last_rsi <= 30 and last_price > sma:
        signal = "🟢 **شراء (CALL)**\n⏱️ **المدة:** 1 دقيقة\n🎯 **السبب:** ارتداد من القاع + اتجاه صاعد"
    elif last_rsi >= 70 and last_price < sma:
        signal = "🔴 **بيع (PUT)**\n⏱️ **المدة:** 1 دقيقة\n🎯 **السبب:** ارتداد من القمة + اتجاه هابط"
    else:
        signal = "⚪ **انتظار**\nالسبب: السوق متذبذب والمخاطرة عالية."

    return f"📌 **تحليل EUR/USD:**\nالسعر: `{last_price}`\nRSI: `{last_rsi}`\n\n{signal}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل أمر /signal للحصول على التحليل.")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري فحص السوق...")
    res = get_eurusd_analysis()
    await update.message.reply_text(res, parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.run_polling()
