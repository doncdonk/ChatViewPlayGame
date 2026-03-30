"""
Twitch チャット接続クライアント
Python標準ライブラリのみ使用（asyncio + ssl）
Twitch IRC: irc.chat.twitch.tv:6697 (SSL)
必要な設定: チャンネル名 + OAuthトークン のみ
"""
import asyncio
import ssl
import re

OPEN_PATTERN = re.compile(r'^([A-Za-z])(\d{1,2})$')
FLAG_PATTERN = re.compile(r'^[Ff][Ll][Aa][Gg]\s+([A-Za-z])(\d{1,2})$')

HOST = "irc.chat.twitch.tv"
PORT = 6697


def parse_command(text):
    text = text.strip()
    m = FLAG_PATTERN.match(text)
    if m:
        return ord(m.group(1).upper()) - ord('A'), int(m.group(2)) - 1, True
    m = OPEN_PATTERN.match(text)
    if m:
        return ord(m.group(1).upper()) - ord('A'), int(m.group(2)) - 1, False
    return None


class TwitchClient:
    def __init__(self, channel, token, on_command, on_chat):
        self.channel    = channel.lower()
        self.token      = token if token.startswith("oauth:") else f"oauth:{token}"
        self.on_command = on_command
        self.on_chat    = on_chat
        self._writer    = None
        self._running   = True

    async def connect(self):
        ctx = ssl.create_default_context()
        retry_delay = 3

        while self._running:
            try:
                print(f"[Twitch] 接続中: {HOST}:{PORT}")
                reader, writer = await asyncio.open_connection(HOST, PORT, ssl=ctx)
                self._writer = writer

                # 認証＆チャンネル参加
                await self._send(writer, f"PASS {self.token}")
                await self._send(writer, f"NICK {self.channel}")
                await self._send(writer, f"JOIN #{self.channel}")
                print(f"[Twitch] チャンネル参加: #{self.channel}")
                retry_delay = 3  # 接続成功したらリセット

                buffer = ""
                while self._running:
                    data = await reader.read(4096)
                    if not data:
                        print("[Twitch] 接続が切れました。再接続します...")
                        break
                    buffer += data.decode("utf-8", errors="ignore")
                    while "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                        self._handle_line(line)

            except Exception as e:
                print(f"[Twitch] エラー: {e} → {retry_delay}秒後に再接続")

            if self._running:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

    async def _send(self, writer, msg):
        writer.write((msg + "\r\n").encode("utf-8"))
        await writer.drain()

    def _handle_line(self, line):
        # PING への応答（接続維持）
        if line.startswith("PING"):
            asyncio.ensure_future(self._pong(line))
            return

        # PRIVMSG パース
        # 例: :username!username@username.tmi.twitch.tv PRIVMSG #channel :message
        if "PRIVMSG" not in line:
            return

        try:
            prefix, rest = line.split(" PRIVMSG ", 1)
            username = prefix.split("!")[0].lstrip(":")
            _, message = rest.split(" :", 1)
            message = message.strip()

            result = parse_command(message)
            if result:
                col, row, is_flag = result
                self.on_command(username, col, row, is_flag)
            else:
                self.on_chat(username, message)
        except Exception:
            pass

    async def _pong(self, ping_line):
        if self._writer:
            await self._send(self._writer, ping_line.replace("PING", "PONG"))

    def stop(self):
        self._running = False
        if self._writer:
            self._writer.close()
