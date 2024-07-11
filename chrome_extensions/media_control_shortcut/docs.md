# Chrome のメディアコントロールから、再生中の動画・音声を再生・停止する拡張機能

## 拡張機能の作成

`manifest.json` と `background.js` を作成する。

## 拡張機能のインストール方法

1. Chromeの拡張機能管理ページ（chrome://extensions/）にアクセスする。
2. 右上の「デベロッパーモード」をオンにする。
3. 「パッケージ化されていない拡張機能を読み込む」をクリックし、`manifest.json` と `background.js` が含まれるフォルダを選択する。

これで、`Ctrl+Shift+P` のショートカットキーを押すことで、Chrome内のすべてのタブで再生中のメディアを一時停止・再生できるようになる。

## デバッグ

1. 拡張機能管理ページで、拡張機能の「Service Worker」を開く。
2. コンソールにエラーメッセージが表示されていないか確認する。
3. ショートカットキーを押して、コンソールにログが出力されるか確認する。

### Cannot access contents of url に対処

下記のようなエラーが出るときは `manifest.json` にその URL を追加する。

```txt
Uncaught (in promise) Error: Cannot access contents of url "https://...". Extension manifest must request permission to access this host.
```
