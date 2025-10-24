# WIndows Yukkuri Generator

Windows向けに台本からAquesTalkの音声とPremiere Proに読み込めるFinal Cut Pro XMLを生成するツールです。GUIは標準のtkinterで構築されているため追加の依存は不要です。

## 使い方

1. `aquestalk_presets.json` を `aquestalk_presets.example.json` を元に作成します。`command_template` にはAquesTalkのコマンドラインを記述し、`{text}` `{output}` `{speaker}` `{voice_id}` `{speed}` `{volume}` のプレースホルダが利用できます。
2. `python app.py` を実行するとGUIが起動します。
3. GUI上で台本を読み込み、必要に応じてAquesTalkの設定ファイルパスや出力フォルダ、プロジェクト名を設定します。
4. 「音声生成」ボタンで台本の各セリフを音声化します。
5. 「Premiere XML生成」ボタンで音声ファイルと字幕情報を含んだFinal Cut Pro XMLを出力します。生成されたXMLはPremiere Proに読み込めます。

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
