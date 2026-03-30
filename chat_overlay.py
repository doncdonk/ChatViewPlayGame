"""
弾幕風チャットオーバーレイ
コメントを画面右から左へ流す
"""
import pygame
import random
import time


# 弾幕の色プール
COLORS = [
    (255, 255, 255),
    (100, 200, 255),
    (80,  230, 160),
    (255, 220,  80),
    (255, 140, 100),
    (200, 130, 255),
    (120, 255, 220),
]


class DanmakuMessage:
    def __init__(self, username, text, screen_w, screen_h, font, y_slot):
        self.username = username
        self.text     = f"{username}: {text}"
        self.color    = random.choice(COLORS)
        self.font     = font
        self.surf     = self._render()
        self.x        = float(screen_w + 20)
        self.y        = float(y_slot)
        self.speed    = random.uniform(180, 280)  # px/sec
        self.alive    = True
        self.screen_w = screen_w

    def _render(self):
        # テキストを切り詰め
        txt = self.text[:50]
        # 縁取り用サーフェス
        surf = pygame.Surface(
            (self.font.size(txt)[0] + 4, self.font.get_height() + 4),
            pygame.SRCALPHA
        )
        # 影
        shadow = self.font.render(txt, True, (0, 0, 0))
        surf.blit(shadow, (2, 2))
        # 本文
        main = self.font.render(txt, True, self.color)
        surf.blit(main, (0, 0))
        return surf

    def update(self, dt):
        self.x -= self.speed * dt
        if self.x + self.surf.get_width() < 0:
            self.alive = False

    def draw(self, screen):
        screen.blit(self.surf, (int(self.x), int(self.y)))


class ChatOverlay:
    """弾幕管理クラス"""
    SLOT_COUNT = 14          # 縦方向のスロット数
    SLOT_HEIGHT = 34         # 1スロットの高さ

    def __init__(self, screen_w, screen_h):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.messages  = []
        self.font      = pygame.font.SysFont("monospace", 20, bold=True)
        self._slot_timer = [0.0] * self.SLOT_COUNT  # スロットの空き管理

    def add_message(self, username, text):
        """新しいコメントを追加"""
        # 空きスロットを探す
        slot = self._find_slot()
        y = 10 + slot * self.SLOT_HEIGHT
        msg = DanmakuMessage(username, text, self.screen_w, self.screen_h, self.font, y)
        self.messages.append(msg)
        # スロットをしばらくロック
        self._slot_timer[slot] = 2.5

    def _find_slot(self):
        # 最もタイマーが小さいスロットを選ぶ
        return min(range(self.SLOT_COUNT), key=lambda i: self._slot_timer[i])

    def update(self, dt):
        self.messages = [m for m in self.messages if m.alive]
        for m in self.messages:
            m.update(dt)
        for i in range(self.SLOT_COUNT):
            self._slot_timer[i] = max(0.0, self._slot_timer[i] - dt)

    def draw(self, screen):
        for m in self.messages:
            m.draw(screen)
