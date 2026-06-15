"""
toncat-verifier — привратник оплаты для криптокормушки.

Проверяет, что на адрес-получатель реально пришёл платёж >= MIN_AMOUNT TON
с уникальным текстовым comment (nonce), который фронт положил в транзакцию.
Только после этого дёргает /feed малины (через SSH-туннель на 127.0.0.1:5556).

Анти-replay: ключ = хеш транзакции (in_msg уникален в блокчейне), хранится в SQLite.
Один реальный платёж = одно кормление; повторный /verify по тому же платежу отклоняется.
Малину (rpi_server.py) не трогаем — она остаётся «тупым» исполнителем за туннелем.
"""
import os
import re
import time
import sqlite3
import threading
import contextlib

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Конфиг через env (значения задаются в docker run) ---
RECEIVER_ADDRESS = os.environ.get(
    "RECEIVER_ADDRESS", "UQCJ0se-AJ78OGP4N7DAj_Am1PcX7wYmeXsSwIDAsC0Tl5P_"
)
MIN_AMOUNT_NANOTON = int(os.environ.get("MIN_AMOUNT_NANOTON", "100000000"))  # 0.1 TON
TESTNET = os.environ.get("TESTNET", "true").lower() in ("1", "true", "yes")
TONCENTER_API_KEY = os.environ.get("TONCENTER_API_KEY", "").strip()
PI_FEED_URL = os.environ.get("PI_FEED_URL", "http://127.0.0.1:5556/feed")
DB_PATH = os.environ.get("DB_PATH", "/data/used.db")
# Принимаем только свежие платежи — отсекает переигрывание старья после рестарта.
MAX_AGE_SECONDS = int(os.environ.get("MAX_AGE_SECONDS", "3600"))  # 1 час (запас на загрузку кормушки)
# Задержка перед запуском мотора: фронт успевает показать и закрыть модалку успеха,
# чтобы кормление было видно на чистом стриме (модалка его не перекрывала).
FEED_DELAY = float(os.environ.get("FEED_DELAY", "5"))

TONCENTER_BASE = (
    "https://testnet.toncenter.com/api/v2"
    if TESTNET
    else "https://toncenter.com/api/v2"
)

NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{4,64}$")

app = FastAPI(title="toncat-verifier")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Хранилище использованных транзакций (анти-replay) ---
def _db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS used_tx ("
        "tx_key TEXT PRIMARY KEY, nonce TEXT, ts INTEGER)"
    )
    return conn


def _mark_used(tx_key: str, nonce: str) -> bool:
    """Атомарно помечает транзакцию использованной (claim). False, если уже была."""
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO used_tx (tx_key, nonce, ts) VALUES (?, ?, ?)",
            (tx_key, nonce, int(time.time())),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def _unmark_used(tx_key: str):
    """Снимает claim — чтобы платёж можно было повторить, если кормление не удалось."""
    conn = _db()
    try:
        conn.execute("DELETE FROM used_tx WHERE tx_key = ?", (tx_key,))
        conn.commit()
    finally:
        conn.close()


class VerifyRequest(BaseModel):
    nonce: str


@app.get("/health")
def health():
    return {"ok": True, "testnet": TESTNET, "receiver": RECEIVER_ADDRESS}


def _fetch_transactions():
    params = {"address": RECEIVER_ADDRESS, "limit": 30, "archival": "true"}
    headers = {"X-API-Key": TONCENTER_API_KEY} if TONCENTER_API_KEY else {}
    with httpx.Client(timeout=15.0) as client:
        r = client.get(
            f"{TONCENTER_BASE}/getTransactions", params=params, headers=headers
        )
        r.raise_for_status()
        data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"toncenter error: {data}")
    return data.get("result", [])


def _find_payment(txs, nonce: str):
    """Ищет входящий платёж с comment == nonce и суммой >= минимума. Возвращает (tx_key, tx) или None."""
    now = time.time()
    for tx in txs:
        in_msg = tx.get("in_msg") or {}
        comment = (in_msg.get("message") or "").strip()
        if comment != nonce:
            continue
        try:
            value = int(in_msg.get("value", "0"))
        except (TypeError, ValueError):
            continue
        if value < MIN_AMOUNT_NANOTON:
            continue
        if MAX_AGE_SECONDS and (now - tx.get("utime", 0)) > MAX_AGE_SECONDS:
            continue
        tid = tx.get("transaction_id", {})
        tx_key = f"{tid.get('lt')}:{tid.get('hash')}"
        return tx_key, tx
    return None


def _trigger_feed():
    with httpx.Client(timeout=15.0) as client:
        r = client.post(PI_FEED_URL)
        r.raise_for_status()
        return r.json()


def _delayed_feed(tx_key: str, nonce: str):
    """Ждёт FEED_DELAY, затем крутит мотор. Если кормушка офлайн — снимает claim."""
    time.sleep(FEED_DELAY)
    try:
        _trigger_feed()
        print(f"[verify] FED (after {FEED_DELAY}s) nonce={nonce} tx={tx_key}")
    except Exception as e:
        print(f"[verify] delayed feed failed, releasing claim: {e}")
        _unmark_used(tx_key)


@app.post("/verify")
def verify(req: VerifyRequest):
    nonce = (req.nonce or "").strip()
    if not NONCE_RE.match(nonce):
        return {"status": "error", "reason": "bad_nonce"}

    try:
        txs = _fetch_transactions()
    except Exception as e:  # сеть/индексатор недоступны — пусть фронт ретраит
        print(f"[verify] toncenter fail: {e}")
        return {"status": "pending", "reason": "indexer_unavailable"}

    found = _find_payment(txs, nonce)
    if not found:
        # Платёж ещё не проиндексирован (лаг) либо его нет — фронт ретраит.
        return {"status": "pending"}

    tx_key, tx = found
    if not _mark_used(tx_key, nonce):
        # Этот платёж уже отработан раньше — анти-replay.
        return {"status": "already_used"}

    # Платёж подтверждён. Кормим в фоне с задержкой, а фронту сразу отвечаем "fed":
    # модалка успеха показывается и закрывается, а мотор срабатывает уже на чистом
    # стриме (через FEED_DELAY секунд). Если кормушка офлайн — claim снимется в фоне.
    threading.Thread(target=_delayed_feed, args=(tx_key, nonce), daemon=True).start()
    print(f"[verify] CONFIRMED nonce={nonce} tx={tx_key}, feed in {FEED_DELAY}s")
    return {"status": "fed", "tx": tx_key, "feed_delay": FEED_DELAY}
