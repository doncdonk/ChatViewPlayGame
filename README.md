# 🎮 ChatViewPlayGame

Twitch チャット連動ゲームランチャー（配信者向け）  
Python 標準ライブラリのみで動作。追加インストール不要でゲームをプレイできます。

---

## 収録ゲーム

| ゲーム | 状態 | 概要 |
|--------|------|------|
| 💣 ViewBomb | ✅ プレイ可能 | チャットコメントで地雷を避けるマインスイーパー |
| ♟ チャットvsリバーシ | ✅ プレイ可能 | 配信者（黒）vs チャット全体（白）でリバーシ対決 |
| 🏇 競馬 | 🚧 準備中 | チャットでレースに投票して参加 |

---

## 起動方法

### Python で直接実行

```bash
python game.py
```

### Windows exe を使う場合

`build.bat` をダブルクリックするだけ。自動で以下を実行します。

1. `pip install pillow pyinstaller`
2. `python build_icon.py` → `icon.ico` 生成
3. `pyinstaller ChatViewPlayGame.spec` → exe ビルド
4. `dist\token_guide.html` をコピー
5. `ChatViewPlayGame_release.zip` を生成

リリース用 ZIP の中身：
```
ChatViewPlayGame_release.zip
├── ChatViewPlayGame.exe
└── token_guide.html
```

---

## 初回セットアップ

### 1. Twitch OAuth トークンの取得

詳しい手順は `token_guide.html` をブラウザで開いてください。

簡易手順：
1. https://twitchtokengenerator.com/ を開く
2. 「Bot Chat Token」をクリック
3. Twitch にログインして認証
4. ACCESS TOKEN をコピー
5. アプリ起動 → 「⚙ Settings」でトークンを入力（先頭に `oauth:` を付ける）

### 2. アプリの設定

「⚙ Settings」画面で以下を設定して保存：

| 項目 | 内容 |
|------|------|
| Twitch Channel Name | あなたのチャンネル名（小文字） |
| OAuth Token | `oauth:` から始まるトークン |
| Theme | 好みのテーマを選択 |

設定は `config.json` に自動保存されます（次回起動時は入力不要）。

---

## 視聴者コマンド

### 💣 ViewBomb

| コマンド | 動作 |
|----------|------|
| `A1` | A列1行目のセルを開く |
| `flag A1` | A列1行目にフラグを立てる / 外す |

コマンド以外のコメントは弾幕として画面を流れます。  
サイドバーの「📋 Copy hint for chat」ボタンでコマンド説明をクリップボードにコピーできます。

### ♟ チャットvsリバーシ

| コマンド | 動作 |
|----------|------|
| `A1` `C3` など | チャット側のターン中に置きたいマスに投票 |

- 配信者（黒）はマウスクリックで石を置く
- チャット（白）のターンは投票を集計して最多票のマスに自動で打つ
- 配信者は `Space` キーで投票を早期締め切り可能
- 最大投票時間を超えると自動締め切り

---

## テーマ一覧

設定画面で切り替え可能。ラジオボタンを選ぶとリアルタイムでプレビュー。

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

---

## ファイル構成

```
ChatViewPlayGame/
├── game.py                  メイン・画面遷移・全ゲーム画面
├── minesweeper.py           ViewBomb ロジック
├── reversi.py               チャットvsリバーシ ロジック
├── twitch_client.py         Twitch IRC 接続（標準ライブラリのみ）
├── config.py                設定の読み書き
├── config.json              保存済み設定（自動生成・gitignore対象）
├── build_icon.py            アイコン生成スクリプト
├── ChatViewPlayGame.spec    PyInstaller ビルド設定
├── build.bat                ワンクリックビルド（Windows）
├── token_guide.html         Twitch トークン取得ガイド
├── .gitignore
└── README.md
```

---

## 注意事項

- `config.json` にはトークンが含まれます。GitHub などに公開しないでください（`.gitignore` で除外済み）
- トークンは約60日で期限切れになります。期限切れの場合は再取得して設定し直してください
- exe 実行時は `ChatViewPlayGame.exe` と同じフォルダに `config.json` が生成されます
