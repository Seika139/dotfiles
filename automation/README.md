# automation

## use poetry

```bash
cd [path_to_automation]
poetry shell # 仮想環境を起動する
python [file] # 仮想環境内で python を実行
exit # 仮想環境を終了する
poetry run python [file] # 仮想環境に入らずに python を実行
```

## 自動クリック

```bash
python -m automation.auto_click # 仮想環境の内
poetry run python -m automation.auto_click # 仮想環境の外
```
