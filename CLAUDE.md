# MiniAppTonCat — криптокормушка для котов

Дипломный проект. Telegram Mini App + железо: донат в TON запускает мотор, который
кормит кота, плюс live-видео с камеры.

---

## Что это и как работает

**Идея:** пользователь открывает Mini App (в Telegram или браузере) → видит поток с
камеры → донатит 0.1 TON через TON Connect → бэкенд крутит серво-мотор → кот накормлен.

**Железо (на кормушке):** Raspberry Pi Zero 2 W
- Камера (поток через go2rtc)
- Светодиод — GPIO BCM 26 (`LIGHT_PIN`)
- Серво-мотор — GPIO BCM 18 / физ. pin 12, 50 Гц PWM (`MOTOR_PIN`)
- Датчик тока INA219 (напряжение батареи через `/status`)
- ~~USB-модем Huawei E3372~~ — **выведен из эксплуатации** (см. «Сеть»)

**Компоненты репозитория:**
| Путь | Что это |
|------|---------|
| `rpi_server.py` | **Реальный бэкенд**, крутится на Pi. FastAPI :8000. Эндпоинты: `/status`, `/light/{on\|off}`, `/motor/{left\|right}`, `/feed` |
| `verifier/` | **Верификатор оплаты** (FastAPI, docker `toncat-verifier` на HP). `/verify {nonce}` проверяет платёж в TON перед кормлением |
| `.github/workflows/deploy.yml` | **CI/CD:** push в main → self-hosted runner на HP пересобирает контейнеры frontend+verifier |
| `main.py` | Мёртвый FastAPI-скелет (только `/health`). По сути не используется |
| `config.ini` | `feed_duration`, `motor_duration`, `testnet` |
| `frontend/` | React + Vite, TON Connect. `App.jsx` — рабочий, `App.tsx` — старый вариант |
| `frontend/src/components/DonationButton.jsx` | Донат → `sendTransaction` → `POST /feed` |
| `android_client/` | Kotlin WebView-обёртка вокруг фронта (незакоммичена, недоделана) |
| `*.py` (~30 шт: `check_*`, `deploy_*`, `diagnose_*`…) | Одноразовые ssh-скрипты. **Мусор, на снос** |

---

## Сеть и подключение

### Текущая схема (после 2026-06)
Pi выходит в интернет через **Wi-Fi**, основной канал — **телефонный хотспот**.
Доступ к Pi — **через Tailscale** (Pi за CGNAT, прямого inbound нет).

- **Tailscale IP Pi:** `100.71.244.91` (hostname `raspberrypi`)
- **SSH:** порт `6969`, пользователь `xxx`
- **Wi-Fi профили (NetworkManager):**
  - `nothing-hotspot` — телефонный хотспот, SSID `nothing`, приоритет **10** (основной)
  - `preconfigured` — домашний Wi-Fi (`192.168.1.x`), приоритет **0** (страховка)
- Pi Zero видит только **2.4 ГГц** — хотспот телефона держать в 2.4 ГГц.
- `dtoverlay=disable-wifi` в `/boot/firmware/config.txt` **закомментирован** (бэкап рядом).

### Как мне (Claude) подключиться к Pi
`sshpass` обычно нет, пароль интерактивный. Рабочий приём — PTY-хелпер
(шаблон есть в `run_remote.py`/`deploy_server.py`). Минимальная версия:

```python
# /tmp/ssh_pi.py — пересоздать при необходимости
import pty, os, select, sys, time
HOST, PORT, PW = "xxx@100.71.244.91", "6969", b"<PASSWORD>\n"
def run(cmd, timeout=40):
    pid, fd = pty.fork()
    if pid == 0: os.execvp("ssh", ["ssh","-p",PORT,"-o","StrictHostKeyChecking=no",
                                   "-o","ConnectTimeout=15",HOST,cmd])
    out=b""; sent=False; t=time.time()
    while time.time()-t < timeout:
        r,_,_ = select.select([fd],[],[],2.0)
        if not r:
            if os.waitpid(pid,os.WNOHANG)!=(0,0): break
            continue
        try:
            c=os.read(fd,4096)
            if not c: break
            out+=c
            if not sent and b"password:" in out.lower(): os.write(fd,PW); sent=True
        except OSError: break
    return out.decode(errors="ignore")
if __name__=="__main__": print(run(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 40))
```
Пароль НЕ хранить здесь в открытом виде — он лежит (увы) в существующих скриптах
репозитория; взять оттуда. См. «Известные проблемы».

### Видеопоток (go2rtc) — почему было два
Из-за CGNAT раньше: **go2rtc #1 на Pi** (RTSP :8554) → SSH reverse-tunnel → **go2rtc #2
на HP-сервере** (`192.168.1.150`) релеил в MSE :1984 → фронт брал поток с HP.
Релей нужен только публичным зрителям (Telegram Mini App). Для зрителя в Tailscale
можно брать поток напрямую с Pi и второй go2rtc/HP не поднимать.

---

## Запуск (dev)
```bash
# фронтенд
cd frontend && npm install && npm run dev    # Vite :5173

# бэкенд — на самом Pi
python3 rpi_server.py                          # FastAPI :8000
```
`frontend/src/App.jsx` сам выбирает API/stream URL: localhost → прямые IP,
в Telegram → относительные пути через прокси.

---

## CI/CD (self-hosted)
Push в `main` (изменения в `frontend/**` или `verifier/**`) → GitHub Actions запускает
workflow `.github/workflows/deploy.yml` на **self-hosted runner на HP**
(`services.github-runners.miniapptoncat` в `/etc/nixos/github-runner.nix`, токен в
`/var/keys/github/miniapptoncat`, состоит в группе `docker`). Runner локально пересобирает
и перезапускает контейнеры `toncat-frontend` (:3005) и `toncat-verifier` (:5557). Триггер
ТОЛЬКО push (не PR — репо публичный, защита от RCE из форков). Caddy/NixOS и малина — вручную.

---

## Известные проблемы / бэклог
1. **🔴 Утечка секретов:** пароль `__SSH_PASSWORD__` в plaintext в ~15 файлах, `StrictHostKeyChecking=no`
   везде. Сменить пароль, перейти на SSH-ключи, вычистить файлы и историю git. **До любого push.**
2. **✅ Донат верифицируется on-chain (СДЕЛАНО 2026-06-15):** сервис `verifier/` (docker
   `toncat-verifier` на HP, `--network host`, 127.0.0.1:5557) проверяет платёж по nonce через
   toncenter (testnet), анти-replay по хешу tx в SQLite, дёргает /feed малины через туннель
   127.0.0.1:5556. Фронт кладёт nonce текст-комментарием в tx и поллит `/verify`. Caddy:
   `/verify/*→5557`, прямой `/pi/feed→403`. Деплой: `deploy_verifier_remote.py` или CI (см. ниже).
3. **🟠 ~30 одноразовых ssh-скриптов** — снести, оставить нормальный деплой.
4. **🟠 Нет автозапуска** — поднять systemd-юниты (go2rtc, rpi_server) с `Restart=always`,
   `enable` на загрузку.
5. **🟠 Батарея ~3ч** — стрим on-demand вместо 24/7, ниже разрешение/fps.
6. `main.py` мёртвый; `android_client/` недоделан (захардкожен dev-URL, нет ресурсов/иконок).

## История железных проблем (решено)
- USB-модем Huawei E3372 ресетился по USB от просадки питания (пики ~2A при регистрации
  в LTE) → `eth0` отваливался → Tailscale флапал. **Решение:** включили встроенный Wi-Fi,
  перешли на телефонный хотспот; модем больше не нужен.

> Подробный контекст и решения также в персональной памяти проекта
> (`memory/` — project-overview, architecture-state, security-leaked-password).
