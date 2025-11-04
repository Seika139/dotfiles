from pathlib import Path

from gtts import gTTS


def main() -> None:
    # 音声にしたいテキスト
    text_to_speak = "Goal for Japan! Tanaka breaks free and shoots! It's in the net!」"
    text_to_speak_ja = (
        "ゴール！日本代表、田中選手が抜け出してシュート！ネットを揺らしました！"
    )

    # 出力ファイル名
    output_path = Path(__file__).parent / "output" / "commentary_gtts.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # gTTSオブジェクトの作成 (lang='ja'で日本語を指定)
    tts = gTTS(text=text_to_speak, lang="en")

    # 音声をファイルに保存
    tts.save(str(output_path))

    output_path_ja = Path(__file__).parent / "output" / "commentary_gtts_ja.mp3"
    tts = gTTS(text=text_to_speak_ja, lang="ja")
    tts.save(str(output_path_ja))

    print(f"音声を保存しました: {output_path.resolve()} & {output_path_ja.resolve()}")


if __name__ == "__main__":
    main()
