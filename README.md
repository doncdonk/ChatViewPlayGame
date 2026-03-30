# 🎮 ChatViewPlayGame

配信者向け Twitch チャット連動ゲームランチャー
Python標準ライブラリのみで動作（追加インストール不要でゲームをプレイ可能）

---

## ▶ 通常起動（Pythonで直接実行）

```bash
python game.py
```

追加インストール不要です。

---

## 📦 Windows exe のビルド方法

### 手順

**① build.bat をダブルクリック**

自動で以下を実行します：
1. pip install pillow pyinstaller
2. python build_icon.py  →  icon.ico 生成
3. pyinstaller ChatViewPlayGame.spec  →  exe ビルド

**② dist\ChatViewPlayGame.exe が完成**

dist フォルダの ChatViewPlayGame.exe を好きな場所に移動して使えます。

---

## 🔑 Twitch OAuth トークンの取得

1. https://twitchtokengenerator.com/ を開く
2. 「Bot Chat Token」をクリック
3. Twitch にログインして認証
4. ACCESS TOKEN をコピー
5. アプリ起動→「設定」画面でトークンを入力（先頭に oauth: を付ける）

---

## 🎮 視聴者コマンド（マインスイーパー）

| コマンド | 動作 |
|----------|------|
| A1       | A列1行目を開く |
| flag A1  | A列1行目にフラグ |

コマンド以外のコメントは弾幕として画面を流れます。

---

## 📺 OBS 設定

「ウィンドウキャプチャ」→「ChatViewPlayGame」を選択するだけ。

---

## 📁 ファイル構成

```
ChatViewPlayGame/
├── game.py                  メイン（起動ファイル）
├── minesweeper.py           ゲームロジック
├── twitch_client.py         Twitch IRC接続
├── config.py                設定読み書き
├── config.json              保存設定（自動生成）
├── build_icon.py            アイコン生成スクリプト
├── ChatViewPlayGame.spec    PyInstaller設定
├── build.bat                ワンクリックビルド（Windows）
└── README.md
```
