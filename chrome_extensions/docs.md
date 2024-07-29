# Chrome のメディアコントロールから、再生中の動画・音声を再生・停止する拡張機能

## 拡張機能の作成

`manifest.json` と `background.js` を作成する。

## 拡張機能のインストール方法

1. Chrome の拡張機能管理ページ（chrome://extensions/）にアクセスする。
2. 右上の「デベロッパーモード」をオンにする。
3. 「パッケージ化されていない拡張機能を読み込む」をクリックし、`manifest.json` と `background.js` が含まれるフォルダを選択する。

## デバッグ

1. 拡張機能管理ページで、拡張機能の「Service Worker」を開く。
2. コンソールにエラーメッセージが表示されていないか確認する。
3. ショートカットキーを押して、コンソールにログが出力されるか確認する。

## 作成した拡張機能一覧

### Media Control Shortcut

`Ctrl+Shift+P` のショートカットキーを押すことで、Chrome 内のすべてのタブで再生中のメディアを一時停止・再生できるようになる。
Chrome の [キーボードショートカット設定](chrome://extensions/shortcuts) で「Chrome のみ」ではなく「グローバル」にすると、Chrome 以外のアプリを操作しているときでも実行できる。

#### Cannot access contents of url に対処

下記のようなエラーが出るときは `manifest.json` にその URL を追加する。

```txt
Uncaught (in promise) Error: Cannot access contents of url "https://...". Extension manifest must request permission to access this host.
```

### URL Incrementer

`Ctrl + Shift + ↑/↓` で URL 文字列を後ろから順にスラッシュ区切りで走査したときに、数字のみまたは `数字.拡張子` になっている箇所をインクリメント / デクリメントさせる。
