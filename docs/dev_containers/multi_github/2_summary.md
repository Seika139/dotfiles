# Dev Containers での複数 GitHub アカウントの運用方法（まとめ）

複数の GitHub アカウントを Dev Containers で運用する場合、最も安全で効率的なベストプラクティスを以下にまとめます。

## 複数の GitHub アカウントを Dev Containers で運用するベストプラクティス

会社用と個人用の GitHub アカウントを Dev Containers 環境でスムーズに使い分けるには、**SSH エージェントフォワーディング**と**リポジトリごとの Git 設定**を組み合わせるのが最適です。

### 1. ホストマシンでの SSH 鍵設定（事前準備）

まず、Dev Containers に入る前に、ホストマシン（あなたのローカル PC）で SSH 鍵の準備と`~/.ssh/config`の設定を行います。

1. **各アカウント用の SSH 鍵ペアを作成する:**
   会社用と個人用で異なる鍵ペアを作成します。ファイル名で区別できるようにすると便利です。

   ```bash
   # 個人用アカウントの鍵
   ssh-keygen -t rsa -f ~/.ssh/id_rsa_personal -C "your_personal_email@example.com"

   # 会社用アカウントの鍵
   ssh-keygen -t rsa -f ~/.ssh/id_rsa_company -C "your_company_email@example.com"
   ```

   鍵作成時にパスフレーズを設定した場合は、忘れないようにしてください。

2. **`~/.ssh/config` を設定する:**
   GitHub への接続時にどの鍵を使うかを SSH に指示するため、`~/.ssh/config`ファイルに以下の設定を追加します。

   ```config
   # ~/.ssh/config

   # 個人用GitHubアカウント
   Host github.com-personal
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_rsa_personal
       IdentitiesOnly yes # これが重要！このホストでは指定された鍵のみ使用

   # 会社用GitHubアカウント
   Host github.com-company
       HostName github.com
       User git
       IdentityFile ~/.ssh/id_rsa_company
       IdentitiesOnly yes # これが重要！このホストでは指定された鍵のみ使用
   ```

3. **SSH エージェントに鍵を登録する:**
   Dev Containers での認証には、SSH エージェントフォワーディングが不可欠です。ホストマシンで SSH エージェントを起動し、作成した鍵をエージェントに登録しておきます。これにより、秘密鍵をコンテナ内部に置くことなく安全に利用できます。

   ```bash
   eval "$(ssh-agent -s)" # ssh-agentが起動していなければ起動
   ssh-add ~/.ssh/id_rsa_personal
   ssh-add ~/.ssh/id_rsa_company
   ```

   パスフレーズを設定している場合は、ここで入力が求められます。

4. **GitHub に公開鍵を登録する:**
   作成した公開鍵（`.pub`ファイル）の内容を、それぞれの GitHub アカウントの「SSH and GPG keys」設定に登録します。

---

### 2. Dev Containers 側の設定と運用

Dev Containers は、デフォルトで SSH エージェントフォワーディングをサポートしているため、基本的には追加の`devcontainer.json`設定は不要です。

1. **SSH エージェントフォワーディングの確認（コンテナ内部）:**
   Dev Container が起動したら、ターミナルで以下のコマンドを実行し、ホストで`ssh-add`した鍵がコンテナ内でも認識されているか確認します。

   ```bash
   ssh-add -l
   ```

   ホストで追加した鍵の情報が表示されれば、SSH エージェントフォワーディングは正常に機能しています。

2. **リポジトリのクローンと Git 設定:**
   各リポジトリをクローンする際に、`~/.ssh/config`で設定した Host 名を使用します。そして、**リポジトリのディレクトリ内でローカルの Git 設定を行います**。これが最もシンプルかつ確実な`gitconfig`の使い分け方法です。

   - **個人用リポジトリの場合:**

     ```bash
     # クローン（URLに config で設定した Host 名を使用）
     git clone git@github.com-personal:YourPersonalUser/your-personal-repo.git
     cd your-personal-repo

     # リポジトリ内で user.name と user.email を設定
     git config user.name "Your Personal Name"
     git config user.email "your_personal_email@example.com"
     ```

   - **会社用リポジトリの場合:**

     ```bash
     # クローン（URLに config で設定した Host 名を使用）
     git clone git@github.com-company:YourCompanyOrg/your-company-repo.git
     cd your-company-repo

     # リポジトリ内で user.name と user.email を設定
     git config user.name "Your Company Name"
     git config user.email "your_company_email@example.com"
     ```

   この`git config`コマンドは、そのリポジトリの`.git/config`ファイルに設定を書き込むため、コンテナを再構築しても設定は保持されます。

3. **グローバルな`gitconfig`の設定（任意）:**
   ホストの`~/.gitconfig`は Dev Containers にコピーされます。もし、会社用・個人用のどちらにも属さない汎用的な Git 操作用のデフォルト設定がある場合は、これをホストのグローバル`gitconfig`に記述しておくと良いでしょう。ただし、個々のリポジトリでの設定が優先されます。

---

### なぜこれがベストプラクティスなのか？

- **セキュリティ:** SSH エージェントフォワーディングにより、**秘密鍵がコンテナ内部に直接コピーされるのを防ぎます。** これにより、コンテナのセキュリティが侵害された場合でも、秘密鍵の漏洩リスクを最小限に抑えられます。
- **シンプルさ:** `devcontainer.json`に複雑な SSH や Git 設定を記述する必要がほとんどありません。ホスト側の SSH 設定がそのまま利用されるため、設定の一元管理が可能です。
- **確実な`gitconfig`の使い分け:** リポジトリごとに`git config`を行うことで、どのリポジトリでどのユーザー情報を使うかが明確になり、意図しないコミット情報の混在を防げます。
- **再利用性:** Dev Containers を破棄して再作成しても、ホストで SSH エージェントに鍵が登録されていれば、特別な作業なく認証が可能です。

この方法で設定することで、Dev Containers 環境でもセキュアかつスムーズに複数の GitHub アカウントを運用できます。
