# /// script
# dependencies = [
#     "edge-tts>=7.0.0",
# ]
# ///
"""
TTS (Text-to-Speech) 文本朗读与播放工具
基于微软 Edge TTS 高清神经网络语音引擎，转换后直接在扬声器播放语音。

使用示例:
    uv run tts.py "你好，欢迎使用语音朗读功能"
    uv run tts.py "Hello world, how are you today?" -v en-US-AriaNeural
    uv run tts.py -f story.txt
    uv run tts.py "保存并播放" -o output.mp3
    uv run tts.py --list-voices zh
"""

import argparse
import asyncio
import ctypes
import os
import sys
import tempfile
import time
from pathlib import Path
import edge_tts


DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


def play_audio(file_path: str):
    """使用 Windows 原生 MCI 接口直接播放音频"""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"[播放错误] 找不到音频文件: {abs_path}", file=sys.stderr)
        return

    if sys.platform == "win32":
        alias = f"tts_{int(time.time() * 1000)}"
        winmm = ctypes.windll.winmm
        res_open = winmm.mciSendStringW(f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, 0)
        if res_open != 0:
            print(f"[播放警告] MCI 打开失败 (code={res_open})，尝试使用系统播放器打开...")
            os.system(f'start "" "{abs_path}"')
            return
        try:
            print("[播放中...] 按 Ctrl+C 可停止")
            winmm.mciSendStringW(f"play {alias} wait", None, 0, 0)
        finally:
            winmm.mciSendStringW(f"close {alias}", None, 0, 0)
    else:
        # 非 Windows 环境回退
        os.system(f'ffplay -nodisp -autoexit "{abs_path}" >/dev/null 2>&1 || mpv "{abs_path}"')


async def list_voices(language_filter: str | None = None):
    """列出可用声音列表"""
    voices = await edge_tts.list_voices()
    if language_filter:
        voices = [
            v
            for v in voices
            if language_filter.lower() in v["ShortName"].lower()
            or language_filter.lower() in v["Locale"].lower()
        ]

    print(f"{'Short Name':<32} {'Gender':<8} {'Locale':<12} {'Friendly Name'}")
    print("-" * 80)
    for v in voices:
        print(
            f"{v['ShortName']:<32} {v['Gender']:<8} {v['Locale']:<12} {v.get('FriendlyName', '')}"
        )


async def speak_text(
    text: str,
    voice: str = DEFAULT_VOICE,
    output_file: str | None = None,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
    play: bool = True,
):
    """将文本转换为语音并播放"""
    if not text.strip():
        print("错误: 转换文本不能为空", file=sys.stderr)
        sys.exit(1)

    # 确定保存路径
    is_temp = output_file is None
    if is_temp:
        temp_dir = tempfile.gettempdir()
        target_path = Path(temp_dir) / f"tts_speech_{int(time.time() * 1000)}.mp3"
    else:
        target_path = Path(output_file).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[TTS] 正在合成语音: \"{text[:40]}{'...' if len(text) > 40 else ''}\"")
    print(f"  - 声音: {voice} | 语速: {rate} | 音量: {volume}")

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )

    await communicate.save(str(target_path))

    if not is_temp:
        print(f"[TTS] 音频文件已保存至: {target_path}")

    if play:
        play_audio(str(target_path))

    # 若为临时文件则播放完毕后清理
    if is_temp and target_path.exists():
        try:
            target_path.unlink()
        except Exception:
            pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Edge-TTS 文本转语音直接播放工具",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("text", nargs="?", help="要朗读的文本内容")
    parser.add_argument("-o", "--output", help="可选：将音频保存到指定文件路径 (如 output.mp3)")
    parser.add_argument("-v", "--voice", default=DEFAULT_VOICE, help=f"声音名称 (默认: {DEFAULT_VOICE}，推荐: zh-CN-YunxiNeural)")
    parser.add_argument("-f", "--file", help="从文本文件读取内容并朗读")
    parser.add_argument("-r", "--rate", default="+0%", help="语速调节，如 '+20%%' 或 '-10%%' (默认: +0%%)")
    parser.add_argument("--volume", default="+0%", help="音量调节，如 '+20%%' 或 '-20%%' (默认: +0%%)")
    parser.add_argument("--pitch", default="+0Hz", help="音调调节，如 '+50Hz' 或 '-50Hz' (默认: +0Hz)")
    parser.add_argument("--no-play", action="store_true", help="仅生成文件，不播放声音")
    parser.add_argument("-l", "--list-voices", nargs="?", const="", help="列出可用声音，支持传入语言过滤，例如 -l zh")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.list_voices is not None:
        asyncio.run(list_voices(args.list_voices if args.list_voices else None))
        return

    text = args.text
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"错误: 找不到文件 {file_path}", file=sys.stderr)
            sys.exit(1)
        text = file_path.read_text(encoding="utf-8")
    elif not text:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            print("错误: 请提供要朗读的文本、指定 -f/--file 或使用 -l/--list-voices 查看声音", file=sys.stderr)
            sys.exit(1)

    asyncio.run(
        speak_text(
            text=text,
            voice=args.voice,
            output_file=args.output,
            rate=args.rate,
            volume=args.volume,
            pitch=args.pitch,
            play=not args.no_play,
        )
    )


if __name__ == "__main__":
    main()
