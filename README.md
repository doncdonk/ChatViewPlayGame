# 🎮 ChatViewPlayGame

Twitch チャット連動ゲームランチャー（配信者向け）
Python 標準ライブラリ + Pillow + NumPy で動作。OBS のウィンドウキャプチャで配信に映せます。

---

## 収録ゲーム

| ゲーム | 状態 | 概要 |
|--------|------|------|
| 💣 ViewBomb | ✅ | チャットコメントで地雷を避けるマインスイーパー |
| ♟ チャットvsリバーシ | ✅ | 配信者（黒/白選択可）vs チャット全体でリバーシ対決 |
| 🏇 競馬 | ✅ | チャットでレースに投票・ポイント獲得 |
| 🎨 ペイント | ✅ | お絵描き配信・チャットが弾幕で流れる |

---

## 起動方法

### Python で直接実行

```bash
python game.py
```

### Windows exe を使う場合

`build.bat` をダブルクリックするだけ。

1. `pip install pillow numpy pyinstaller`
2. `python build_icon.py` → `icon.ico` 生成
3. `pyinstaller ChatViewPlayGame.spec` → exe ビルド
4. `dist\token_guide.html` / `dist\img\` をコピー
5. `ChatViewPlayGame_release.zip` を生成

**リリース ZIP の構成：**
```
ChatViewPlayGame_release.zip
├── ChatViewPlayGame.exe
├── token_guide.html
└── img/
    ├── rdesign_19914.png  （茶色馬スプライト）
    ├── rdesign_19916.png  （白馬スプライト）
    └── rdesign_19917.png  （ゴール背景）
```

---

## 初回セットアップ

### 1. Twitch OAuth トークンの取得

`token_guide.html` をブラウザで開いてください。

簡易手順：
1. https://twitchtokengenerator.com/ を開く
2. 「Bot Chat Token」をクリック
3. Twitch にログインして認証
4. ACCESS TOKEN をコピー
5. アプリ起動 → 「⚙ Settings」でトークンを入力（先頭に `oauth:` を付ける）

### 2. アプリの設定

「⚙ Settings」画面で以下を設定：

| 項目 | 内容 |
|------|------|
| Window Size | 1280×720 / 1600×900（デフォルト）/ 1920×1080 |
| Theme | 7種類から選択（リアルタイムプレビュー） |
| Twitch Channel Name | あなたのチャンネル名（小文字） |
| OAuth Token | `oauth:` から始まるトークン |

ウィンドウサイズを変更した場合は再起動が必要です（保存後に再起動ボタンが表示されます）。

### 3. オンライン / オフライン切り替え

トップメニューの `🌐 Online` / `📴 Offline` ボタンで切り替え。
Offline モードでは Twitch 接続なしでゲームをプレイできます。

---

## 視聴者コマンド

### 💣 ViewBomb

| コマンド | 動作 |
|----------|------|
| `A1` | A列1行目のセルを開く（列 A〜Z、行 1〜） |
| `flag A1` | A列1行目にフラグを立てる / 外す |

- 配信者はマウスクリックでも操作可能
- ロビーで座標文字サイズをスライダー調整可能
- モード: 通常 / 連続（クリアごとに地雷+3）

### ♟ チャットvsリバーシ

| コマンド | 動作 |
|----------|------|
| `A1` `C3` など | チャット側ターン中に投票 |

- 配信者の手番（黒/白）をロビーで選択可能
- チャット側の時間切れ時の自動配置（有効/無効）を選択可能
- 配信者は `Space` キーで投票を早期締め切り

### 🏇 競馬

| コマンド | 動作 |
|----------|------|
| `1` 〜 `8` | 該当番号の馬に投票（1人1票） |

- 配信者も投票画面をクリックして投票可能
- ステータス・調子・騎手相性がレース結果に影響
- オッズ表示あり（的中でオッズ×1pt獲得）
- レース数: 1 / 3 / 5 / 10 / 無限
- 結果後の自動遷移: なし / 15 / 30 / 60秒
- 複数レースの累積ポイントランキングを表示
- 馬は茶色/白馬の画像で描画（`img/` ディレクトリ必須）

**ゴール演出の流れ：**
```
GOAL!! テキスト（1.5秒）
 → 勝ち馬スライドイン（1秒）
 → 順位表＋花吹雪（3秒）
 → 結果画面
```

### 🎨 ペイント

チャットコメントが弾幕として描画エリアを流れます。

| ツール | 操作 |
|--------|------|
| ✏ ペン | ドラッグで自由描画 |
| ／ 直線 | ドラッグ→放しで確定 |
| □ 四角 | ドラッグ→放しで確定 |
| ○ 円/楕円 | ドラッグ→放しで確定 |
| ✦ 消しゴム | ドラッグで白く消す |

- 太さ: 1 / 3 / 5 / 8px
- カラーパレット: 16色プリセット＋カスタムカラーピッカー
- ↩ 元に戻す（1ストローク単位）
- 🗑 全消し
- 💾 保存（exe と同じフォルダに `paint_YYYYMMDD_HHMMSS.png` で保存）

---

## テーマ一覧

| テーマ名 | 雰囲気 |
|----------|--------|
| NightBlue | 深夜ネオン調（デフォルト） |
| TerminalGreen | CRT モニター・ハッカー風 |
| ArcadeNeon | 80年代ゲーセン |
| SteelGray | ミリタリー・金属質感 |
| SunsetWarm | オレンジ・ピンク暖色系 |
| IceWhite | 北欧・クリーン |
| VoidPurple | 宇宙・サイバーパンク |

---

## OBS 設定

1. OBS を起動
2. ソース → `+` → **ウィンドウキャプチャ** を追加
3. ウィンドウ一覧から **ChatViewPlayGame** を選択
4. OK をクリック

ウィンドウサイズは起動時に固定されるため、キャプチャ枠がズレません。

---

## ファイル構成

```
ChatViewPlayGame/
├── game.py                  メイン・全画面クラス
├── minesweeper.py           ViewBomb ロジック
├── reversi.py               リバーシ ロジック
├── horserace.py             競馬ロジック（馬・騎手生成、オッズ計算、描画クラス）
├── twitch_client.py         Twitch IRC 接続
├── config.py                設定の読み書き
├── config.json              保存済み設定（自動生成・gitignore対象）
├── build_icon.py            アイコン生成スクリプト
├── ChatViewPlayGame.spec    PyInstaller ビルド設定
├── build.bat                ワンクリックビルド（Windows）
├── token_guide.html         Twitch トークン取得ガイド
├── img/                     競馬用画像（馬スプライト・ゴール背景）
│   ├── rdesign_19914.png
│   ├── rdesign_19916.png
│   └── rdesign_19917.png
├── .gitignore
└── README.md
```

---

## 将来の拡張予定

### 競馬 画像アニメーション対応
`horserace.py` の `ImageHorseRenderer` に PNG フレームを渡すだけで差し替え可能な設計になっています。

```
horse_frames/
├── run_0.png 〜 run_3.png  # 走行フレーム（推奨: 透過PNG）
└── goal.png                # ゴール時
```

---

## 注意事項

- `config.json` にはトークンが含まれます。GitHub などに公開しないでください（`.gitignore` で除外済み）
- トークンは約60日で期限切れになります。期限切れの場合は再取得して設定し直してください
- exe 実行時は `ChatViewPlayGame.exe` と同じフォルダに `config.json` と `img/` が必要です
- ペイント保存（`paint_*.png`）は `.gitignore` で除外済みです

---

## クレジット

### イラスト素材

本プロジェクトで使用しているイラスト素材は以下のサイトからお借りしています。

**イラストセンター**
- サイト: https://illustcenter.com/
- 利用規約: https://illustcenter.com/terms/
- 制作: R-DESIGN

素材の著作権はイラストセンター（R-DESIGN）に帰属します。
