#!/usr/bin/env python3
"""指尖花开 - 本地静态服务器（仅本机访问；支持 HTTP Range，视频才能拖动进度）"""
import http.server, socketserver, os, re

PORT = 8123
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.mjs':  'text/javascript',
        '.wasm': 'application/wasm',
        '.task': 'application/octet-stream',
        '.mp4':  'video/mp4',
    }

    def send_head(self):
        """带 Range 支持的静态文件响应（GET/HEAD）。"""
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()          # 目录走默认逻辑
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, 'File not found')
            return None
        try:
            fs = os.fstat(f.fileno())
            size = fs.st_size
            rng = self.headers.get('Range')
            m = re.match(r'bytes=(\d*)-(\d*)$', rng.strip()) if rng else None

            if m and self.command == 'GET':
                start = int(m.group(1)) if m.group(1) else None
                end = int(m.group(2)) if m.group(2) else None
                if start is None:                # bytes=-N 后缀形式
                    n = end if end is not None else 0
                    start, end = max(0, size - n), size - 1
                elif end is None:                # bytes=N- 开放形式
                    end = size - 1
                end = min(end, size - 1)
                if start > end or start >= size:
                    f.close()
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.end_headers()
                    return None
                f.seek(start)
                length = end - start + 1
                self.send_response(206)
                self.send_header('Content-Type', self.guess_type(path))
                self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Content-Length', str(length))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        break
                    remaining -= len(chunk)
                f.close()
                return None                       # 主体已发送

            # 普通完整响应
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(path))
            self.send_header('Content-Length', str(size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except Exception:
            try:
                f.close()
            except Exception:
                pass
            raise

    def end_headers(self):
        # 仅允许本机页面来源，保持私有
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:8123')
        super().end_headers()

    def log_message(self, fmt, *args):
        pass                                      # 安静运行


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == '__main__':
    os.chdir(ROOT)
    with Server(('127.0.0.1', PORT), Handler) as httpd:
        httpd.serve_forever()
