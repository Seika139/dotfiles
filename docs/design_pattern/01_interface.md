# 疎結合：具象クラスへの依存を避ける

具象クラスへの依存とは、あるコードが特定の具体実装を直接前提にしてしまい、同じ契約を満たす別実装へ差し替えられない状態を指します。
こうなると以下の問題が生じやすくなります。

- 依存する側と依存先が強く結合し、変更の影響範囲が広がる。
- テストや挙動切り替えのためにモックや代替実装を差し込む手段が乏しくなる。
- インターフェイスや抽象化を介さないため、拡張や再利用が難しくなる。

そのため、一般的にはインターフェイス・抽象クラス・DI（依存性注入）などを介して「振る舞い（契約）」に依存させ、実装は後から差し替え可能にするのが推奨されます。

## 悪い例（具象クラスへ直接依存）

```php
<?php
declare(strict_types=1);

class FileLogger
{
    public function write(string $message): void
    {
        // 実装省略: ローカルファイルに追記
    }
}

class OrderService
{
    public function __construct(private FileLogger $logger) {}

    public function place(): void
    {
        // 処理…
        $this->logger->write('注文を登録しました');
    }
}
```

`OrderService` は `FileLogger` という具体的な実装を前提にしており、コンソール出力やクラウド転送など別実装へ差し替えたい時にコードを書き換える必要があります。

## 良い例（抽象に依存・DI）

```php
<?php

declare(strict_types=1);

interface PaymentGateway
{
    public function charge(int $amount): void;
}

class QUICPayGateway implements PaymentGateway
{
    public function charge(int $amount): void
    {
        // QUICPay API で決済する処理
    }
}

class PayPalGateway implements PaymentGateway
{
    public function charge(int $amount): void
    {
        // PayPal API で決済する処理
    }
}

class OrderService
{
    public function __construct(private PaymentGateway $gateway) {}

    public function place(int $amount): void
    {
        // 業務ロジック…
        $this->gateway->charge($amount);
    }
}
```

```php
<?php

declare(strict_types=1);

// --- 実際の利用側で依存を注入する例 ---

$gateway = new QUICPayGateway();              // ここで具体実装を選択
$orderService = new OrderService($gateway);  // OrderService へ注入

$orderService->place(5000);
```

### 「抽象に依存する」とは

上記の例では `OrderService` は `PaymentGateway` という抽象（契約）に依存するだけなので、`QUICPayGateway` でも `PayPalGateway` でも渡したものがそのまま利用できます。
テスト時にはモック化した `PaymentGateway` を差し込めるため、疎結合・テスタブルな構造になります。

### DI（依存性注入）とは

`OrderService` は `PaymentGateway` という抽象に依存し、具象クラスは外側（利用側）で選択・注入します。
この注入はコンストラクタから行われているため「コンストラクタインジェクション」と呼ばれます。
テスト時は `PaymentGateway` を実装したテストダブルを注入すれば外部サービスを叩かずに検証できます。

## 抽象に依存と DI は視点が異なる

両方とも「具象に縛られない設計」を目指しますが、視点が少し異なります。

### 抽象に依存する

コードの依存対象がインターフェイス（契約）であることを示した設計の話です。`OrderService` が `PaymentGateway` に依存するように書けば、どの実装が来ても振る舞いは契約に従ってくれる、という“依存先”の選び方の原則です。

### DI（依存性注入）

「その抽象を、どこで・どうやって具象に差し替えるか」という“注入の仕組み”の話です。`OrderService` のコンストラクタでインターフェイス型を受け取り、利用側が `QUICPayGateway` や `PayPalGateway` を渡すことで差し替えられる、という具象の渡し方（注入経路）を具体化しています。

---

まとめると、抽象に依存する設計は「何に依存すべきか」の原則、DI は「その抽象をどう渡して結合を緩めるか」という実装パターンです。抽象への依存が土台にあり、その依存関係を実際に差し込む手段として DI が機能する、という関係になります。

## DI 以外の注入方法

- セッターインジェクション（依存を後から setXxx() などで渡す）
- メソッドインジェクション（処理メソッド呼び出し時に依存を渡す）
- プロパティインジェクション（公開 or アノテーション付きプロパティへ直接代入）

いずれも目的は「具象に縛られず、外部から差し替えられるようにすること」ですが、タイミング（生成時・呼出時）や適用対象（全体 vs 特定メソッド）で使い分けます。
