#!/usr/bin/env python3
"""Generate a clean three-chapter audiobook proof with Qwen3-TTS.

The script deliberately keeps ambience out of the main render so voice naturalness,
prosody and speaker separation can be judged without effects hiding defects.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 24000

SEGMENTS = [
    {"id": 1, "role": "announcer", "speaker": "serena", "pause": 0.8, "text": "人工智能演播样片。作品，《辐射废土：我囤满物资建了世外桃源》。第一卷，绝境反杀，初立根基。"},
    {"id": 2, "role": "narrator", "speaker": "serena", "pause": 0.9, "text": "第一章，冷库之外的死局。"},
    {"id": 3, "role": "narrator", "speaker": "serena", "pause": 0.45, "text": "冷，不是温度。冷是一把没有刃口的刀，从指尖开始，一寸寸割断血液、知觉，和活下去的念头。"},
    {"id": 4, "role": "narrator", "speaker": "serena", "pause": 0.38, "text": "白娜最后一次睁开眼时，隔着冷库门上结霜的小窗，看见男友许川站在外面。他身旁挽着一个穿白色羽绒服的女人，是她亲手提拔起来的仓储主管，林薇。"},
    {"id": 5, "role": "linwei", "speaker": "vivian", "pause": 0.45, "text": "仓库、公司，还有你囤的那些货，以后都是我们的。"},
    {"id": 6, "role": "narrator", "speaker": "serena", "pause": 0.28, "text": "报警灯明明在闪，外面的人却拔掉了总控电源。"},
    {"id": 7, "role": "xuchuan", "speaker": "dylan", "pause": 0.62, "text": "别怪我。你活着，字就签不下来。"},
    {"id": 8, "role": "narrator", "speaker": "serena", "pause": 0.42, "text": "她防过停电，防过火灾，防过供应链断裂。她防了所有意外，唯独没防枕边人。意识沉进冰层时，耳机里的废土有声书仍在断断续续播放。"},
    {"id": 9, "role": "radio", "speaker": "uncle_fu", "pause": 0.55, "text": "大灾变后的第三年，三等避难所里，一个叫白娜的女孩，被狗剩抢走半块饼，又被周虎扔进鼠道。她没有活过这一夜。"},
    {"id": 10, "role": "narrator", "speaker": "serena", "pause": 0.42, "text": "再睁眼，扑进鼻腔的不是冷库里干净的冷气，而是污水、腐肉和铁锈混在一起的臭味。后脑的疼痛撞出警报、暗红雨和地下设施几个破碎画面。她不知道灾变从何而来，也不知道自己是否真的掉进了那部小说。"},
    {"id": 11, "role": "narrator", "speaker": "serena", "pause": 0.25, "text": "前方拐角忽然投出一个庞大的影子。背脊弓起，尾巴扫过墙面。两点猩红在黑暗里同时亮起。"},
    {"id": 12, "role": "system", "speaker": "uncle_fu", "pause": 0.28, "text": "检测到绑定者生命体征恢复。仓储映射权限待激活。是否开启？"},
    {"id": 13, "role": "narrator", "speaker": "serena", "pause": 0.85, "text": "她还没来得及弄清映射是什么，两只脸盆大的黑毛辐射鼠已经同时蹬地，污水炸开，直扑她的喉咙。"},

    {"id": 14, "role": "narrator", "speaker": "serena", "pause": 0.65, "text": "第二章，两斧换一条命。"},
    {"id": 15, "role": "baina", "speaker": "vivian", "pause": 0.22, "text": "开！"},
    {"id": 16, "role": "narrator", "speaker": "serena", "pause": 0.38, "text": "意识里，一座巨大仓库在黑暗中铺开。冷冻区、常温区、药品区和应急物资区，正是她经营的三号冷链仓。红柄消防斧出现在右侧半米空地。白娜侧身一捞，黄色门牙已经咬在木柄上。"},
    {"id": 17, "role": "system", "speaker": "uncle_fu", "pause": 0.3, "text": "当前等级，一级。内部时间静止。仅可存取非生命物。活物无法进入。"},
    {"id": 18, "role": "narrator", "speaker": "serena", "pause": 0.3, "text": "冲力把她撞上墙，后脑伤口再次裂开。第二只巨鼠从侧面跃起，利爪撕开棉衣。"},
    {"id": 19, "role": "baina", "speaker": "vivian", "pause": 0.3, "text": "长这么肥，吃的都是人吧？"},
    {"id": 20, "role": "narrator", "speaker": "serena", "pause": 0.36, "text": "她借墙面一蹬，双手抡斧。第一下劈进鼠颈，却只陷进去一半。巨鼠尖叫着甩尾，她没有松手。第二斧沿着同一道伤口落下，温热腥血喷了满脸。"},
    {"id": 21, "role": "narrator", "speaker": "serena", "pause": 0.3, "text": "背后风声骤起。白娜扑倒翻滚，抄起不锈钢托盘挡住鼠牙，又一斧切进后腿。她踩住尾根，连续三斧，砍向头颈连接处。第三斧落下，通道终于安静。"},
    {"id": 22, "role": "baina", "speaker": "vivian", "pause": 0.4, "text": "刚醒就送外卖。可惜骑手反杀，差评退单。"},
    {"id": 23, "role": "narrator", "speaker": "serena", "pause": 0.42, "text": "她握着斧头站了几秒，双臂控制不住地发抖。不是威风，是低血糖、失血和突然爆发后的脱力。两只鼠尸附近没有任何奖励。杀死怪物，也不代表必然掉出晶核。"},
    {"id": 24, "role": "narrator", "speaker": "serena", "pause": 0.3, "text": "她正要检查出口，身后忽然传来极轻的一声抽气。不是老鼠。是人。"},
    {"id": 25, "role": "thug", "speaker": "eric", "pause": 0.85, "text": "那小贱人肯定还在里面！给我搜！"},

    {"id": 26, "role": "narrator", "speaker": "serena", "pause": 0.65, "text": "第三章，墙角的活人。"},
    {"id": 27, "role": "narrator", "speaker": "serena", "pause": 0.38, "text": "破木板后缩着一个女孩。右腿以不自然的角度歪着，脸白得像纸。白娜只看得出伤很重，却没有资格凭一次急救培训判断那究竟是骨折、脱位，还是血管已经受压。"},
    {"id": 28, "role": "narrator", "speaker": "serena", "pause": 0.4, "text": "脚步声越来越近，至少三个人。她有空间和武器，独自离开，活下来的概率远高于拖一个伤员。可她刚被许川当成一项清除后收益更高的成本，锁死在冷库里。若醒来第一件事，就是把另一个人也算成累赘，她和门外那两个人，还剩多少区别？"},
    {"id": 29, "role": "sumengyu", "speaker": "serena", "pause": 0.34, "text": "你走吧。别管我。右边接检修夹层，你一个人，来得及。"},
    {"id": 30, "role": "baina", "speaker": "vivian", "pause": 0.25, "text": "他们为什么抓你？"},
    {"id": 31, "role": "sumengyu", "speaker": "serena", "pause": 0.2, "text": "因为我跑了。"},
    {"id": 32, "role": "baina", "speaker": "vivian", "pause": 0.2, "text": "从哪儿？"},
    {"id": 33, "role": "sumengyu", "speaker": "serena", "pause": 0.35, "text": "周虎的避难所。"},
    {"id": 34, "role": "thug", "speaker": "eric", "pause": 0.32, "text": "虎哥说了，活要见人，死要见尸！"},
    {"id": 35, "role": "narrator", "speaker": "serena", "pause": 0.38, "text": "白娜收起斧头，俯身抓住女孩腋下，把人半拖半抱到倒塌的金属柜后。柜子与墙之间只有半米，勉强藏得下两个人。"},
    {"id": 36, "role": "sumengyu", "speaker": "serena", "pause": 0.36, "text": "他们要的是你。你把我推出去吧。我腿断了，本来就走不了。你就能从另一边跑。"},
    {"id": 37, "role": "narrator", "speaker": "serena", "pause": 0.25, "text": "她明明怕得牙齿都在打颤，却还是把身体往柜外挪了一点。白娜抬手，毫不客气地把她按了回去。"},
    {"id": 38, "role": "baina", "speaker": "vivian", "pause": 0.55, "text": "谁说我要拿你换路？我这辈子最烦两种人。一种，替别人决定谁该死。一种，替自己决定自己只配去死。"},
    {"id": 39, "role": "narrator", "speaker": "serena", "pause": 0.28, "text": "防尘布外，手电光骤然停住。男人粗重的呼吸，就在金属柜另一侧。"},
    {"id": 40, "role": "thug", "speaker": "eric", "pause": 1.0, "text": "这后头……是不是有东西？"},
    {"id": 41, "role": "announcer", "speaker": "serena", "pause": 0.3, "text": "前三章神经语音演播样片，完。"},
]

ROLE_FILTERS = {
    "narrator": "highpass=f=70,lowpass=f=11500",
    "announcer": "highpass=f=80,lowpass=f=11000",
    "baina": "highpass=f=85,lowpass=f=11800",
    "linwei": "highpass=f=105,lowpass=f=11200",
    "xuchuan": "highpass=f=65,lowpass=f=10500",
    "sumengyu": "highpass=f=105,lowpass=f=11800,volume=0.94",
    "thug": "highpass=f=55,lowpass=f=9000,volume=1.03",
    "radio": "highpass=f=320,lowpass=f=3900,acompressor=threshold=-20dB:ratio=3:attack=8:release=80,volume=0.92",
    "system": "highpass=f=220,lowpass=f=5200,acompressor=threshold=-18dB:ratio=4:attack=5:release=70,volume=0.90",
}


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def make_silence(path: Path, seconds: float) -> None:
    frames = max(1, int(SAMPLE_RATE * seconds))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"\x00\x00" * frames)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out / "raw"
    mastered_dir = args.out / "mastered"
    raw_dir.mkdir(exist_ok=True)
    mastered_dir.mkdir(exist_ok=True)

    concat_entries: list[Path] = []
    manifest = []

    for item in SEGMENTS:
        idx = item["id"]
        role = item["role"]
        raw = raw_dir / f"{idx:03d}_{role}.wav"
        mastered = mastered_dir / f"{idx:03d}_{role}.wav"
        seed = 20260727 + idx * 97
        cmd = [
            str(args.engine),
            "-d", str(args.model),
            "-s", item["speaker"],
            "-l", "Chinese",
            "--text", item["text"],
            "--seed", str(seed),
            "--temperature", "0.55",
            "--top-k", "35",
            "--rep-penalty", "1.08",
            "--max-duration", "35",
            "--int8",
            "-j", "2",
            "-o", str(raw),
        ]
        run(cmd)

        filt = ROLE_FILTERS.get(role, "highpass=f=70,lowpass=f=11500")
        # Segment-level normalization keeps speaker changes controlled while preserving dynamics.
        af = f"{filt},loudnorm=I=-21:TP=-2:LRA=9"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-ar", str(SAMPLE_RATE), "-ac", "1", "-af", af, str(mastered)])
        concat_entries.append(mastered)

        silence = mastered_dir / f"{idx:03d}_pause.wav"
        make_silence(silence, float(item["pause"]))
        concat_entries.append(silence)
        manifest.append({**item, "seed": seed, "raw": str(raw.relative_to(args.out)), "mastered": str(mastered.relative_to(args.out))})

    concat_file = args.out / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p.as_posix()}'" for p in concat_entries) + "\n", encoding="utf-8")

    joined = args.out / "qwen3_tts_three_chapters_clean.wav"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "pcm_s16le", str(joined)])

    final_wav = args.out / "《辐射废土》前三章_Qwen3-TTS神经语音样片.wav"
    final_mp3 = args.out / "《辐射废土》前三章_Qwen3-TTS神经语音样片.mp3"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(joined), "-af", "loudnorm=I=-18:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", str(final_wav)])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(final_wav), "-codec:a", "libmp3lame", "-b:a", "192k", str(final_mp3)])

    (args.out / "segments.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out / "README.txt").write_text(
        "模型：Qwen3-TTS-12Hz-0.6B-CustomVoice（神经TTS）\n"
        "用途：判断中文自然度、角色区分、停顿和演播节奏。\n"
        "本版本不铺环境音，避免音效掩盖声线问题。\n"
        "角色：Serena=旁白/苏梦雨，Vivian=白娜/林薇，Dylan=许川，Eric=追兵，Uncle_Fu=广播/系统。\n",
        encoding="utf-8",
    )
    print(final_mp3)
    return 0


if __name__ == "__main__":
    sys.exit(main())
