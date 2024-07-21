# OmniSharp や .NET について

## OmniSharp

OmniSharp は、C#開発のためのクロスプラットフォーム開発ツールです。
Visual Studio Code（VSCode）や他のエディタでC#コードの補完、ナビゲーション、リファクタリング、デバッグなどの機能を提供します。

- **役割**: OmniSharpは、C#コードの静的解析を行い、コード補完やエラー検出、リファクタリングなどの機能を提供します。UnityのC#スクリプトをVSCodeで編集する際に使用されます。
- **設定**: VSCodeの設定ファイル（`settings.json`）でOmniSharpの設定を調整できます。例えば、特定の.NET SDKを使用するように設定することができます。

  ```json
  {
      "omnisharp.useModernNet": true,
      "omnisharp.path": "latest"
  }
  ```

### .NET

.NETは、Microsoftが開発したフレームワークで、アプリケーションの開発と実行をサポートします。.NETには、.NET Framework、.NET Core、.NET 5/6/7などのバージョンがあります。Unityは特定のバージョンの.NETをサポートしています。

- **役割**: .NETは、C#コードの実行環境を提供します。Unityでは、.NET Standard 2.0や2.1などを使用して、クロスプラットフォームの互換性を確保します。
- **バージョン**: Unityのバージョンによってサポートされる.NETバージョンが異なります。例えば、Unity 2020以降は.NET Standard 2.1をサポートしています。

### C\#

C#は、Microsoftが開発したプログラミング言語で、.NETフレームワーク上で動作します。Unityでは、スクリプトの記述にC#が使用されます。

- **役割**: C#は、Unityのゲームロジックやスクリプトを記述するための主要な言語です。オブジェクト指向プログラミングの特性を持ち、強力な型システムと豊富なライブラリを提供します。
- **バージョン**: UnityのバージョンによってサポートされるC#のバージョンが異なります。例えば、Unity 2020ではC# 8.0がサポートされています。

### Mono

Monoは、.NETフレームワークのオープンソース実装で、クロスプラットフォームの互換性を提供します。Unityは、Monoを使用してC#スクリプトを実行します。

- **役割**: Monoは、Unityのスクリプトランタイムとして機能し、C#コードの実行をサポートします。これにより、Windows、macOS、Linuxなどの異なるプラットフォームで同じC#コードを実行できます。
- **設定**: Unityのプロジェクト設定で、スクリプトランタイムバージョンとしてMonoを選択することができます。
  - **Edit > Project Settings > Player > Other Settings** で `Scripting Backend` を `Mono` に設定します。
  
---

# VSCodeでUnityの開発を行うための準備手順

## 1. Visual Studio Codeのインストール

まず、Visual Studio Code（VSCode）をインストールします。VSCodeはMicrosoftが提供する無料のコードエディタで、公式サイトからダウンロードできます。

## 2. C#拡張機能のインストール

VSCodeでC#コードを快適に編集するために、Microsoftが提供するC#拡張機能をインストールします。

1. VSCodeを開きます。
2. 左側のサイドバーにある拡張機能アイコン（四角形のアイコン）をクリックします。
3. 検索バーに「C#」と入力し、Microsoftが提供する「C#」拡張機能をインストールします。

## 3. Unityの設定

Unityでの開発に必要な設定を行います。

### Unityプロジェクトの作成または開く

1. Unity Hubを使用して新しいプロジェクトを作成するか、既存のプロジェクトを開きます。

### Visual Studio CodeをUnityの外部スクリプトエディタとして設定

1. Unityエディタを開きます。
2. メニューから `Edit` > `Preferences` を選択します。
3. 左側のリストから `External Tools` を選択します。
4. `External Script Editor` ドロップダウンメニューから `Visual Studio Code` を選択します。

### OmniSharpの設定

OmniSharpは、VSCodeでC#コードの補完やナビゲーション、リファクタリング、デバッグなどの機能を提供します。必要に応じて、VSCodeの設定ファイル（`settings.json`）でOmniSharpの設定を調整します。

1. VSCodeを開きます。
2. メニューから `File` > `Preferences` > `Settings` を選択します。
3. 右上のアイコン（ファイルアイコン）をクリックして、`settings.json` を開きます。
4. 以下の設定を追加します。

   ```json
   {
       "omnisharp.useModernNet": true,
       "omnisharp.path": "latest"
   }
   ```

## 4. .NET SDKのインストール

Unityの特定のバージョンによっては、.NET SDKのインストールが必要になる場合があります。.NET SDKは、Microsoftの公式サイトからダウンロードできます。

## 5. Monoの設定

Unityは、Monoを使用してC#スクリプトを実行します。MonoはUnityに同梱されているため、通常は追加のインストールは不要です。

### スクリプトランタイムバージョンの設定

1. Unityエディタでプロジェクトを開きます。
2. メニューから `Edit` > `Project Settings` を選択します。
3. 左側のリストから `Player` を選択します。
4. `Other Settings` セクションを探し、`Scripting Backend` を `Mono` に設定します。
5. `Api Compatibility Level` を `NET Standard 2.0` や `NET Standard 2.1` に設定します。

## 6. UnityプロジェクトをVSCodeで開く

Unityエディタで `Assets` フォルダ内の任意のC#スクリプトをダブルクリックすると、VSCodeが開きます。これにより、UnityプロジェクトがVSCodeで開かれ、C#スクリプトの編集が可能になります。

## 追加の設定とツール

### 1. Unity拡張機能のインストール

VSCodeには、Unity開発をサポートするための拡張機能がいくつかあります。これらをインストールすることで、開発体験が向上します。

- [Unity for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=visualstudiotoolsforunity.vstuc)
- Unity Code Snippets

### 2. VSCode設定ファイルの調整

VSCodeの設定ファイル（`settings.json`）を調整することで、開発環境をカスタマイズできます。

1. **ファイルの監視設定**:
   - Unityが生成する大量のファイルに対してVSCodeが過剰に反応しないように設定します。

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

Unityプロジェクトのデバッグを行うための設定を行います。

1. **launch.jsonの設定**:
   - デバッグ設定を行うために、VSCodeのデバッグ設定ファイル（`launch.json`）を作成します。
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

### 5. Git統合

バージョン管理システムとしてGitを使用している場合、VSCodeのGit統合機能を活用します。

1. **GitLens**:
   - Gitの履歴や変更を視覚的に確認できる拡張機能です。
   - インストール方法: 拡張機能マーケットプレイスで「GitLens」を検索し、インストールします。

### 6. タスクランナーの設定

ビルドやテストの自動化を行うために、タスクランナーを設定します。

1. **tasks.jsonの設定**:
   - Unityのビルドやテストを自動化するためのタスクを設定します。

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
