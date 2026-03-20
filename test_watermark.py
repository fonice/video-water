#!/usr/bin/env python3
"""测试视频水印处理"""

import subprocess
import time
import os

def get_video_duration(path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def get_video_size(path):
    return os.path.getsize(path) / 1024 / 1024

def test_watermark():
    video_path = '/Users/lin/Downloads/video-test/发现更多精彩视频 - 抖音搜索.mp4'
    logo_path = '/Users/lin/Downloads/video-test/logo.1c8fc73f.png'
    output_path = '/Users/lin/Downloads/video-out/test.mp4'
    
    if not os.path.exists(video_path):
        print(f"视频不存在: {video_path}")
        return
    
    original_size = get_video_size(video_path)
    original_duration = get_video_duration(video_path)
    print(f"原视频: {original_size:.1f} MB, {original_duration:.1f}秒")
    
    cmd = [
        'ffmpeg', '-y', '-hide_banner',
        '-i', video_path,
        '-i', logo_path,
        '-filter_complex', '[0:v][1:v]overlay=W-w-20:20[out]',
        '-map', '[out]',
        '-map', '0:a?',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        output_path
    ]
    
    print(f"\n执行命令: ffmpeg -i input -i logo -filter_complex overlay ... -preset ultrafast -crf 23 output")
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"失败: {result.stderr}")
        return
    
    output_size = get_video_size(output_path)
    print(f"\n结果:")
    print(f"  处理时间: {elapsed:.1f}秒")
    print(f"  输出大小: {output_size:.1f} MB")
    print(f"  速度比: {original_duration/elapsed:.1f}x")
    print(f"  体积比: {output_size/original_size*100:.0f}%")

if __name__ == '__main__':
    test_watermark()
