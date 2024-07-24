# OmniSharp や .NET について

## OmniSharp

OmniSharp は、C#開発のためのクロスプラットフォーム開発ツールです。
Visual Studio Code（VSCode）や他のエディタで C#コードの補完、ナビゲーション、リファクタリング、デバッグなどの機能を提供します。

- **役割**: OmniSharp は、C#コードの静的解析を行い、コード補完やエラー検出、リファクタリングなどの機能を提供します。Unity の C#スクリプトを VSCode で編集する際に使用されます。
- **設定**: VSCode の設定ファイル（`settings.json`）で OmniSharp の設定を調整できます。例えば、特定の.NET SDK を使用するように設定することができます。

  ```json
  {
    "omnisharp.useModernNet": true,
    "omnisharp.path": "latest"
  }
  ```

### .NET

.NET は、Microsoft が開発したフレームワークで、アプリケーションの開発と実行をサポートします。.NET には、.NET Framework、.NET Core、.NET 5/6/7 などのバージョンがあります。Unity は特定のバージョンの.NET をサポートしています。

- **役割**: .NET は、C#コードの実行環境を提供します。Unity では、.NET Standard 2.0 や 2.1 などを使用して、クロスプラットフォームの互換性を確保します。
- **バージョン**: Unity のバージョンによってサポートされる.NET バージョンが異なります。例えば、Unity 2020 以降は.NET Standard 2.1 をサポートしています。

### C\#

C#は、Microsoft が開発したプログラミング言語で、.NET フレームワーク上で動作します。Unity では、スクリプトの記述に C#が使用されます。

- **役割**: C#は、Unity のゲームロジックやスクリプトを記述するための主要な言語です。オブジェクト指向プログラミングの特性を持ち、強力な型システムと豊富なライブラリを提供します。
- **バージョン**: Unity のバージョンによってサポートされる C#のバージョンが異なります。例えば、Unity 2020 では C# 8.0 がサポートされています。

### Mono

Mono は、.NET フレームワークのオープンソース実装で、クロスプラットフォームの互換性を提供します。Unity は、Mono を使用して C#スクリプトを実行します。

- **役割**: Mono は、Unity のスクリプトランタイムとして機能し、C#コードの実行をサポートします。これにより、Windows、macOS、Linux などの異なるプラットフォームで同じ C#コードを実行できます。
- **設定**: Unity のプロジェクト設定で、スクリプトランタイムバージョンとして Mono を選択することができます。
  - **Edit > Project Settings > Player > Other Settings** で `Scripting Backend` を `Mono` に設定します。

---

# VSCode で Unity の開発を行うための準備手順

## 1. Visual Studio Code のインストール

まず、Visual Studio Code（VSCode）をインストールします。VSCode は Microsoft が提供する無料のコードエディタで、公式サイトからダウンロードできます。

## 2. C#拡張機能のインストール

VSCode で C#コードを快適に編集するために、Microsoft が提供する C#拡張機能をインストールします。

1. VSCode を開きます。
2. 左側のサイドバーにある拡張機能アイコン（四角形のアイコン）をクリックします。
3. 検索バーに「C#」と入力し、Microsoft が提供する「C#」拡張機能をインストールします。

## 3. Unity の設定

Unity での開発に必要な設定を行います。

### Unity プロジェクトの作成または開く

1. Unity Hub を使用して新しいプロジェクトを作成するか、既存のプロジェクトを開きます。

### Visual Studio Code を Unity の外部スクリプトエディタとして設定

1. Unity エディタを開きます。
2. メニューから `Edit` > `Preferences` を選択します。
3. 左側のリストから `External Tools` を選択します。
4. `External Script Editor` ドロップダウンメニューから `Visual Studio Code` を選択します。

### OmniSharp の設定

OmniSharp は、VSCode で C#コードの補完やナビゲーション、リファクタリング、デバッグなどの機能を提供します。必要に応じて、VSCode の設定ファイル（`settings.json`）で OmniSharp の設定を調整します。

1. VSCode を開きます。
2. メニューから `File` > `Preferences` > `Settings` を選択します。
3. 右上のアイコン（ファイルアイコン）をクリックして、`settings.json` を開きます。
4. 以下の設定を追加します。

   ```json
   {
     "omnisharp.useModernNet": true,
     "omnisharp.path": "latest"
   }
   ```

## 4. .NET SDK のインストール

Unity の特定のバージョンによっては、.NET SDK のインストールが必要になる場合があります。.NET SDK は、Microsoft の公式サイトからダウンロードできます。

## 5. Mono の設定

Unity は、Mono を使用して C#スクリプトを実行します。Mono は Unity に同梱されているため、通常は追加のインストールは不要です。

### スクリプトランタイムバージョンの設定

1. Unity エディタでプロジェクトを開きます。
2. メニューから `Edit` > `Project Settings` を選択します。
3. 左側のリストから `Player` を選択します。
4. `Other Settings` セクションを探し、`Scripting Backend` を `Mono` に設定します。
5. `Api Compatibility Level` を `NET Standard 2.0` や `NET Standard 2.1` に設定します。

## 6. Unity プロジェクトを VSCode で開く

Unity エディタで `Assets` フォルダ内の任意の C#スクリプトをダブルクリックすると、VSCode が開きます。これにより、Unity プロジェクトが VSCode で開かれ、C#スクリプトの編集が可能になります。

## 追加の設定とツール

### 1. Unity 拡張機能のインストール

VSCode には、Unity 開発をサポートするための拡張機能がいくつかあります。これらをインストールすることで、開発体験が向上します。

- [Unity for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=visualstudiotoolsforunity.vstuc)
- Unity Code Snippets

### 2. VSCode 設定ファイルの調整

VSCode の設定ファイル（`settings.json`）を調整することで、開発環境をカスタマイズできます。

1. **ファイルの監視設定**:

   - Unity が生成する大量のファイルに対して VSCode が過剰に反応しないように設定します。

   ```json
   {
     "files.watcherExclude": {
       "**/Library/**": true,
       "**/Temp/**": true,
       "**/Obj/**": true,
       "**/Build/**": true,
       "**/Assets/**/Scripts/**": true
     },
     "files.exclude": {
       "**/.git": true,
       "**/.svn": true,
       "**/.hg": true,
       "**/CVS": true,
       "**/.DS_Store": true,
       "**/Library": true,
       "**/Temp": true,
       "**/Obj": true,
       "**/Build": true
     }
   }
   ```

2. **コードフォーマット設定**:

   - C#コードのフォーマットを自動化するための設定です。

   ```json
   {
     "editor.formatOnSave": true,
     "editor.formatOnType": true,
     "csharp.format.enable": true
   }
   ```

### 3. デバッグ設定

Unity プロジェクトのデバッグを行うための設定を行います。

1. **launch.json の設定**:

   - デバッグ設定を行うために、VSCode のデバッグ設定ファイル（`launch.json`）を作成します。
   - デバッグビューを開き、歯車アイコンをクリックして「Unity Editor」を選択します。これにより、`launch.json`が自動的に生成されます。

   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Attach to Unity",
         "type": "unity",
         "request": "attach"
       }
     ]
   }
   ```

### 4. シンタックスハイライトとコード補完の強化

C#コードのシンタックスハイライトとコード補完を強化するための拡張機能をインストールします。

1. **C# Extensions**:
   - C#コードの補完やリファクタリング機能を強化する拡張機能です。
   - インストール方法: 拡張機能マーケットプレイスで「C# Extensions」を検索し、インストールします。

### 5. Git 統合

バージョン管理システムとして Git を使用している場合、VSCode の Git 統合機能を活用します。

1. **GitLens**:
   - Git の履歴や変更を視覚的に確認できる拡張機能です。
   - インストール方法: 拡張機能マーケットプレイスで「GitLens」を検索し、インストールします。

### 6. タスクランナーの設定

ビルドやテストの自動化を行うために、タスクランナーを設定します。

1. **tasks.json の設定**:

   - Unity のビルドやテストを自動化するためのタスクを設定します。

   ```json
   {
     "version": "2.0.0",
     "tasks": [
       {
         "label": "Build Unity Project",
         "type": "shell",
         "command": "path/to/your/unity/Editor/Unity.exe",
         "args": [
           "-projectPath",
           "${workspaceFolder}",
           "-buildTarget",
           "Win64",
           "-executeMethod",
           "BuildScript.PerformBuild"
         ],
         "group": {
           "kind": "build",
           "isDefault": true
         },
         "problemMatcher": []
       }
     ]
   }
   ```
