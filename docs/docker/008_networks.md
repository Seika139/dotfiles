# Networks between containers

Docker Compose は、複数のコンテナを連携させてアプリケーションを構築する際に非常に便利なツールです。そのコンテナ間の通信を司るのが「ネットワーク」であり、そのネットワークがどのように動作するかを決定するのが「ドライバ」です。

## Docker Compose におけるネットワーク

Docker Compose で `compose.yml` ファイルを使ってサービスを定義すると、デフォルトでは、その Compose ファイルで定義されたすべてのサービスが所属する単一のネットワークが自動的に作成されます。このデフォルトネットワークにより、各サービスは他のサービスに対してサービス名（コンテナ名）でアクセスできるようになります。

```yaml
services:
  web:
    image: nginx
    ports:
      - "80:80"
  app:
    image: my-app
    environment:
      DB_HOST: db
  db:
    image: postgres
```

この例では `app`, `web`, `db` の 3 つのサービスが定義されています。
これらのサービスはすべて Docker Compose によって自動的に作成された同じネットワークに接続されます。
これにより、`app` サービスは `db` サービスに対して `db` というホスト名でアクセスできるようになります。
このように、Docker Compose はサービス間の通信を簡単に設定できるようにしてくれます。

## カスタムネットワークを定義する

より複雑な構成や、サービス間のネットワーク分離が必要な場合は、自分でカスタムネットワークを定義できます。 `networks` セクションをトップレベルで定義し、各サービスでどのネットワークに接続するかを指定します。

```yaml
services:
  web:
    image: nginx
    ports:
      - "80:80"
    networks:
      - frontend_network # frontend_network に接続
  app:
    image: my-app
    environment:
      DB_HOST: db
    networks:
      - frontend_network # frontend_network に接続
      - backend_network # backend_network に接続
  db:
    image: postgres
    networks:
      - backend_network # backend_network に接続

networks:
  frontend_network: # フロントエンド用ネットワーク
    driver: bridge
  backend_network: # バックエンド用ネットワーク
    driver: bridge
```

この例では、frontend_network と backend_network という 2 つのカスタムネットワークを定義しています。

- web サービスと app サービスは frontend_network に接続し、相互に通信できます。
- app サービスと db サービスは backend_network に接続し、相互に通信できます。
- web サービスと db サービスは共通のネットワークに接続されていないため、直接通信できません。app サービスを介して間接的に通信することになります。

## 外部ネットワークの利用

Docker Compose で管理されていない既存のネットワークにコンテナを接続することもできます。これは、`external: true` を設定することで実現します。

```yaml
services:
  my_service:
    image: some_image
    networks:
      - existing_network # 既存のネットワークに接続

networks:
  existing_network:
    external: true
```

この設定の場合、`existing_network` という名前のネットワークが事前に `docker network create existing_network` などで作成されている必要があります。

## ネットワークドライバの種類

ネットワークドライバは、Docker ネットワークの基盤となる技術を決定します。Docker はいくつかの組み込みドライバを提供しており、用途に応じて選択できます。

### bridge (ブリッジ) - デフォルト

- 特徴:
  - Docker のデフォルトのネットワークドライバです。
  - 仮想ブリッジを作成し、そのブリッジにコンテナを接続します。
  - 同じブリッジネットワーク上のコンテナは、IP アドレスやコンテナ名（DNS 名前解決）を使って相互に通信できます。
  - ホストマシンからコンテナにアクセスするには、ポートフォワーディング（-p オプション）が必要です。
  - 異なる Docker ホスト上のコンテナ間では直接通信できません。
- 利用シーン:
  - 単一ホスト上で複数のコンテナを連携させる一般的なアプリケーション。
  - 開発環境や小規模な本番環境。

### host (ホスト)

- 特徴:
  - コンテナが Docker ホストのネットワークスタックを直接使用します。
  - コンテナは独自のネットワーク名前空間を持たず、ホストと同じ IP アドレス、ポート、ネットワークインターフェイスを共有します。
  - ポートフォワーディングが不要で、ホストの IP アドレスとポートを使ってコンテナのサービスにアクセスできます。
  - コンテナとホスト間のネットワーク分離がなくなるため、セキュリティリスクやポート競合に注意が必要です。
- 利用シーン:
  - ネットワークのオーバーヘッドを最小限に抑えたい場合。
  - コンテナが特定のネットワーク設定を必要とせず、ホストのネットワークをそのまま利用したい場合。
  - デバッグ目的。
- 設定方法: `network_mode: host` をサービスに指定します。

  ```yaml
  services:
    my_service:
      image: some_image
      network_mode: host
  ```

### overlay (オーバーレイ)

- 特徴:
  - 複数の Docker デーモンホストにまたがる分散ネットワークを作成します。
  - Docker Swarm などのクラスター環境で、異なるホスト上のコンテナ間で通信するために使用されます。
  - 暗号化を有効にすることで、セキュアな通信が可能です。
  - Docker がパケットのルーティングを透過的に処理します。
- 利用シーン:
  - Docker Swarm モードでマルチホスト環境を構築する場合。
  - マイクロサービスアーキテクチャで、異なるホスト上のサービス間通信が必要な場合。

### none (なし)

- 特徴:
  - コンテナにネットワークインターフェイス（ループバックインターフェイスを除く）が割り当てられません。
  - コンテナは外部との通信が完全に遮断されます。
- 利用シーン:

  - ネットワークアクセスが不要なコンテナ（例: 計算のみを行うバッチ処理）。
  - セキュリティを最大化したい場合。
  - 設定方法: `network_mode: none` をサービスに指定します。

    ```yaml
    services:
      isolated_task:
        image: some-image
        network_mode: none
    ```

### macvlan (MacVLAN) および ipvlan (IPvLAN)

- 特徴:
  - コンテナに専用の MAC アドレスを割り当て、ホストネットワークに直接接続させます。
  - コンテナが物理ネットワーク上の独立したデバイスとして振る舞うため、ルーターやスイッチから直接 IP アドレスが割り当てられるように見えます。
- 利用シーン:
  - 既存のネットワークインフラストラクチャにコンテナを組み込みたい場合。
  - ネットワークに依存するレガシーアプリケーションを Docker で実行する場合。
