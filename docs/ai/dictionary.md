# Dictionary

AI に関する用語集。

- [Dictionary](#dictionary)
  - [ChatGPT](#chatgpt)
  - [Generative AI](#generative-ai)
  - [Hallucination](#hallucination)
  - [LLM (Large Language Model)](#llm-large-language-model)
  - [Knowledge Cutoff](#knowledge-cutoff)
  - [MCP (Model Context Protocol)](#mcp-model-context-protocol)
    - [MCP ホスト](#mcp-ホスト)
    - [MCP クライアント](#mcp-クライアント)
    - [MCP サーバー](#mcp-サーバー)
    - [参考ページ](#参考ページ)
  - [RAG (Retrieval-Augmented Generation)](#rag-retrieval-augmented-generation)

## ChatGPT

OpenAI が開発した [LLM](#llm-large-language-model)「GPT-3.5」や「GPT-4」を利用したチャットサービス。

## Generative AI

日本語で「生成 AI」と呼ばれる、テキスト、画像、音声などの新しいコンテンツを自律的に生成する AI の総称。
従来の AI は事前に学習したデータの範疇で判断・判定していたのに対し、生成 AI は自らが獲得した学習成果から新たに創造することができる。

## Hallucination

日本語で「幻覚（ハルシネーション）」と呼ばれる、AI が事実と異なる情報を生成する現象。
AI が自信を持って誤った情報を提供することがあり、使用者はその情報の正確性を確認する必要がある。

## LLM (Large Language Model)

日本語で「大規模言語モデル」と呼ばれる、膨大なテキストデータを学習して自然言語処理を行う AI モデル。
自律的にデータを生成する「[生成 AI](#generative-ai)」の一種であり、LLM は自然言語の理解と生成に特化している。

代表的なモデルには以下のようなものがある。

- GPT（OpenAI）
- Claude（Anthropic）
- Gemini（Google DeepMind）
- LLaMA（Meta）

## Knowledge Cutoff

単に「カットオフ」とも呼ばれる、AI モデルがいつまでのデータを学習しているかを示す日付。
[LLM](#llm-large-language-model)などの AI モデルは過去のデータに基づいて学習されているため、最新の情報について正確に答えることができない。

## MCP (Model Context Protocol)

AI アプリケーションと外部の情報源（データベースや API など）の間の通信を **標準化** するためのプロトコル。

従来は、AI モデル（`GPT-4`や`Claude`など）と各種データソース（データベース、ファイル、クラウドサービスなど）を連携する際に、AI やデータソースごとに別々の API や認証方式を実装しなければならなかった。
しかし、MCP という標準化に対応することで、AI アプリケーションとデータソースの間の通信を統一的に行うことが可能になる。

### MCP ホスト

LLM を内包したアプリケーション（Claude Desktop や Zed, Cursor など）のこと。
MCP ホストは、MCP クライアントを通じて外部の情報源と通信し、LLM に必要な情報を提供する役割を果たす。

### MCP クライアント

MCP ホスト内に組み込まれたコンポーネントで、MCP サーバとの通信を担当する。

### MCP サーバー

特定のデータソースやツールへのアクセスを提供する軽量サーバーのこと。
例えば、ファイルシステム、データベース、API などへのアクセスを提供するサーバーがある。
サーバーはクライアントからのリクエストを処理し、必要なデータや機能を提供する。

### 参考ページ

- [Model Context Protocol（MCP）とは？生成 AI の可能性を広げる新しい標準](https://zenn.dev/cloud_ace/articles/model-context-protocol)
- [【MCP のトリセツ #1】MCP の概要と導入方法](https://zenn.dev/takna/articles/mcp-server-tutorial-01-install)
- [【徹底解説】MCP とは？「AI の USB ポート」 #LLM - Qiita](https://qiita.com/syukan3/items/f74b30240eaf31cb2686)

## RAG (Retrieval-Augmented Generation)

日本語では「検索拡張生成」と呼ばれる、[LLM](#llm-large-language-model) に検索機能を組み合わせた AI の活用手法。

「知らないことは答えられない」という LLM の弱点を補うために、外部の情報源から必要な情報を取得して LLM に提供してより正確で関連性の高い回答を生成する。

[生成 AI](#generative-ai)には [カットオフ](#knowledge-cutoff)があるため、新たな知識をインプットするには、専用の学習データを用意し、一定の時間をかけて追加学習を行う必要があるが、RAG ではその追加学習のステップを省略できる。
生成 AI に質問をする際に、その質問に関連する情報を同時に提供することで、その情報に基づいた適切な回答を導き出すことができるのです。
たとえば「本日の社員食堂のおすすめを教えてほしい」と生成 AI に聞いても、そもそも自社の社員食堂のメニューを知らない生成 AI には回答できません。そこで RAG では、生成 AI に質問する際、同時に社員食堂のメニューのデータを渡します。こうすることで、生成 AI が独自情報を踏まえた回答を行えるようになります。
