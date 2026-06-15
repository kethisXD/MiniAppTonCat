#!/usr/bin/env python3
"""
Деплой сервиса-верификатора (verifier/) на HP-сервер как docker-контейнер.

Пакует verifier/, заливает на HP, собирает образ и поднимает контейнер
toncat-verifier рядом с toncat-frontend. Контейнер слушает 127.0.0.1:5557
и ходит к малине через туннель на 127.0.0.1:5556 (поэтому --network host).

Пароль SSH НЕ хранится в файле. Передавать через переменную окружения:
    HP_SSH_PASSWORD='...' python3 deploy_verifier_remote.py
"""
import os
import sys
import pty
import time
import select
import subprocess

REMOTE_HOST = "xxx@192.168.1.150"
PASSWORD = os.environ.get("HP_SSH_PASSWORD", "__SSH_PASSWORD__")

# --- Параметры верификатора (env контейнера) ---
RECEIVER_ADDRESS = "UQCJ0se-AJ78OGP4N7DAj_Am1PcX7wYmeXsSwIDAsC0Tl5P_"
TESTNET = "false"  # должно совпадать с config.ini (сейчас mainnet)
MIN_AMOUNT_NANOTON = "100000000"  # 0.1 TON
PI_FEED_URL = "http://127.0.0.1:5556/feed"  # бэкенд малины через SSH-туннель на HP


def run_with_password(argv, timeout=600):
    """Запускает команду под PTY, автоматически вводя SSH-пароль по запросу."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(argv[0], argv)
    out = b""
    sent = False
    start = time.time()
    while time.time() - start < timeout:
        r, _, _ = select.select([fd], [], [], 1.0)
        if not r:
            if os.waitpid(pid, os.WNOHANG) != (0, 0):
                break
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        sys.stdout.buffer.write(chunk)
        sys.stdout.flush()
        if not sent and b"password:" in out.lower():
            os.write(fd, PASSWORD.encode() + b"\n")
            sent = True
            out = b""  # не печатать дальше остатки с эхо
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        _, status = os.waitpid(pid, 0)
        return os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
    except ChildProcessError:
        return 0


def main():
    if PASSWORD == "__SSH_PASSWORD__":
        print("ВНИМАНИЕ: пароль не задан. Запусти как HP_SSH_PASSWORD='...' python3 deploy_verifier_remote.py")
        sys.exit(2)

    here = os.path.dirname(os.path.abspath(__file__))

    # 1) Пакуем verifier/ локально.
    print(">>> Пакую verifier/ ...")
    subprocess.run(
        ["tar", "czf", "/tmp/verifier.tar.gz", "-C", here, "verifier"],
        check=True,
    )

    # 2) Заливаем на HP.
    print(">>> Заливаю на HP ...")
    rc = run_with_password(
        ["scp", "-o", "StrictHostKeyChecking=no",
         "/tmp/verifier.tar.gz", f"{REMOTE_HOST}:~/verifier.tar.gz"]
    )
    if rc != 0:
        print(f"scp завершился с кодом {rc}")
        sys.exit(rc)

    # 3) Собираем образ и поднимаем контейнер.
    remote_cmd = " && ".join([
        "rm -rf ~/verifier",
        "tar xzf ~/verifier.tar.gz",
        "cd ~/verifier",
        "docker build -t toncat-verifier .",
        "docker stop toncat-verifier || true",
        "docker rm toncat-verifier || true",
        # /var/lib/toncat-verifier создаётся dockerd (root) автоматически; тот же
        # путь использует CI (.github/workflows/deploy.yml) — общая БД анти-replay.
        "docker run -d --restart unless-stopped --network host "
        "-v /var/lib/toncat-verifier:/data "
        f"-e RECEIVER_ADDRESS={RECEIVER_ADDRESS} "
        f"-e TESTNET={TESTNET} "
        f"-e MIN_AMOUNT_NANOTON={MIN_AMOUNT_NANOTON} "
        f"-e PI_FEED_URL={PI_FEED_URL} "
        "--name toncat-verifier toncat-verifier",
        "sleep 2",
        "docker ps --filter name=toncat-verifier",
        "curl -s http://127.0.0.1:5557/health || true",
    ])
    print(">>> Сборка и запуск на HP ...")
    rc = run_with_password(
        ["ssh", "-o", "StrictHostKeyChecking=no", REMOTE_HOST, remote_cmd]
    )
    print(f"\nГотово, код выхода {rc}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
