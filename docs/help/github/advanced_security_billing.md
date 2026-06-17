# GitHub Advanced Security の課金境界

このメモでは、enterprise を GitHub.com 上の GitHub Enterprise Cloud organization 配下のリポジトリとして扱う。GHE.com と GitHub Enterprise Server は、機能境界や契約条件が少し異なるため別扱いにする。

## 有料 SKU

GitHub Advanced Security の有料 SKU (Stock Keeping Unit) は、次の 2 つとして整理する。

※ GitHub が提供する SKU の詳細は [GitHub製品名とSKU番号](https://docs.github.com/ja/billing/reference/product-and-sku-names) を参照。

| SKU                      | 主な中身                                                                   | 課金単位         |
| ------------------------ | -------------------------------------------------------------------------- | ---------------- |
| GitHub Secret Protection | secret scanning、push protection、custom patterns、validity checks など    | active committer |
| GitHub Code Security     | code scanning、CodeQL、dependency review、premium Dependabot features など | active committer |

active committer は、その機能が有効なリポジトリに、過去 90 日以内に push された commit の committer。リポジトリ数ではなく、organization / enterprise 全体で unique に数える。

支払い方式は metered billing または volume / subscription。

## repo 種別ごとの扱い

| repo 種別                                        | Secret Protection                                                            | Code Security / CodeQL code scanning                                                                  | Dependabot                                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| GitHub.com public repo                           | 無料で secret scanning 利用可                                                | 無料で code scanning / dependency review 利用可                                                       | Dependabot alerts / updates は全プラン系                                                               |
| GitHub.com org private/internal, Team/Enterprise | 有効化すると Secret Protection SKU で active committer 課金                  | 有効化すると Code Security SKU で active committer 課金                                               | 基本 Dependabot は全プラン系。ただし custom auto-triage rules や dependency review は Code Security 側 |
| GitHub.com 個人 public repo                      | public repo なので無料枠                                                     | public repo なので無料枠                                                                              | 利用可                                                                                                 |
| GitHub.com 個人 private repo, Free/Pro           | 通常の Secret Protection paid SKU は使えない / 購入対象外として扱う          | code scanning / CodeQL は public repo のみ。private で使うには Team/Enterprise + Code Security が必要 | Dependabot alerts / updates は利用可                                                                   |
| GHE.com / GitHub Enterprise Server               | public / private に関係なく Advanced Security 機能はライセンス対象として扱う | 同左                                                                                                  | 基本機能と有料機能の境界は環境 / 契約に依存                                                            |

## public repo の無料枠

GitHub.com の public repository では、一部の Advanced Security 機能を無料で使える。

代表例:

- code scanning
- secret scanning
- dependency review

public repository を private に変更し、Advanced Security を支払っていない場合、そのリポジトリの Advanced Security 機能は無効化される。

## private/internal repo の考え方

GitHub.com の organization private / internal repository で Secret Protection または Code Security を有効化すると、対応する SKU の active committer 課金対象になる。

混同しやすい点:

- Dependabot alerts / security updates / version updates は全プラン系として扱う。
- Dependency review は Code Security 側として扱う。
- Dependabot の custom auto-triage rules は Code Security 側の premium Dependabot features として扱う。
- CodeQL は SKU 名ではない。code scanning として使うと Code Security 側、Code Quality として使うと Code Quality 側。

## 今回の確認結果との対応

今回の対象リポジトリでは、Code Security が `disabled` なので、CodeQL code scanning alerts や SARIF upload は `Code Security must be enabled` で 403 になる。

一方で、Code Quality の dynamic CodeQL quality scan は別系統のため、Code Security が無効でも成功している。

Secret Protection は push protection、AI detection、non-provider patterns、validity checks が有効。委任系の delegated bypass / delegated alert dismissal は無効。

Dependabot は alerts / security updates / version updates を分けて確認する。Dependency review は Dependabot alerts とは別で、現状 workflow / ruleset / branch protection に設定がない。

## 参考

- [GitHub Advanced Security license billing](https://docs.github.com/en/billing/concepts/product-billing/github-advanced-security)
- [GitHub security features](https://docs.github.com/en/code-security/getting-started/github-security-features)
- [Secret scanning availability](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning)
- [Private repository enablement](https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement)
- [GitHub Code Quality](https://docs.github.com/en/code-security/concepts/about-code-quality)
