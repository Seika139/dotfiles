# Ad Nuisance Remover

邪魔な広告を手動で隠し、広告表示に伴うスクロールなどの操作制限を解除する Manifest V3 拡張です。全画面オーバーレイだけでなく、画面端に固定表示される対応済みの広告も対象にします。

## アイコン

赤い停止標識と斜線で広告表示を抑え、開いたターコイズ色の南京錠で操作制限の解除を表現しています。`icons/` には Chrome 用の 16、32、48、128 px PNG と、再生成用の高解像度原本を含めています。

## インストール

1. Chrome で `chrome://extensions/` を開き、「デベロッパーモード」を有効にします。
2. 「パッケージ化されていない拡張機能を読み込む」を選び、この `ad_nuisance_remover` フォルダを指定します。
3. 対象ページで拡張機能のアイコンをクリックします。

以前の `ad_overlay_unlock` フォルダを読み込んでいた場合は、先に `chrome://extensions/` で旧拡張機能の「削除」を選びます。その後、改めて「パッケージ化されていない拡張機能を読み込む」から `chrome_extensions/ad_nuisance_remover` を選択してください。

## 権限

この拡張機能は `activeTab` と `scripting` のみを要求し、`host_permissions` は要求しません。アイコンを押したときだけ、その時点で表示しているタブへ一時的にアクセスして処理を実行します。

## 動作

アイコンクリック時だけ、現在の最上位ページを調べます。画面の大部分を覆い、実際に画面上の点を遮っている固定・絶対・sticky 要素を候補にし、属性、URL、または表示文に広告・スポンサー・プロモーション・インタースティシャル・paywall などの根拠がある場合だけ非表示にします。Google Funding Choices の広告視聴ゲート（`fc-message-root` 内の `fc-monetization-dialog-container`／`fc-dialog-overlay` と `.fc-rewarded-ad-button` の組み合わせ）と、全画面サイズの Google AdSense vignette／rewarded 広告（`adsbygoogle-noablate` の `data-vignette-loaded`／`data-slotcar-rewarded`）は、固有の DOM 印と画面占有条件の両方を満たす場合に限り、広告ダイアログとして処理します。さらに、`ins.adsbygoogle.adsbygoogle-noablate` が `data-anchor-status="displayed"` と `data-anchor-shown="true"` を持ち、画面上端または下端に固定され、高い `z-index` で表示されている Google AdSense アンカー広告も非表示にします。このアンカー広告だけを隠した場合は、スクロールロックの根拠ではないため `html` と `body` のスタイルを変更しません。全画面候補を隠したときだけ、`html` と `body` の明確な `overflow`、`touch-action`、固定位置によるロックを限定的に解除します。固定位置の負の `top` は現在のスクロール位置へ補正します。操作後は最大 8 秒間だけ、追加・属性変更による広告の再挿入を監視します。

同じページでアイコンをもう一度クリックすると、拡張機能が変更した各 inline style プロパティだけを元に戻します。拡張機能が設定した値と異なる変更は復元時に保持しますが、ページやユーザーが同じプロパティを同じ値へ変更した競合は区別できず、元の値へ戻る場合があります。復元時にスクロール位置を開始位置へ戻すことはありません。ページを再読み込みした場合も、ページ側の元の状態に戻ります。

## 除外と限界

ログイン・認証・決済・パスワード・cookie 同意に関わる語やフォームを含む要素、通常の `dialog`、ARIA モーダルは候補から除外します。Google Funding Choices でも、全画面の `.fc-monetization-dialog-container` または `.fc-dialog-overlay` の配下に広告視聴用 `.fc-rewarded-ad-button` があり、候補とその Funding Choices 祖先・子孫に上記の保護根拠やフォームがない場合だけ、この通常ダイアログ保護の例外です。そのため広告でも解除されない場合があります。逆にサイト独自の表示が広告用語を含み、条件に一致した場合は誤判定の可能性があります。Chrome の内部ページ、Chrome ウェブストア、一部の保護されたページでは拡張機能を実行できません。
