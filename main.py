#!/usr/bin/env python3
"""
批量给视频添加素材或水印
使用 FFmpeg subprocess 调用 (高速)
"""

import os
import sys
import tkinter as tk
import subprocess
import json
import re
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

# PyInstaller 打包支持
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')


class VideoWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频批量加水印工具")
        self.root.geometry("600x500")
        
        self.config_file = Path.home() / '.video_watermark_config.json'
        
        self.video_folder = tk.StringVar()
        self.watermark_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.watermark_position = tk.StringVar(value="右下角")
        self.watermark_size = tk.DoubleVar(value=20)
        self.watermark_opacity = tk.DoubleVar(value=80)
        self.video_bitrate = tk.IntVar(value=32)
        self.output_scale = tk.IntVar(value=100)
        self.output_fps = tk.IntVar(value=0)
        self.is_processing = False
        
        self.load_config()
        self.setup_ui()
    
    def setup_ui(self):
        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="视频批量加水印", style='Title.TLabel').pack(pady=(0, 15))
        
        file_frame = ttk.LabelFrame(main_frame, text="文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="视频:").grid(row=0, column=0, sticky='w', padx=5, pady=3)
        ttk.Entry(file_frame, textvariable=self.video_folder, width=40).grid(row=0, column=1, padx=5, pady=3)
        ttk.Button(file_frame, text="选择", command=self.select_video_folder, width=8).grid(row=0, column=2, padx=5, pady=3)
        
        ttk.Label(file_frame, text="Logo:").grid(row=1, column=0, sticky='w', padx=5, pady=3)
        ttk.Entry(file_frame, textvariable=self.watermark_path, width=40).grid(row=1, column=1, padx=5, pady=3)
        ttk.Button(file_frame, text="选择", command=self.select_watermark, width=8).grid(row=1, column=2, padx=5, pady=3)
        
        ttk.Label(file_frame, text="输出:").grid(row=2, column=0, sticky='w', padx=5, pady=3)
        ttk.Entry(file_frame, textvariable=self.output_folder, width=40).grid(row=2, column=1, padx=5, pady=3)
        ttk.Button(file_frame, text="选择", command=self.select_output_folder, width=8).grid(row=2, column=2, padx=5, pady=3)
        
        set_frame = ttk.LabelFrame(main_frame, text="设置", padding="10")
        set_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(set_frame, text="位置:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        positions = ["右下角", "左上角", "右上角", "左下角", "居中"]
        self.position_combo = ttk.Combobox(set_frame, textvariable=self.watermark_position, 
                                           values=positions, state="readonly", width=12)
        self.position_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Label(set_frame, text="大小:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        tk.Scale(set_frame, from_=5, to=50, orient=tk.HORIZONTAL,
                 variable=self.watermark_size, length=100, showvalue=True).grid(row=0, column=3, sticky='w', padx=5, pady=5)
        ttk.Label(set_frame, text="%").grid(row=0, column=4, sticky='w', padx=2, pady=5)
        
        ttk.Label(set_frame, text="CRF:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        tk.Scale(set_frame, from_=23, to=40, orient=tk.HORIZONTAL,
                 variable=self.video_bitrate, length=100, showvalue=True,
                 command=lambda v: self.quality_label.config(text=f"{self.video_bitrate.get()}")).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.quality_label = ttk.Label(set_frame, text="32")
        self.quality_label.grid(row=1, column=2, sticky='w', padx=2, pady=5)
        
        ttk.Label(set_frame, text="帧率:").grid(row=1, column=2, sticky='w', padx=15, pady=5)
        tk.Scale(set_frame, from_=0, to=30, orient=tk.HORIZONTAL,
                 variable=self.output_fps, length=80, showvalue=True,
                 command=lambda v: self.fps_label.config(
                     text=f"{self.output_fps.get() if self.output_fps.get() > 0 else '原'}")).grid(row=1, column=3, sticky='w', padx=5, pady=5)
        self.fps_label = ttk.Label(set_frame, text="原")
        self.fps_label.grid(row=1, column=4, sticky='w', padx=2, pady=5)
        
        ttk.Label(set_frame, text="分辨率:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        tk.Scale(set_frame, from_=50, to=100, orient=tk.HORIZONTAL,
                 variable=self.output_scale, length=100, showvalue=True,
                 command=lambda v: self.scale_label.config(text=f"{self.output_scale.get()}%")).grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.scale_label = ttk.Label(set_frame, text="100%")
        self.scale_label.grid(row=2, column=2, sticky='w', padx=2, pady=5)
        
        prog_frame = ttk.LabelFrame(main_frame, text="进度", padding="10")
        prog_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.progress_label = ttk.Label(prog_frame, text="等待开始...")
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(prog_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(prog_frame, height=6, width=50, state=tk.DISABLED, relief=tk.FLAT)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(5, 0))
        self.start_button = ttk.Button(btn_frame, text="开始处理", command=self.start_processing, width=15)
        self.start_button.pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="退出", command=self.root.quit, width=10).pack(side=tk.LEFT, padx=10)
    
    def load_config(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    cfg = json.load(f)
                self.video_folder.set(cfg.get('video_folder', ''))
                self.watermark_path.set(cfg.get('watermark_path', ''))
                self.output_folder.set(cfg.get('output_folder', ''))
                self.watermark_position.set(cfg.get('watermark_position', '右下角'))
                self.watermark_size.set(cfg.get('watermark_size', 20))
                self.watermark_opacity.set(cfg.get('watermark_opacity', 80))
                self.video_bitrate.set(cfg.get('video_bitrate', 32))
                self.output_scale.set(cfg.get('output_scale', 100))
                self.output_fps.set(cfg.get('output_fps', 0))
        except Exception:
            pass
    
    def save_config(self):
        try:
            cfg = {
                'video_folder': self.video_folder.get(),
                'watermark_path': self.watermark_path.get(),
                'output_folder': self.output_folder.get(),
                'watermark_position': self.watermark_position.get(),
                'watermark_size': self.watermark_size.get(),
                'watermark_opacity': self.watermark_opacity.get(),
                'video_bitrate': self.video_bitrate.get(),
                'output_scale': self.output_scale.get(),
                'output_fps': self.output_fps.get(),
            }
            with open(self.config_file, 'w') as f:
                json.dump(cfg, f)
        except Exception:
            pass
    
    def select_video_folder(self):
        """选择视频文件夹"""
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if folder:
            self.video_folder.set(folder)
    
    def select_watermark(self):
        """选择水印文件"""
        file_path = filedialog.askopenfilename(
            title="选择水印/素材文件",
            filetypes=[
                ("图片/视频文件", "*.png *.jpg *.jpeg *.gif *.mp4 *.avi *.mov"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.watermark_path.set(file_path)
    
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def log_status(self, message):
        """更新状态文本"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def get_watermark_position(self, video_width, video_height, watermark_width, watermark_height):
        """计算水印位置"""
        margin = 20  # 边距
        pos = self.watermark_position.get()
        
        if pos == "左上角":
            return (margin, margin)
        elif pos == "右上角":
            return (video_width - watermark_width - margin, margin)
        elif pos == "左下角":
            return (margin, video_height - watermark_height - margin)
        elif pos == "右下角":
            return (video_width - watermark_width - margin, video_height - watermark_height - margin)
        elif pos == "居中":
            return ((video_width - watermark_width) // 2, (video_height - watermark_height) // 2)
        else:
            return (video_width - watermark_width - margin, video_height - watermark_height - margin)
    
    def get_video_info(self, video_path):
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            info = {}
            info['width'] = re.search(r'"width"\s*:\s*(\d+)', result.stdout)
            if info['width']:
                info['width'] = int(info['width'].group(1))
            info['height'] = re.search(r'"height"\s*:\s*(\d+)', result.stdout)
            if info['height']:
                info['height'] = int(info['height'].group(1))
            bitrate = re.search(r'"bit_rate"\s*:\s*"(\d+)"', result.stdout)
            if bitrate:
                info['bitrate'] = int(bitrate.group(1))
            codec = re.search(r'"codec_name"\s*:\s*"(\w+)"', result.stdout)
            if codec:
                info['codec'] = codec.group(1)
            return info
        except Exception:
            return {}

    def build_ffmpeg_command(self, video_path, watermark_path, output_path, video_info):
        vw = video_info.get('width')
        vh = video_info.get('height')
        crf = self.video_bitrate.get()
        fps = self.output_fps.get()
        
        wm_size = self.watermark_size.get() / 100.0
        target_w = int(vw * wm_size) if vw else 100
        pos = self.get_ffmpeg_position(target_w, vw, vh)
        
        scale_pct = self.output_scale.get() / 100.0
        
        cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error']
        cmd.extend(['-i', video_path])
        cmd.extend(['-i', watermark_path])
        
        if scale_pct < 1.0 and vw and vh:
            new_w = int(vw * scale_pct / 2) * 2
            new_h = int(vh * scale_pct / 2) * 2
            if fps > 0:
                filter_str = f'[0:v][1:v]overlay={pos}[tmp];[tmp]scale={new_w}:{new_h},fps={fps}[out]'
            else:
                filter_str = f'[0:v][1:v]overlay={pos}[tmp];[tmp]scale={new_w}:{new_h}[out]'
        else:
            if fps > 0:
                filter_str = f'[0:v][1:v]overlay={pos},fps={fps}[out]'
            else:
                filter_str = f'[0:v][1:v]overlay={pos}[out]'
        
        cmd.extend(['-filter_complex', filter_str])
        cmd.extend(['-map', '[out]', '-map', '0:a?'])
        
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', str(crf),
            '-c:a', 'copy', '-movflags', '+faststart', output_path
        ])
        
        return cmd

    def get_ffmpeg_position(self, watermark_width, video_width, video_height):
        margin = 20
        pos = self.watermark_position.get()
        
        if not watermark_width:
            watermark_width = 100
        
        if video_width and video_height:
            if pos == "左上角":
                return f"{margin}:{margin}"
            elif pos == "右上角":
                return f"{video_width - watermark_width - margin}:{margin}"
            elif pos == "左下角":
                return f"{margin}:{video_height - margin}"
            elif pos == "右下角":
                return f"{video_width - watermark_width - margin}:{video_height - margin}"
            elif pos == "居中":
                return f"(W-w)/2:(H-h)/2"
        
        if video_width:
            return f"W-w-{margin}:H-h-{margin}"
        return f"W-w-{margin}:H-h-{margin}"

    def process_video(self, video_path, watermark_path, output_path):
        import time
        start_time = time.time()
        
        try:
            video_info = self.get_video_info(video_path)
            cmd = self.build_ffmpeg_command(video_path, watermark_path, output_path, video_info)
            
            self.log_status(f"CMD: ffmpeg ...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode != 0:
                err = result.stderr.strip() if result.stderr else '无错误信息'
                self.log_status(f"FFmpeg 错误: {err}")
                self.log_status(f"CMD: {' '.join(cmd)}")
                return False, elapsed
            
            return True, elapsed
        except subprocess.TimeoutExpired:
            self.log_status("处理超时 (10分钟)")
            return False, time.time() - start_time
        except Exception as e:
            self.log_status(f"处理失败: {e}")
            return False, time.time() - start_time
    
    def process_videos(self):
        """批量处理视频"""
        video_folder = self.video_folder.get()
        watermark_path = self.watermark_path.get()
        output_folder = self.output_folder.get()
        
        if not video_folder or not watermark_path or not output_folder:
            messagebox.showwarning("警告", "请填写所有路径")
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL)
            return
        
        # 获取视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        for f in os.listdir(video_folder):
            if Path(f).suffix.lower() in video_extensions:
                video_files.append(f)
        
        if not video_files:
            messagebox.showwarning("警告", "所选文件夹中没有视频文件")
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL)
            return
        
        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)
        
        # 设置进度条
        self.progress_bar['maximum'] = len(video_files)
        self.progress_bar['value'] = 0
        
        import time
        total_start = time.time()
        success_count = 0
        total_times = []
        
        for i, video_file in enumerate(video_files):
            self.progress_label.config(text=f"正在处理: {video_file} ({i+1}/{len(video_files)})")
            self.log_status(f"开始处理: {video_file}")
            
            video_path = os.path.join(video_folder, video_file)
            output_path = os.path.join(output_folder, f"output_{video_file}")
            
            success, elapsed = self.process_video(video_path, watermark_path, output_path)
            total_times.append(elapsed)
            
            if success:
                success_count += 1
                self.log_status(f"完成: {video_file} ({elapsed:.1f}秒)")
            else:
                self.log_status(f"失败: {video_file}")
            
            self.progress_bar['value'] = i + 1
            self.root.update_idletasks()
        
        total_elapsed = time.time() - total_start
        
        self.progress_label.config(text=f"处理完成! 成功: {success_count}/{len(video_files)}")
        self.log_status(f"\n处理完成! 成功: {success_count}/{len(video_files)}")
        self.log_status(f"总耗时: {total_elapsed:.1f}秒 (平均 {total_elapsed/len(video_files):.1f}秒/个)")
        messagebox.showinfo("完成", f"处理完成!\n成功: {success_count}/{len(video_files)}\n总耗时: {total_elapsed:.1f}秒")
        
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
    
    def start_processing(self):
        if self.is_processing:
            return
        
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        
        self.save_config()
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self.process_videos)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = VideoWatermarkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
