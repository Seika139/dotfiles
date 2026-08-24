# 作図

git 管理が容易なテキストを一次情報として、人間が見やすい図を作成するツールについてまとめる。
LLM が図を作成する場合においても、テキストを介して図を作成することで、その図の編集やバージョン管理が容易になる。

## 作図のステップ

図の作成においては以下のように複数のステップからなる。

1. DSL: 人間やLLMが記述するためのテキスト形式の言語
2. Internal Model: テキストに書かれた「意味・構造」を、プログラムが扱える構造化データにする
3. Layout: 構造化データを、図にするとき「どこに・どう配置するか」を計算する
4. Rendering: 計算された配置情報をもとに、図を描画する。出力するデータ形式は、SVG, PNG, PDF, HTML など様々

描画ツールは様々あるが、サービスによっては、このステップの一部のみを提供する場合もある。(Structurizr, ELK, Cytoscape.js, React Flow など)
以降で紹介する Mermaid, PlantUML, D2 は、DSL から Rendering までを一貫して提供する。（内部のレイアウトエンジンに ELK などを利用している）

## 代表的なツール

### PlantUML

Java が必要

**VSCode 拡張機能**: <https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml>

### Mermaid

Markdown に埋め込み
.mmd または .mermaid

**VSCode 拡張機能**: <https://marketplace.visualstudio.com/items?itemName=vstirbu.vscode-mermaid-preview>, <https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid> など

### D2

go で書かれたツール。

```bash
brew install d2
```

**VSCode 拡張機能**: <https://marketplace.visualstudio.com/items?itemName=terrastruct.d2>

<https://qiita.com/makioshibori/items/006983f8b7486c0752e3>

<https://senkohome.com/ai-diagram-general/#graphvizdot%E8%A8%80%E8%AA%9E--%E8%87%AA%E5%8B%95%E3%83%AC%E3%82%A4%E3%82%A2%E3%82%A6%E3%83%88%E3%81%AE%E5%85%83%E7%A5%96>
