# Unity, C# の変数定義について

**目次**

- [Unity, C# の変数定義について](#unity-c-の変数定義について)
  - [フィールドとプロパティ](#フィールドとプロパティ)
    - [フィールド](#フィールド)
    - [プロパティ](#プロパティ)
    - [自動実装プロパティ](#自動実装プロパティ)
      - [読み取り専用にする](#読み取り専用にする)
      - [C# 9.0 の`init`アクセサ](#c-90-のinitアクセサ)
      - [デフォルト値の設定](#デフォルト値の設定)
      - [プライベートセッター](#プライベートセッター)
  - [プロパティやフィールドを一度設定した値から変更できなくする方法](#プロパティやフィールドを一度設定した値から変更できなくする方法)
    - [1. `readonly` フィールド](#1-readonly-フィールド)
    - [2. プロパティのゲッターのみを公開する](#2-プロパティのゲッターのみを公開する)
    - [3. イミュータブルオブジェクト](#3-イミュータブルオブジェクト)
    - [4. `init` アクセサ（C# 9.0 以降）](#4-init-アクセサc-90-以降)
    - [5. カスタムロジックを使ったプロパティ](#5-カスタムロジックを使ったプロパティ)
  - [Unity でクラスがインスタンス化されるタイミング](#unity-でクラスがインスタンス化されるタイミング)
    - [1. スクリプトの`Start`メソッド内でインスタンス化](#1-スクリプトのstartメソッド内でインスタンス化)
    - [2. スクリプトの`Awake`メソッド内でインスタンス化](#2-スクリプトのawakeメソッド内でインスタンス化)
    - [3. 任意のメソッド内でインスタンス化](#3-任意のメソッド内でインスタンス化)
    - [4. シリアライズされたフィールドとしてインスタンス化](#4-シリアライズされたフィールドとしてインスタンス化)
    - [5. スクリプトのコンストラクタ内でインスタンス化](#5-スクリプトのコンストラクタ内でインスタンス化)

## フィールドとプロパティ

### フィールド

フィールドはクラスや構造体のデータを保持するための変数です。
直接アクセスできますが、カプセル化の観点から直接アクセスは推奨されないことが多いです。

```csharp
public class Person
{
    public string name;  // フィールド
    public int _age;  // このようにアンダースコアをプレフィックスとして付けることもある。
}
```

フィールドは一般的に camelCase またはアンダースコア付き camelCase で書きます。

### プロパティ

プロパティはフィールドにアクセスするためのメソッドのようなもの。
ゲッター（getter）とセッター（setter）を使って、フィールドの値を取得したり設定したりできます。
プロパティを使うことで、データの検証やカプセル化を行うことができます。

```csharp
public class Person
{
    private string name;  // プライベートフィールド

    public string Name    // プロパティ
    {
        get { return name; }
        set { name = value; }
    }
}
```

プロパティは PascalCase で書くことが一般的です。

### 自動実装プロパティ

C#では、自動実装プロパティを使うことで、フィールドとプロパティを簡潔に定義できます。

```csharp
public class Person
{
    public string Name { get; set; }  // 自動実装プロパティ
}
```

#### 読み取り専用にする

C# 6.0 以降では、読み取り専用の自動実装プロパティを定義できます。
これは、プロパティの初期化時またはコンストラクタ内でのみ値を設定できます。

```csharp
public class Person
{
    public string Name { get; }

    public Person(string name)
    {
        Name = name;
    }
}
```

#### C# 9.0 の`init`アクセサ

C# 9.0 以降では、`init`アクセサを使用すると、オブジェクトの初期化時にのみプロパティの値を設定可能になります。

```csharp
public class Person
{
    public string Name { get; init; }
}

// 使用例
var person = new Person { Name = "John" };
// person.Name = "Doe"; // これはコンパイルエラー
```

#### デフォルト値の設定

自動実装プロパティにはデフォルト値を設定できます。

```csharp
public class Person
{
    public string Name { get; set; } = "Unknown";
}
```

#### プライベートセッター

プロパティのセッターをプライベートにすることで、外部から値を変更できないようにします。

```csharp
public class Person
{
    public string Name { get; private set; }

    public Person(string name)
    {
        Name = name;
    }
}
```

## プロパティやフィールドを一度設定した値から変更できなくする方法

### 1. `readonly` フィールド

`readonly`キーワードを使用すると、フィールドは初期化時またはコンストラクタ内でのみ設定可能となり、それ以降は変更できなくなります。

```csharp
public class Person
{
    public readonly string Name;

    public Person(string name)
    {
        Name = name;
    }
}
```

### 2. プロパティのゲッターのみを公開する

プロパティのセッターをプライベートにすることで、外部から値を変更できなくします。

```csharp
public class Person
{
    private string name;
    public string Name
    {
        get { return name; }
        private set { name = value; } // ココ
    }

    public Person(string name)
    {
        Name = name;
    }
}
```

### 3. イミュータブルオブジェクト

クラス全体を不変（イミュータブル）にする設計。これにより、オブジェクトの状態が一度設定されたら変更されないことを保証します。

```csharp
public class Person
{
    public string Name { get; }

    public Person(string name)
    {
        Name = name;
    }
}
```

### 4. `init` アクセサ（C# 9.0 以降）

C# 9.0 以降では、`init`アクセサを使用してプロパティを初期化時にのみ設定可能にできます。

```csharp
public class Person
{
    public string Name { get; init; }
}

// 使用例
var person = new Person { Name = "John" };
// person.Name = "Doe"; // これはコンパイルエラー
```

### 5. カスタムロジックを使ったプロパティ

カスタムロジックを使って、一度設定された値を変更できないようにすることも可能です。

```csharp
public class Person
{
    private string name;
    public string Name
    {
        get { return name; }
        set
        {
            if (name == null)
            {
                name = value;
            }
            else
            {
                throw new InvalidOperationException("Name can only be set once.");
            }
        }
    }
}
```

## Unity でクラスがインスタンス化されるタイミング

### 1. スクリプトの`Start`メソッド内でインスタンス化

`Start`メソッドは、MonoBehaviour を継承したクラスにおいて、オブジェクトが有効化された最初のフレームで一度だけ呼び出されます。このメソッド内でインスタンスを生成することが一般的です。

```csharp
using UnityEngine;

public class PersonManager : MonoBehaviour
{
    void Start()
    {
        Person person = new Person("John");
        Debug.Log(person.Name);
    }
}
```

### 2. スクリプトの`Awake`メソッド内でインスタンス化

`Awake`メソッドは、オブジェクトが初めてロードされたときに呼び出されます。`Start`よりも早いタイミングで呼び出されるため、他のスクリプトの初期化よりも前に実行したい処理がある場合に使用します。

```csharp
using UnityEngine;

public class PersonManager : MonoBehaviour
{
    void Awake()
    {
        Person person = new Person("John");
        Debug.Log(person.Name);
    }
}
```

### 3. 任意のメソッド内でインスタンス化

特定のイベントや条件に応じてインスタンスを生成したい場合、任意のメソッド内でインスタンス化できます。

```csharp
using UnityEngine;

public class PersonManager : MonoBehaviour
{
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            Person person = new Person("John");
            Debug.Log(person.Name);
        }
    }
}
```

### 4. シリアライズされたフィールドとしてインスタンス化

Unity のインスペクターで設定した値を使ってインスタンスを生成する場合、スクリプトのフィールドとして定義し、シリアライズできます。

```csharp
using UnityEngine;

public class PersonManager : MonoBehaviour
{
    [SerializeField] private string personName;

    private Person person;

    void Start()
    {
        person = new Person(personName);
        Debug.Log(person.Name);
    }
}
```

### 5. スクリプトのコンストラクタ内でインスタンス化

Unity では、MonoBehaviour を継承したクラスのコンストラクタは通常使用しませんが、非 MonoBehaviour クラスであればコンストラクタ内でインスタンスを生成することも可能です。

```csharp
public class GameManager
{
    private Person person;

    public GameManager()
    {
        person = new Person("John");
        Debug.Log(person.Name);
    }
}
```
