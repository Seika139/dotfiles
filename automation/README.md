# automation

## use poetry

```bash
cd [path_to_automation]
poetry --version

# poetry が v2.0.0 以上の場合
poetry env activate # 仮想環境を起動する
python [file] # 仮想環境内で python を実行
poetry env deactivate # 仮想環境を終了する

# poetry が v2.0.0 未満の場合
poetry shell # 仮想環境を起動する
python [file] # 仮想環境内で python を実行
exit # 仮想環境を終了する

# 仮想環境に入らずに python を実行する場合
poetry run python [file]
```

## 自動クリック

```bash
python -m automation.auto_click # 仮想環境の内
poetry run python -m automation.auto_click # 仮想環境の外
```
