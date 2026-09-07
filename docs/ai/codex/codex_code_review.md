# Codex Code Review

※ 最終更新: 2026/09

Codex Cloud と GitHub を連携して Pull Request に対して Codex にコードレビューさせる機能。

公式ドキュメント: <https://learn.chatgpt.com/ja-JP/docs/third-party/github>

## 基本的な使い方

pull request に

```text
@codex review
```

とコメントすると、Codex のレビューが開始する。
上記の設定画面から、コメントなしで自動的にレビューを開始する設定も可能。

## Codex Review 側の設定

設定画面: <https://chatgpt.com/codex/cloud/settings/code-review> から ChatGPT のアカウント単位で Codex Review の設定を行う。
ChatGPT アカウントに紐づいている GitHub アカウントに対して「アカウント全体に対する設定」と「リポジトリ単位の設定」の両方を行うことができる。

アカウント単位の設定では以下の設定ができる

- Codex Code Review の ON/OFF
- デフォルトの Review trigger の設定
- 網羅的・徹底的なコードレビューをするか否か（Exhaustive code review）
- Codex のクレジットを消費してコードレビューを行うか否か

## Review trigger

自動レビューのタイミングは以下の3種類。

- On PR open: PR がレビュー対象になったタイミングで1回
- On every push: PR に新しい commit が push されるたび
- Smart Trigger (Experimental): Codex 側で適切なタイミングを判断する実験的モード

なお、 Draft Pull Request の場合は自動レビューは行われない。 Draft から Ready for Review に変更されたタイミングで自動レビューが開始される。

## リポジトリ固有の設定

AGENTS.md でリポジトリ固有の設定ができる。

ルールの対象コードに最も近いファイルに `## Code Review Rules` セクションを追加する。
つまり、リポジトリ全体のルールはルートの AGENTS.md に追加し、サービス固有のルールは `services/<service_name>/AGENTS.md` のような下位ディレクトリに追加する。

```markdown
## Code Review Rules

- rule1: description
- rule2: description
```

### 有用なルール

- 影響が大きいリポジトリ固有の動作に注目します。 指摘対象となる互換性の制約、データ境界、危険な副作用を記述し、 それが重要な理由も説明します。
- 安全な方法や例外を明記します。 Codex が実際の問題と想定どおりの動作を区別できるよう、十分なコンテキストを示します。
- ルールの適用範囲を限定し、長期的に有効な内容にします。 変更される可能性のある関数名ではなく、 期待する結果を重視し、ガイダンスを対象コードの近くに配置します。
- 機械的なチェックは CI に任せます。 フォーマットやリントなど、 機械的に判定できるチェックはレビューのルールに含めないでください。

## レビュー指摘への対応

ユーザーが下記のようなコメントを残すことで、Pull Request 内の問題の修正を依頼できる。

```text
@codex fix the P1 issue
```

Codex は Pull Request をコンテキストとしてクラウドチャットを開始し、必要な権限がある場合は修正をブランチにプッシュできる。

## Codex へのその他のタスクの依頼

コメントで @codex をメンションし、review 以外の内容を指定すると、Codex は Pull Request をコンテキストとしてクラウドチャットを開始する。

```text
@codex fix the CI failures
```
