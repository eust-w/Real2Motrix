"""Compose a narrated launch explainer from the real, locally recorded UI.

Requires macOS say, FFmpeg/FFprobe and Pillow. No private capture footage or
third-party music is used. Pass a CJK font file with --font on other setups.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SCENES = [
    ("3D 模型进仿真，还差哪一步？", "VISUAL / COLLISION / STRUCTURE",
     "把三维模型带进机器人仿真，不只是能看。还需要碰撞几何、场景结构，以及可检查的输出。", "motion"),
    ("Real2Motrix", "本地采集与资产处理工作台 / ALPHA",
     "这是 Real2Motrix，一个开源的本地采集与资产处理工作台。目前处于 Alpha 阶段。", "desktop"),
    ("真实处理，不伪装成扫描", "原创几何测试资产 / 非实拍重建",
     "你现在看到的是原创几何测试资产，不是实拍重建。它通过真实后端处理，在桌面端交互预览。", "motion"),
    ("不止一个模型文件", "MJCF / URDF / MESH / METADATA",
     "视觉网格与碰撞网格分别管理，输出 MJCF、URDF 和元数据。导出包还会进行结构校验。", "package"),
    ("手机采集：实验能力", "轨迹覆盖率 ≠ 表面完整度",
     "项目提供手机原生采集和在线上传代码。但真机效果还需要验收，轨迹覆盖率也不等于扫描完整度。", "boundary"),
    ("把下一步，变成可验收的结果", "RECONSTRUCTION / COVERAGE / SIMULATION",
     "接下来重点是表面覆盖反馈、物体和场景分流，以及真实数据集上的重建与仿真验证。", "roadmap"),
    ("从可复现，走向可信赖", "github.com/eust-w/Real2Motrix",
     "代码已经开放。如果你在做机器人仿真、三维重建或移动采集，欢迎运行示例，用真实测试一起改进。", "motion"),
]


def run(command):
    subprocess.run([str(value) for value in command], check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)
    ], text=True).strip())


def wrap(draw, text, font, width):
    lines, line = [], ""
    for char in text:
        if line and draw.textlength(line + char, font=font) > width:
            lines.append(line)
            line = ""
        line += char
    if line:
        lines.append(line)
    return lines


def timestamp(seconds):
    millis = round(seconds * 1000)
    return f"{millis // 3600000:02}:{millis // 60000 % 60:02}:{millis // 1000 % 60:02},{millis % 1000:03}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/launch"))
    parser.add_argument("--font", type=Path, default=Path("/System/Library/Fonts/Hiragino Sans GB.ttc"))
    parser.add_argument("--voice", default="Tingting")
    parser.add_argument("--orbit", type=Path, help="Optional already-trimmed fullscreen orbit recording")
    args = parser.parse_args()
    out = args.output.resolve()
    build = out / "render"
    build.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((out / "evidence.json").read_text())
    if not evidence["validation"]["valid"]:
        raise RuntimeError("Do not render a successful-demo claim without validation evidence")
    audio_durations = []
    subtitles = []
    elapsed = 0
    for index, (_, _, narration, _) in enumerate(SCENES):
        voice = build / f"voice-{index}.aiff"
        run(["say", "-v", args.voice, "-r", "205", "-o", voice, narration])
        spoken = duration(voice)
        audio_durations.append(spoken + 0.65)
        chunks = [part for part in re.split(r"[。！？]", narration) if part]
        weights = [len(part) for part in chunks]
        cursor = 0
        for part, weight in zip(chunks, weights):
            end = cursor + spoken * weight / sum(weights)
            subtitles.append((elapsed + cursor, elapsed + end, part))
            cursor = end
        elapsed += spoken + 0.65
    (out / "Real2Motrix.zh-CN.srt").write_text("\n\n".join(
        f"{i + 1}\n{timestamp(start)} --> {timestamp(end)}\n{text}"
        for i, (start, end, text) in enumerate(subtitles)
    ) + "\n", encoding="utf-8")

    # The raw capture includes setup. Only the fullscreen orbit is distributed.
    motion = args.orbit.resolve() if args.orbit else build / "orbit.mp4"
    if not args.orbit:
        run(["ffmpeg", "-y", "-v", "error", "-ss", "8", "-i", out / "desktop-recording.webm",
             "-t", "10", "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", motion])
    font = lambda size: ImageFont.truetype(str(args.font), size)
    bg, fg, muted, teal, amber = "#171b1c", "#f4f6f5", "#acb8b7", "#53d5bc", "#ffce71"
    for orientation, (width, height) in {"landscape": (1920, 1080), "portrait": (1080, 1920)}.items():
        vertical = orientation == "portrait"
        margin = 64
        media = (64, 490, 952, 720) if vertical else (64, 275, 1792, 640)
        chapter_start = 0
        clips = []
        for index, (title, subhead, narration, kind) in enumerate(SCENES):
            seconds = audio_durations[index]
            plate = Image.new("RGB", (width, height), bg)
            draw = ImageDraw.Draw(plate)
            draw.text((margin, 50), "REAL2MOTRIX   /   OPEN-SOURCE ALPHA", font=font(25), fill=teal)
            title_lines = wrap(draw, title, font(64 if vertical else 62), width - margin * 2)
            y = 130
            for line in title_lines:
                draw.text((margin, y), line, font=font(64 if vertical else 62), fill=fg)
                y += 90
            draw.text((margin, y + 15), subhead, font=font(27), fill=muted)
            mx, my, mw, mh = media
            if kind in {"motion", "desktop"}:
                screenshot = Image.open(out / ("desktop.png" if kind == "desktop" else "scene.png"))
                if kind == "motion":
                    screenshot = screenshot.crop((330, 260, 1590, 1000))
                screenshot = ImageOps.contain(screenshot, (mw, mh))
                plate.paste(screenshot, (mx + (mw - screenshot.width) // 2, my + (mh - screenshot.height) // 2))
            else:
                if kind == "package":
                    lines = [("01", "scene.xml / scene.urdf"), ("02", "视觉网格 + 碰撞网格"),
                             ("03", "物体清单 + 重建元数据"), ("04", "结构校验：通过")]
                elif kind == "boundary":
                    lines = [("有源码", "iOS / ARKit 原生采集"), ("有接口", "帧与网格的在线上传"),
                             ("待验收", "真机采集与补扫效果"), ("需区分", "轨迹覆盖 ≠ 表面覆盖")]
                else:
                    lines = [("01", "真实采集基准与失败案例"), ("02", "场景 / 物体分别处理"),
                             ("03", "表面覆盖与不确定性反馈"), ("04", "目标仿真器内的物理验证")]
                for row, (label, value) in enumerate(lines):
                    row_y = my + 35 + row * 145
                    draw.line((mx, row_y - 15, mx + mw, row_y - 15), fill="#3b4546", width=2)
                    draw.text((mx, row_y), label, font=font(27), fill=teal)
                    draw.text((mx if vertical else mx + 170, row_y + 49 if vertical else row_y), value,
                              font=font(38 if vertical else 46), fill=fg)
            draw = ImageDraw.Draw(plate)
            label_y = 1265 if vertical else 934
            draw.text((margin, label_y), "原创几何测试资产 · 非实拍重建", font=font(26), fill=amber)
            if vertical:
                draw.text((margin, 1340), "本地处理 / 可检查输出 / 实验性手机采集", font=font(25), fill=muted)
            draw.text((margin, height - 38), f"{index + 1:02} / 07    真实软件录屏 + 合成配音", font=font(19), fill=muted)
            image_path = build / f"{orientation}-{index}.png"
            plate.save(image_path)
            if index == 0:
                plate.save(out / f"cover-{orientation}.png")
            inputs = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", image_path]
            filters = []
            current = "0:v"
            next_input = 1
            if kind == "motion":
                inputs.extend(["-stream_loop", "-1", "-i", motion])
                filters.append(f"[1:v]crop=1260:740:330:260,scale={mw}:{mh}:force_original_aspect_ratio=decrease,pad={mw}:{mh}:(ow-iw)/2:(oh-ih)/2:color=0x171b1c[screen]")
                filters.append(f"[0:v][screen]overlay={mx}:{my}[media]")
                current = "media"
                next_input += 1
            for caption_index, (start, end, text) in enumerate(subtitles):
                if start < chapter_start - 0.01 or start >= chapter_start + seconds:
                    continue
                subtitle = Image.new("RGBA", (width, 180), (0, 0, 0, 0))
                painter = ImageDraw.Draw(subtitle)
                lines = wrap(painter, text, font(40 if vertical else 38), width - 128)
                for line_index, line in enumerate(lines):
                    x = (width - painter.textlength(line, font=font(40 if vertical else 38))) // 2
                    painter.text((x, line_index * 58), line, font=font(40 if vertical else 38), fill=fg)
                subtitle_path = build / f"caption-{orientation}-{caption_index}.png"
                subtitle.save(subtitle_path)
                inputs.extend(["-loop", "1", "-framerate", "30", "-i", subtitle_path])
                label = f"sub{caption_index}"
                filters.append(f"[{current}][{next_input}:v]overlay=0:{1510 if vertical else 986}:enable='between(t,{start-chapter_start:.3f},{end-chapter_start:.3f})'[{label}]")
                current = label
                next_input += 1
            inputs.extend(["-i", build / f"voice-{index}.aiff"])
            filters.append(f"[{current}]fade=t=in:st=0:d=0.22,fade=t=out:st={seconds-.22:.3f}:d=0.22,format=yuv420p[video]")
            clip = build / f"{orientation}-{index}.mp4"
            run(inputs + ["-filter_complex", ";".join(filters), "-map", "[video]", "-map", f"{next_input}:a",
                          "-af", "apad,loudnorm=I=-16:TP=-1.5:LRA=11", "-t", f"{seconds:.3f}",
                          "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                          "-threads", "4", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", clip])
            clips.append(clip)
            chapter_start += seconds
        concat = build / f"{orientation}.txt"
        concat.write_text("\n".join(f"file '{p}'" for p in clips) + "\n")
        target = out / f"Real2Motrix-intro-{orientation}-1080p.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", concat,
             "-c", "copy", "-movflags", "+faststart", target])
        print(f"Rendered {target.name}: {duration(target):.2f}s", flush=True)
    (out / "media-provenance.json").write_text(json.dumps({
        "source": "real application recording of original synthetic geometry",
        "not_demonstrated": ["real phone scan", "video reconstruction fidelity", "physics runtime", "3DGS"],
        "voice": f"macOS say {args.voice}; synthetic narration", "music": "none",
        "narration": [scene[2] for scene in SCENES], "package_sha256": evidence["package_sha256"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
