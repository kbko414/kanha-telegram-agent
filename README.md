# Kanha Telegram Agent - မြန်မာဘာသာ လမ်းညွှန်

Uncensored AI agent - Telegram bot အနေနဲ့။ Tools: shell, file, web. Memory ပါ။ Owner-only.

## အမြန်တပ်ဆင်နည်း (one-command)

```bash
curl -fsSL https://raw.githubusercontent.com/kbko414/kanha-telegram-agent/main/setup_tgagent.sh | sudo bash
```

Installer က Python, Ollama, model (dolphin-mistral), .env, systemd service အကုန်လုပ်ပေးတယ်။ ပြီးရင် Telegram မှာ bot ကို /start ပို့ရုံပဲ။ အသေးစိတ်က အောက်မှာ ရှိတယ်။

## ၁။ တပ်ဆင်ခြင်း

```bash
# Ubuntu 22.04/24.04
apt update && apt install -y python3.11 python3.11-venv python3-pip curl

cd /opt/tgagent
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

၂။ Model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull dolphin-mistral
systemctl enable --now ollama
```

၃။ Config

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

· TG_TOKEN - @BotFather ကနေ ယူ
· OWNER_ID - @userinfobot ကနေ ယူ
· MODEL - dolphin-mistral:latest

၄။ Run

```bash
python bot.py
```

Telegram မှာ bot ကို ရှာပြီး /start ပို့။

၅။ systemd (အမြဲ run)

```bash
cat > /etc/systemd/system/tgagent.service <<EOF
[Unit]
Description=Kanha Telegram Agent
After=network-online.target ollama.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tgagent
EnvironmentFile=/opt/tgagent/.env
ExecStart=/opt/tgagent/venv/bin/python /opt/tgagent/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now tgagent
journalctl -u tgagent -f
```

Commands

Command အလုပ်
/start စတင်
/reset Memory ဖျက်
/memory မှတ်ထားတာ ကြည့်
/temp 1.2 Temperature ပြောင်း
/ping ရှိလား စစ်

သတိထားရန်

· Shell က root - User=tgagent ပြောင်းပြီး chown -R tgagent /opt/tgagent လုပ်ပါ
· Prompt injection - web_fetch မလိုရင် tools.py ကနေ ဖြုတ်ပါ
· Context window - 16384 tokens ထည့်ထားပြီး (agent.py)
