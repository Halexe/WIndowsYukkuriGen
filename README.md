# WIndows Yukkuri Generator

Windows向けに台本からAquesTalkの音声とPremiere Proに読み込めるFinal Cut Pro XMLを生成するツールです。GUIは標準のtkinterで構築されているため追加の依存は不要です。

## 使い方

### 事前準備

1. Python 3.10 以降をインストールします（標準の `tkinter` が利用できる環境が必要です）。
2. リポジトリを任意の場所へ展開し、コマンドプロンプトまたは PowerShell でこのフォルダへ移動します。
3. AquesTalk（AquesTalkPlayer や aquostalk.exe など）を任意の場所に配置し、実行ファイルのフルパスを控えておきます。
4. `aquestalk_presets.example.json` をコピーして `aquestalk_presets.json` を作成します。`command_template` にはAquesTalkのコマンドラインを記述し、`{text}` `{text_file}` `{output}` `{speaker}` `{voice_id}` `{speed}` `{volume}` のプレースホルダが利用できます。

### 台本ファイルの用意

1. `Script.txt` のサンプルを参考に、台本を UTF-8 で保存します。
2. 話者名（霊夢・魔理沙など）とセリフの間は「全角スペース」で区切ります。
3. セクションを分けたい場合は行頭を `-` で始めるとカットマーカーとして扱われます。

### アプリの起動

1. コマンドプロンプトで `python app.py` を実行すると GUI が起動します。
2. 初回起動時は `AquesTalk設定` ボタンから `aquestalk_presets.json` を選択し、必要であれば話者ごとのプリセットを確認・編集します。

### 音声生成～Premiere 取り込みまで

1. 「台本読込」ボタンで作成した台本ファイルを選択します。読み込んだ内容は画面下部で確認できます。
2. 出力先フォルダ、プロジェクト名、Premiere シーケンスのベース名を必要に応じて入力します。
3. 「音声生成」ボタンを押すと、台本の各セリフが設定済みのプリセットで音声化され、指定した出力フォルダに WAV ファイルが保存されます。
   - 生成中にエラーが出た場合はメッセージダイアログで内容が表示されます。
   - `use_text_file` を有効にしたプリセットは一時ファイルを作成し、自動的に削除します。
4. 音声生成が完了したら「Premiere XML生成」ボタンを押します。音声ファイルと字幕（リンクスタイル霊夢/魔理沙）を含む Final Cut Pro XML が同じフォルダへ出力されます。
5. Premiere Pro の「ファイル > 読み込み」から生成された XML を選択するとシーケンスが作成され、音声と字幕がタイムラインに配置されます。

## スクリプトの書式

- セクション見出しは `- セクション名` の形式で記述します（任意）。
- セリフは `話者（全角スペース）内容` の形式で記述します。
- 空行は無視されます。

例:

```
- イントロ
霊夢　こんにちは
魔理沙　やあ
```

## 出力される字幕スタイル

話者が「霊夢」の場合は字幕スタイル `リンクスタイル霊夢` を、話者が「魔理沙」の場合は `リンクスタイル魔理沙` を自動で適用します。それ以外の話者の場合は `デフォルト字幕` スタイルを設定します。

## AquesTalkPlayerのエラー対処

`C:\YukkuriVoiceGenWin\REIMU が見つかりませんでした。` というエラーが表示される場合、AquesTalkPlayer.exe が参照する音声データフォルダが見つかっていません。

1. YukkuriVoiceGenWin を展開したフォルダ内に `REIMU` や `MARISA` などの音声データフォルダが存在することを確認します。
2. `AquesTalkPlayer.exe` と同じ階層にこれらのフォルダを配置し、フォルダごと `C:\YukkuriVoiceGenWin` などエラーに表示されているパスへ配置します。
3. もしくは `aquestalk_presets.json` の `command_template` を編集し、実際に配置したフォルダへの絶対パスを指定してください（例: `"C:\\Tools\\YukkuriVoiceGenWin\\AquesTalkPlayer.exe ..."`）。

上記のいずれかを実施すると、AquesTalkPlayer が正しい音声データを読み込めるようになりエラーが解消されます。

## aquostalk.exe を利用した音声生成

`aquostalk.exe`（AquesTalk専用のコマンドラインツール）は日本語テキストを Shift_JIS などのテキストファイル経由で受け取る必要があります。このツールを利用する場合は、AquesTalk のプリセットに以下のような追加設定を行ってください。

```json
{
  "speaker": "ナレーション",
  "command_template": "aquostalk.exe /voice {voice_id} /speed {speed} /volume {volume} /file {text_file} /out {output}",
  "voice_id": "NARRATION",
  "speed": 100,
  "volume": 100,
  "use_text_file": true,
  "text_file_encoding": "shift_jis"
}
```

`use_text_file` を `true` に設定すると、台本の各行のテキストを一時ファイルに書き出して `{text_file}` プレースホルダに差し込みます。`text_file_encoding` は生成される一時ファイルの文字コードです（省略時は UTF-8）。`text_file_suffix` を設定すれば一時ファイルの拡張子も変更できます。

これにより `aquostalk.exe` などの「テキストファイルでの入力」を前提としたツールでも正しく音声を生成できます。
