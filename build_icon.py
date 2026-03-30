"""
ChatViewPlayGame アイコン生成スクリプト
実行: python build_icon.py
生成物: icon.ico (256x256 ~ 16x16 マルチサイズ)
依存: pip install pillow
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os

# ── カラー定義 ──────────────────────────────
BG_COLOR      = (13,  15,  26,  255)   # #0D0F1A 濃紺
ACCENT        = (100, 180, 255, 255)   # #64B4FF 青
SAFE          = (80,  220, 160, 255)   # #50DCA0 緑
CONTROLLER    = (220, 225, 255, 255)   # コントローラー本体（明るめグレー白）
CTRL_DARK     = (140, 150, 200, 255)   # コントローラー影
HUMAN_COLOR   = (100, 180, 255, 255)   # 人型シルエット
BUBBLE_BG     = (30,  36,  60,  220)   # 吹き出し背景
BUBBLE_TEXT   = (80,  220, 160, 255)   # 吹き出し文字


def draw_icon(size: int) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s    = size
    cx   = s // 2

    # ── 背景：角丸矩形 ──────────────────────
    radius = s // 5
    draw.rounded_rectangle([0, 0, s-1, s-1], radius=radius, fill=BG_COLOR)

    # ── グロー（うっすら円形グラデーション風） ──
    for i in range(6, 0, -1):
        r_glow = int(s * 0.38 * i / 6)
        alpha  = int(18 * (7 - i))
        glow   = (*ACCENT[:3], alpha)
        draw.ellipse(
            [cx - r_glow, s//2 - r_glow, cx + r_glow, s//2 + r_glow],
            fill=glow
        )

    # ── 人型シルエット ──────────────────────
    # 頭（円）
    head_r = int(s * 0.10)
    head_cx = int(s * 0.36)
    head_cy = int(s * 0.26)
    draw.ellipse(
        [head_cx - head_r, head_cy - head_r,
         head_cx + head_r, head_cy + head_r],
        fill=HUMAN_COLOR
    )
    # 胴体
    body_top    = head_cy + head_r
    body_bottom = int(s * 0.56)
    body_w      = int(s * 0.13)
    draw.rounded_rectangle(
        [head_cx - body_w, body_top,
         head_cx + body_w, body_bottom],
        radius=int(s * 0.04),
        fill=HUMAN_COLOR
    )
    # 腕（左）
    arm_w = int(s * 0.06)
    draw.rounded_rectangle(
        [head_cx - body_w - arm_w*2, body_top + int(s*0.02),
         head_cx - body_w,           body_top + int(s*0.20)],
        radius=int(s*0.03),
        fill=HUMAN_COLOR
    )
    # 腕（右）
    draw.rounded_rectangle(
        [head_cx + body_w,           body_top + int(s*0.02),
         head_cx + body_w + arm_w*2, body_top + int(s*0.20)],
        radius=int(s*0.03),
        fill=HUMAN_COLOR
    )
    # 脚（左）
    leg_w = int(s * 0.07)
    draw.rounded_rectangle(
        [head_cx - body_w,            body_bottom,
         head_cx - body_w + leg_w,    body_bottom + int(s*0.20)],
        radius=int(s*0.03),
        fill=HUMAN_COLOR
    )
    # 脚（右）
    draw.rounded_rectangle(
        [head_cx + body_w - leg_w,    body_bottom,
         head_cx + body_w,            body_bottom + int(s*0.20)],
        radius=int(s*0.03),
        fill=HUMAN_COLOR
    )

    # ── ゲームコントローラー ────────────────
    ctrl_x1 = int(s * 0.40)
    ctrl_x2 = int(s * 0.92)
    ctrl_y1 = int(s * 0.46)
    ctrl_y2 = int(s * 0.72)
    ctrl_r  = int(s * 0.08)
    # 本体
    draw.rounded_rectangle(
        [ctrl_x1, ctrl_y1, ctrl_x2, ctrl_y2],
        radius=ctrl_r,
        fill=CONTROLLER
    )
    # 側面影
    draw.rounded_rectangle(
        [ctrl_x1, ctrl_y1 + int(s*0.04),
         ctrl_x2, ctrl_y2],
        radius=ctrl_r,
        fill=CTRL_DARK
    )
    draw.rounded_rectangle(
        [ctrl_x1 + int(s*0.01), ctrl_y1,
         ctrl_x2 - int(s*0.01), ctrl_y2 - int(s*0.03)],
        radius=ctrl_r,
        fill=CONTROLLER
    )

    # 十字キー（左側）
    dpad_cx = int(s * 0.54)
    dpad_cy = int(s * 0.59)
    dw      = int(s * 0.05)
    dh      = int(s * 0.035)
    draw.rectangle(
        [dpad_cx - dw, dpad_cy - dh, dpad_cx + dw, dpad_cy + dh],
        fill=BG_COLOR
    )
    draw.rectangle(
        [dpad_cx - dh, dpad_cy - dw, dpad_cx + dh, dpad_cy + dw],
        fill=BG_COLOR
    )

    # ボタン（右側・4つ）
    btn_cx  = int(s * 0.79)
    btn_cy  = int(s * 0.59)
    btn_r   = int(s * 0.028)
    btn_off = int(s * 0.068)
    btn_colors = [
        (255, 80,  80,  255),   # ×赤（上）
        (80,  220, 160, 255),   # ○緑（右）
        (100, 180, 255, 255),   # □青（下）
        (255, 200, 50,  255),   # △黄（左）
    ]
    positions = [
        (btn_cx,         btn_cy - btn_off),
        (btn_cx + btn_off, btn_cy),
        (btn_cx,         btn_cy + btn_off),
        (btn_cx - btn_off, btn_cy),
    ]
    for pos, col in zip(positions, btn_colors):
        draw.ellipse(
            [pos[0]-btn_r, pos[1]-btn_r, pos[0]+btn_r, pos[1]+btn_r],
            fill=col
        )

    # スタート・セレクトボタン（中央小）
    for ox in [-int(s*0.03), int(s*0.03)]:
        mid_cx = int((ctrl_x1 + ctrl_x2) / 2) + ox
        mid_cy = ctrl_y1 + int(s * 0.08)
        sr = int(s * 0.018)
        draw.ellipse(
            [mid_cx-sr, mid_cy-sr, mid_cx+sr, mid_cy+sr],
            fill=CTRL_DARK
        )

    # ── チャット吹き出し（右上）──────────────
    if size >= 48:
        bx1 = int(s * 0.62)
        by1 = int(s * 0.06)
        bx2 = int(s * 0.94)
        by2 = int(s * 0.36)
        br  = int(s * 0.06)
        # 吹き出し本体
        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=br,
            fill=BUBBLE_BG,
            outline=ACCENT[:3] + (180,),
            width=max(1, int(s * 0.015))
        )
        # 吹き出し尾（三角）
        tail_pts = [
            (bx1 + int(s*0.06), by2),
            (bx1 + int(s*0.02), by2 + int(s*0.07)),
            (bx1 + int(s*0.14), by2),
        ]
        draw.polygon(tail_pts, fill=BUBBLE_BG)

        # 吹き出し内の「…」ライン
        if size >= 64:
            line_y = (by1 + by2) // 2
            lx1    = bx1 + int(s * 0.06)
            lx2    = bx2 - int(s * 0.06)
            lh     = max(2, int(s * 0.025))
            draw.rounded_rectangle(
                [lx1, line_y - lh, lx2, line_y + lh],
                radius=lh,
                fill=(*SAFE[:3], 200)
            )
            # 2本目（短め）
            line_y2 = line_y + lh * 3
            draw.rounded_rectangle(
                [lx1, line_y2 - lh, lx1 + (lx2-lx1)*2//3, line_y2 + lh],
                radius=lh,
                fill=(*ACCENT[:3], 160)
            )

    # ── 配信ランプ（左上の赤い丸）───────────
    lamp_r  = max(2, int(s * 0.055))
    lamp_cx = int(s * 0.14)
    lamp_cy = int(s * 0.14)
    # グロー
    for gi in range(3, 0, -1):
        gr = lamp_r + gi * max(1, int(s*0.02))
        ga = 40 * gi
        draw.ellipse(
            [lamp_cx-gr, lamp_cy-gr, lamp_cx+gr, lamp_cy+gr],
            fill=(255, 60, 80, ga)
        )
    draw.ellipse(
        [lamp_cx-lamp_r, lamp_cy-lamp_r,
         lamp_cx+lamp_r, lamp_cy+lamp_r],
        fill=(255, 60, 80, 255)
    )

    return img


def build_ico(output_path="icon.ico"):
    sizes = [256, 128, 64, 48, 32, 16]
    images = [draw_icon(s) for s in sizes]
    # ICO として保存（Pillow は複数サイズを1ファイルに埋め込める）
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"✅ アイコン生成完了: {output_path}")
    # PNG プレビューも出力
    preview_path = output_path.replace(".ico", "_preview.png")
    images[0].save(preview_path, format="PNG")
    print(f"✅ プレビューPNG: {preview_path}")


if __name__ == "__main__":
    build_ico("icon.ico")
