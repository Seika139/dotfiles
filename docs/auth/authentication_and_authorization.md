# Authentication and Authorization（認証・認可）

インターネット上でセキュアなサービスを提供するためには「正規に承認された人だけを通し、それ以外を遮断する」仕組み（**アクセス制御**）が必要である。
アクセス制御を構成する要素として、認証（Authentication）と認可（Authorization）がある。
**認証** とは、サービス提供者に対してアクセスしようとする主体が主張する身元（Identity）が正当であることを確認することであり、**認可** とは、その主体が特定のリソースにアクセスする権限を持っているかどうかを確認することである。

※ 特に、認証は「○○認証」という用語が多いが、実際にその用語が指すのは認証の方法や手段であり、並列に扱う概念ではない場合があることに注意する。

<!-- 初回と二回目以降
○○認証 -->

<!--

認証・認可情報（credentials）
│
├─ username + password
│    └─ Basic Auth
│
├─ API Key
│
└─ Access Token
     │
     ├─ Opaque Token
     └─ JWT
          ↑ tokenの「形式」

Access Tokenをどう提示するか
     │
     ├─ Bearer
     └─ DPoP
          ↑ tokenの「使い方」
 -->

## 認証

一般的に、ユーザーの認証を要求する Webサービスではユーザーがアクセスする際に認証を行い、その後に認可を行うことでアクセス制御を実現している。

**本人証明**
本人（人間そのものだったり、メールアドレス、ユーザーIDなど）に対して、その人しか知り得ない・持ち得ない情報を提示することで、その人であることを証明する。

認証に用いる情報は下記の3要素がある。

1. 知識情報：パスワード、PINコード、秘密の質問など
2. 所持情報：USBキー、スマートフォン、ICカード、ハードウェアトークンなど
3. 生体情報：指紋、虹彩、顔、手の平の静脈など

このうちの2種類以上を使って認証することを多要素認証（MFA）という。

## 認可

**権限確認**
認証された本人が特定の情報（Webページなどのリソース）にアクセスする権限を持っているかどうかを確認する。

## 認証済み状態を維持する

一般的な Web サービスでは顔認証や ID・パスワードによる認証が用いてログインする。
しかし HTTP は本来ステートレス（状態を保持しない）なプロトコルであるため、通信のたびに認証情報を送信する必要がある。

じゃあ毎回 ID とパスワードを HTTP リクエストに含めて送信しているのだろうか。
この方法は以下の問題点があるため、基本的には採用されない。

- 毎回 ID とパスワードを送信する必要があるため、通信のたびに認証情報が漏洩するリスクがある。（顔認証の場合、リクエストの度に顔認証を実施するのは最悪の UX になるだろう）
- bcrypt などのハッシュ関数を用いてパスワードの検証には計算コストがかかるため、毎回の送信には適さない。

そこで最初の認証が成功してからは、セッションやトークンといった仕組みを用いて認証済み状態を維持することが一般的である。

### Basic認証

Basic認証は、HTTPの認証方式のひとつで、ユーザー名とパスワードを組み合わせて認証を行う。

ベーシック認証は Cookie やログインセッションを使用せず、すべてのHTTPリクエストにユーザー名とパスワードを Base64 でエンコードした文字列を付与する。

[認証済み情報を維持する](#認証済み状態を維持する) の項目で「通信のたびに認証情報が漏洩するリスクがある」と述べたが、Basic認証ではまさにそのリスクが存在する。
Base64は暗号化ではなく、単なるエンコードであるため、通信内容が盗聴されるとユーザー名とパスワードが漏洩する危険性がある。
HTTPSを使用して暗号化することで、通信内容の盗聴や改ざんを防ぐことができる。

それ以外にも Basic認証は以下の問題点がある。

- パスワードのブルートフォース攻撃（総当たり攻撃）: パスワードの複雑さや長さを十分に確保することで対策
- ユーザーがパスワードを忘れた場合に簡単にリセットできる手段がない

### Digest認証

Digest認証は、Basic認証と同様に HTTP プロトコルでサポートされているユーザー認証方式のひとつである。
Basic認証との唯一の違いは、ユーザー名とパスワードを平文で送信するのではなく、ハッシュ化された値を送信する点である。
クライアントは MD5 などのハッシュ関数を使用して、ユーザー名、パスワード、サーバーから送信されたランダムな値（nonce）、HTTPメソッド、リクエストURIなどを組み合わせてハッシュ化し、そのハッシュ値をサーバーに送信する。ハッシュ関数によく使用される MD5 は現在の基準では安全性が低いため、より安全なハッシュ関数の使用が推奨される。
nonce は、リプレイ攻撃を防ぐために使用される一度限りのランダムな値であり、有効期限が設定されている場合もある。

### セッション認証

セッション認証は、Webアプリケーションでよく使用される認証方式のひとつで、セッションという仕組みでユーザーの認証状態を管理する。

- ユーザーがログインフォームにユーザー名とパスワードを入力すると、サーバーはその情報を検証して、認証が成功した場合にセッションを開始し、サーバー側で管理される一意の識別子（セッションID）をクライアントに付与する。
- クライアントはそのセッションIDを Cookie に保存して、以降のリクエストでサーバーにセッションIDを送信する
- セッションIDを受け取ったサーバーは、セッションIDに紐づくユーザー情報を取得して、ユーザーの認証状態を確認する。

セッション認証はログインするとセッションIDが発行する仕組みであるため、Basic認証やDigest認証とは異なってログイン・ログアウトの概念が存在する。
注意点としてセッションを使用してユーザーの認証状態を管理するため、セッションIDが漏洩すると不正アクセスのリスクがある。

**ログイン**

```mermaid
sequenceDiagram

participant Br as Browser
participant Sv as Server
participant Ss as Session Store

Br->>Sv: POST /login<br>id, password
Sv->>Sv: id / password を検証

alt 認証失敗
    Sv-->>Br: 401 Unauthorized
else 認証成功
    Sv->>Sv: 推測困難なセッションIDを生成
    Sv->>Ss: セッションIDに紐づく<br>セッション情報を保存
    Sv-->>Br: 200 OK<br>Set-Cookie: sessionID=xxxx<br>HttpOnly Secure SameSite=Lax
    Note over Br: ブラウザがCookieを保存
end
```

**ログイン後のリクエスト**

```mermaid
sequenceDiagram

participant Br as Browser
participant Sv as Server
participant Ss as Session Store

Br->>Sv: GET /resource<br>Cookie: sessionID=xxxx
Note over Br: Cookieはブラウザが<br>自動的に付与

Sv->>Ss: sessionID でセッションを検索

alt 無効なセッション・期限切れ
    Ss-->>Sv: 該当なし
    Sv-->>Br: 401 Unauthorized
else 有効なセッション
    Ss-->>Sv: セッション情報
    Sv->>Sv: ユーザーとして処理
    Sv-->>Br: 200 OK
end
```

セッションストアとはセッション情報を保存する場所のことで、以下のようなものを利用することが多い。

- サーバーのメモリ
- MySQLなどのデータベース
- Redis などのキャッシュサーバー

サービスをスケールアウト（サーバーを複数台に増やすこと）する場合、セッション情報を共有する必要があるため、データベースやキャッシュサーバーにセッション情報を保持し、各サーバーから共通してセッションを保存・取得できるようにする。

### トークン認証

トークン認証はセッション認証とは異なり、サーバー側でユーザーの認証状態を保持せず、クライアントが保持するトークンを用いて認証を行う方式である。

ログインが成功したタイミングでサーバーはアクセストークンを発行する。
アクセストークンには、有効期限やそのトークンでアクセス可能なリソースの範囲などが含まれている。他にもユーザー情報や認可情報なども含まれることがあるが、それはトークンの形式による。

トークン認証はセッション認証が抱える以下の問題をある程度解決する。

| セッション認証の課題                                         | トークン認証による解決策                       |
| :----------------------------------------------------------- | :--------------------------------------------- |
| サーバー側でセッション情報を保持する必要がある(ステートフル) | サーバーはステートレスで済む                   |
| スケールアウト時にセッション情報を共有する必要がある         | クライアントがトークンを保持するため不要       |
| セッションストアに対する追加費用と運用コスト                 | クライアントがトークンを保持するため不要       |
| セッションIDが漏洩すると不正アクセスのリスクがある           | トークンは有効期限付きで、署名により改ざん防止 |
| ログアウトの概念が必要                                       | トークンの有効期限が切れると自動的に無効       |

トークンの有効期限が切れるまでは誰が使っても有効なので、逆に言えば不正にトークンを取得されると、その有効期限が切れるまで不正アクセスが可能となるという弱点がある。

これを補うために、リフレッシュトークンとアクセストークンを組み合わせて運用するパターンが一般的である。
通常のアクセスでは有効期間が短いアクセストークンのみが使用され、アクセストークンの有効期限が切れたときにリフレッシュトークンを用いて新しいアクセストークンを取得する。これにより、不正にアクセストークンが取得された場合でも被害を最小限に抑えることができる。

```mermaid
sequenceDiagram
participant Cl as Client
participant Sv as Server

Cl->>Sv: リクエスト（アクセストークン付き）
alt アクセストークン有効
  Sv-->>Cl: 200 OK
else アクセストークン期限切れ
  Sv->>Cl: 401 Unauthorized
  Cl->>Sv: リフレッシュトークン送信
  Sv->>Sv: リフレッシュトークンを検証して<br>新しいアクセストークンを生成
  Sv-->>Cl: 新しいアクセストークンを返す
  Cl->>Sv: リクエスト（新しいアクセストークン）
  Sv-->>Cl: 200 OK
end
```

#### JWT（JSON Web Token）

JWT（JSON Web Token）はトークン認証でよく用いられるトークンの形式（規格）である。
つまり、認証以外でも、認可や情報のやり取りなどに使用されることがあるし、JWT以外の形式のトークンも存在する。

JWT の読み方は「ジョット」である。これは [JSON Web Token (JWT) | RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519) に書いてある。

JWTは、2つのドット（.）で区切られたヘッダー、ペイロード、署名の3つの部分から構成される文字列である。

JWTによる詳細な認証の流れは [JWT認証の流れを理解する #初学者向け - Qiita](https://qiita.com/asagohan2301/items/cef8bcb969fef9064a5c) が分かりやすい。

**ヘッダ**

- ヘッダはJWT自身を説明する部分
- alg は必須の項目で、後の手順で署名をつけるときに使うアルゴリズムを表記する
- typ はトークンのタイプで、JWT とする

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**ペイロード**

- JWTが伝達する情報本体である「クレーム（Claims）」を定める JSON オブジェクト
- Claim は `Claim Name: Claim Value` の組からなる

```json
// ペイロードの例
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022
}
```

ペイロードは Base64URL でエンコードするだけなので、パスワードなどの機密情報を含めてはならない。

クレームの名前には以下の3つの分類が存在する。

**登録済みクレーム（Registered Claim Names）**

RFC 7519で標準として定義されているクレーム群。
すべて任意（OPTIONAL）での使用だが、異なるアプリケーション間での相互運用性を高めるための出発点として推奨されている。

- iss（Issuer）: トークンの発行者
- sub（Subject）: トークンが主張している対象（ユーザーの識別子など）
- aud（Audience）: トークンの想定される受信者（利用者）
- exp（Expiration Time）: トークンが無効になる有効期限
- nbf（Not Before）: この時刻より前にはトークンを処理（受入）してはならないという開始時刻
- iat（Issued At）: トークンが発行された時刻
- jti（JWT ID）: トークンの一意な識別子（再プレイ攻撃の防止に有効）

**公開クレーム（Public Claim Names）**
開発者が自由に定義できる。ただし、名前の衝突を防ぐために、IANAのレジストリに登録するか、衝突耐性のある名前（Collision-Resistant Name：ドメイン名やURIなど）を使用する必要がある。

**非公開クレーム（Private Claim Names）**
JWTをやり取りする特定の共同当事者（サービス提供者とクライアントなど）の間で、合意の上で使用する独自仕様のクレーム。衝突する可能性があるため、注意して使用する必要がある。

**署名（Signature）**

Base64urlでエンコードされた「ヘッダ」と、Base64urlでエンコードされた「ペイロード」をドット（.）で連結する。
これを指定されたアルゴリズム（ヘッダの alg で指定されたもの）と、暗号鍵を用いて暗号ハッシュ化（あるいはデジタル署名）を行う。
計算された署名（ハッシュ値）をさらにBase64urlエンコードしたものが「署名」パートとなる。

```javascript
// Base64urlエンコード
{"alg": "HS256", "typ": "JWT"}
eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9

{"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
eyJzdWIiOiAiMTIzNDU2Nzg5MCIsICJuYW1lIjogIkpvaG4gRG9lIiwgImlhdCI6IDE1MTYyMzkwMjJ9Cg==

// HS256 と暗号鍵で署名
xTauSR2dlM1bJuIiwlRHy0Sj-66g5_7qL2RKWT2u5J4

// これらをつなげると JWT が完成する
eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJzdWIiOiAiMTIzNDU2Nzg5MCIsICJuYW1lIjogIkpvaG4gRG9lIiwgImlhdCI6IDE1MTYyMzkwMjJ9.xTauSR2dlM1bJuIiwlRHy0Sj-66g5_7qL2RKWT2u5J4
```

※ [JSON Web Token（JWT）デバッガー](https://www.jwt.io/ja#debugger) にて、ヘッダ、ペイロード、署名の内容を確認できる。

**署名なしJWT（Unsecured JWT）**

JWTのコンテンツがJWT自身の署名以外の手段で保護されている場合、署名や暗号化を行わないJWTを作成できる。この場合、ヘッダの alg は "none" となり、署名部分は空の文字列（何も書かない状態）になる。

**暗号化による保護**

JWTの内容を暗号化して保護するための規格として **JWE（JSON Web Encryption）** が存在する。
JWSが署名によって改ざん検知を行うのに対し、JWEは暗号化によって内容の秘匿性を提供する。

- [JWE（JSON Web Encryption）| RFC 7516](https://datatracker.ietf.org/doc/html/rfc7516)

JWE と JWS を組み合わせて使用することも可能。
HTTPS で通信が暗号化されているため、JWE を使用しなくても通信経路上での盗聴は防げる。

**改竄の検知**

JWTは中身を見られることを防いだり改竄を防ぐための技術ではなく、改竄を検知する技術である。

JWTの署名部分は、暗号鍵を知らなければ中身を見ることはできないが、含まれる情報はヘッダ+ペイロードと同じである。
ヘッダとペイロードはただ Base64URL エンコードしただけなので、デコードすれば簡単に元のJSONに戻すことができる。
つまり誰かが JWT を盗んだ場合、中身を簡単に見ることができ、さらに書き換えることもできる。
もちろんJWTが盗まれてしまうようなことは防がなければならないが、万が一見られても被害がないように、JWTにはパスワードなどを含めてはいけない。

そして万が一改ざんされてしまった場合に、その改ざんを検知するのが、JWTの役割である。
検証した結果改ざんされていない場合にのみ、本物のJWTとみなす。
署名をもちいて改竄されてないことを検証する仕組みを **JWS**（JSON Web Signature）という。

改竄できない理由は署名する際に、ヘッダとペイロードの内容が暗号鍵を用いて暗号ハッシュ化されるためである。
暗号化は共通鍵（対称鍵）方式、か公開鍵暗号方式で行われる。

**共通鍵方式（対称鍵方式）**

共通鍵方式、対称鍵方式はどちらも「暗号化と復号化で同じ鍵を使用する方式」である。
具体的なアルゴリズムとしては HS256（HMAC with SHA-256）などがある。

```mermaid
sequenceDiagram
Actor U as User
participant S as Server

Note over U,S: JWT の発行
U->>S: POST /login<br>id, password
S-->>S: id / password を検証
S-->>S: 暗号鍵で署名した JWT を発行
S-->>U: JWT を返す

Note over U,S: JWT の検証
U->>S: リクエストのヘッダーに JWT を付与して送信
S-->>S: 暗号鍵で署名を検証
S-->>U: 200 OK
```

**公開鍵方式**

公開鍵方式では Application に加えて認証サーバーという登場人物が現れる。
認証サーバーはアプリケーションのサーバーと同一のサービスでもいいし、Google や Microsoft などの自前のサービス外の認証サービスでもよい。
公開鍵方式は署名の生成と署名の検証で異なる鍵を使用することから、公開鍵を自分以外のサービスに配布しても安全であるということを生かして、自前のサービス外の認証サービスを利用できるのである。

```mermaid
sequenceDiagram
  actor U as ユーザー
  participant Auth as 認証サーバー
  participant API as アプリケーションサーバー<br>APIサーバー

  Note over U,Auth: ユーザー認証
  U->>Auth: ログイン
  Auth->>Auth: ユーザーを認証<br/>（ID/Password、OIDC、SAMLなど）

  alt 認証失敗
    Auth-->>U: 401 Unauthorized
  else 認証成功
    Note over U,Auth: アクセストークンの発行
    Auth->>Auth: 秘密鍵で署名したJWTを生成して<br>これをアクセストークンとする
    Auth-->>U: アクセストークンを返す
  end

  Note over U,API: 自前サービスへのアクセス
  U->>API: Request + Access Token
  API->>API: 公開鍵でJWTの署名を検証
  API->>API: exp / aud などを検証

  alt Tokenが有効
    API-->>U: 200 OK
  else Tokenが無効
    API-->>U: 401 Unauthorized
  end
```

---

その説明は後述する OAuth 2.0 や OpenID Connect（OIDC）で行う。
その説明にも備えて、ここではユーザーとサーバーに加えて OP（OpenID Provider）が登場する。

※ OIDC や OAuth、SAML など文脈によって、認証・認可を提供する側のサービスと利用する側のサービスの呼び方が異なるのでややこしい。が IdP / SP は他の文脈でも比較的一貫して使われる（ことが多いように感じる）。

|           | 提供側                   | 利用側                 |
| :-------- | :----------------------- | :--------------------- |
| OIDC      | OpenID Provider（OP）    | Relying Party（RP）    |
| OAuth 2.0 | Authorization Server     | Client                 |
| SAML      | Identity Provider（IdP） | Service Provider（SP） |

JWT を用いた認証において、OpenID Provider（OP）は **JWKS**（JSON Web Key Set）を公開し、クライアントはこれを用いて署名の検証を行う。
JWKS は OpenID Provider が公開しているエンドポイント `/.well-known/jwks.json` から取得できる公開鍵の集合である。

JWKS は以下のように複数の公開鍵を含んだ JSON 形式のデータである。

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "1b94c",
      "use": "sig",
      "n": "vrjOf...",
      "e": "AQAB"
    },
    {
      "kty": "RSA",
      "kid": "2b95d",
      "use": "sig",
      "n": "abc123...",
      "e": "AQAB"
    }
  ]
}
```

Relying Party は kid を用いて JWKS から対応する公開鍵を取得し、署名の検証を行う。
複数の公開鍵を公開しているメリットとして、鍵のローテーションが容易になる点が挙げられる。新しい鍵を追加しても、古い鍵で署名されたトークンは引き続き検証可能である。

**JWK と JWKS**

**kidによる鍵の選択**

<!-- ここからは下書き -->

```mermaid
sequenceDiagram
actor U as User
participant RP as Relying Party（RP）
participant OP as OpenID Provider（OP）
participant JWKS as JWKS Endpoint

note over U,JWKS: JWT の発行（ログイン）
U->>OP: POST /login<br>id, password
OP-->>OP: id / password を検証
OP-->>OP: 暗号鍵で署名した JWT を発行
OP-->>U: JWT を返す

Note over U,JWKS: JWT の検証
U->>OP: リクエストのヘッダーに JWT を付与して送信
OP->>JWKS: 公開鍵を取得
JWKS-->>OP: 公開鍵を返す
OP-->>OP: 公開鍵でJWTの署名を検証
alt JWT の署名が無効
OP-->>U: 401 Unauthorized
else JWT の署名が有効
  OP-->>OP: JWT の exp / iss / aud を検証して有効性を確認
  OP-->>U: 200 OK
end

Note over U,OP: JWT の検証
U->>RP: RPのサービスを使いたいです
RP-->U: OP の認可エンドポイントへのリダイレクト
U->>OP: POST /login<br>id, password
OP-->>OP: id / password を検証
alt 認証失敗
  OP-->>U: 401 Unauthorized
else 認証成功
  OP-->>U: RP の callback URL へリダイレクト<br>Authorization Code を付与
  U->>RP: RP の callback URL へリダイレクト<br>Authorization Code を送信
  RP->>OP: Authorization Code を OP のトークンエンドポイントへ送信
  OP->>OP: 秘密鍵で署名した ID トークンを生成
  OP-->>RP: ID トークンを返す
  RP->JWKS: 公開鍵一覧を取得
  JWKS-->>RP: 公開鍵一覧を返す
  RP-->>RP: ID トークンの kid に対応する公開鍵を選択
  RP-->>RP: 選択した公開鍵で ID トークンの署名を検証
  RP-->>RP: ID トークンの exp / iss / aud を検証して有効性を確認
  alt ID トークンが無効
    RP-->>U: 401 Unauthorized
  else ID トークンが有効
    RP-->>U: 200 OK（RP のサービスを表示）
  end
end
```

---

 <!--

公開鍵暗号方式とは別で
OAuth 2.0 → OIDC の順で説明するのがよさそう。 OIDC とセットで SAML、 SSO も説明する。
OAuth 2.1 もさらに説明する。 PKCE などの拡張も含まれる。

  PASETO
  DPoP
  Opaque
  -->

Bearer Token は、HTTPリクエストのヘッダーにトークンを付与することで認証を行う方式である。
Bearer Token は、OAuth 2.0 や OpenID Connect（OIDC）などの認証・認可プロトコルで使用される。

この方式では、サーバーはトークンを検証することでユーザーの認証を行い、必要に応じて認可情報を取得する。トークンは通常、一定の有効期限を持ち、有効期限が切れると再度認証が必要となる。

```mermaid
sequenceDiagram

participant B as Browser
participant S as Server

B->>S: サーバーに id と pw を POST
S-->>S: id と pw を検証
S-->>S: id と pw が正しい場合、暗号鍵で署名した JWT を生成
S-->>B: JWT を返す
```

### トークン形式の種類

トークンにはいくつかの形式があり、代表的なものとして以下がある。

#### JWT（JSON Web Token）

JWT（JSON Web Token）はトークン認証などで用いられるトークンの形式（規格）である。
つまり、認証以外でも、認可や情報のやり取りなどに使用されることがあるし、JWT以外の形式のトークンも存在する。

#### PASETO

#### SAML Assertion

<!--
SAML
OIDC
OAuth2.0
MFA
JWT
JWKs
OP
SSO
PKCE
nonce
IdP と SP
-->
