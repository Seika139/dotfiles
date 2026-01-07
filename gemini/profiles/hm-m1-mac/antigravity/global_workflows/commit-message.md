---
description: "ステージされている差分をコミットする"
---

## 概要

以下のルールに従ってコミットメッセージを作ります。
コミットの対象は現時点でステージングされているファイルです。
ステージされていないファイルの差分については考慮しません。
また、ステージされているファイルが1つもない場合はその旨を通知し、コミットは行いません。

## コミットメッセージのルール

**Follow the Conventional Commits format strictly for commit messages.**
**Write commit message in Japanese.**

Use the structure below:

```plain
<type>[optional scope]: <gitmoji> <description>

[optional body]
```

Guidelines:

1. **Type and Scope**: Choose an appropriate type (e.g., `feat`, `fix`) and optional scope to describe the affected module or feature.

2. **Gitmoji**: Include a relevant `gitmoji` that best represents the nature of the change.

3. **Description**: Write a concise, informative description in the header; use backticks if referencing code or specific terms.

4. **Body**: For additional details, use a well-structured body section:
   - Use bullet points (`*`) for clarity.
   - Clearly describe the motivation, context, or technical details behind the change, if applicable.

Commit messages should be clear, informative, and professional, aiding readability and project tracking.
